"""
coleta_corpus.py — Coleta e amostragem estratificada de discursos parlamentares
=================================================================================

Pipeline de extração de discursos da 57ª legislatura da Câmara dos Deputados
para construção do corpus do trabalho final da disciplina de Estruturas para
Ciência de Dados.

Procedimento
------------
1. Lista todos os deputados da 57ª legislatura via API de Dados Abertos da
   Câmara dos Deputados (https://dadosabertos.camara.leg.br/api/v2/).
2. Para cada deputado, itera os discursos no período definido em DATA_INICIO–
   DATA_FIM, persistindo a coleta crua em cache SQLite local.
3. Aplica filtros de qualidade: tipo de discurso (subset com maior densidade
   léxica) e tamanho mínimo de transcrição.
4. Realiza amostragem estratificada por deputado via *largest remainder method*
   com piso de 1 discurso por parlamentar contemplado, garantindo que o corpus
   final tenha exatamente N_AMOSTRA discursos (default = 8000) com cobertura
   máxima de autores.
5. Persiste o corpus final em Parquet (formato colunar comprimido) acompanhado
   de um JSON com estatísticas descritivas para uso posterior no notebook.

Reprodutibilidade
-----------------
- Amostragem usa `random.Random(SEED)` com SEED fixa.
- Cache SQLite (.camara_cache.sqlite) permite reexecuções determinísticas.
- Versão de dependências listada em requirements.txt.

Dependências
------------
- httpx >= 0.27
- pandas >= 2.0
- pyarrow >= 14.0 (engine do Parquet)

Uso
---
    # Execução completa (8000 discursos):
    python coleta_corpus.py

    # Smoke test com 5 deputados e 100 discursos finais:
    python coleta_corpus.py --dry-run

    # Tamanho de amostra customizado:
    python coleta_corpus.py --n-amostras 4000

    # Logging em modo debug:
    python coleta_corpus.py --log-level DEBUG

Saídas
------
- data/discursos.parquet          → corpus amostrado (schema documentado abaixo)
- data/discursos_metadata.json    → estatísticas descritivas
- data/.camara_cache.sqlite       → cache HTTP persistente

Schema do parquet
-----------------
    id_discurso       : str    — identificador único (id_deputado + data + hash)
    id_deputado       : int    — id na API da Câmara
    nome_deputado     : str    — nome parlamentar
    sigla_partido     : str    — sigla partidária no momento da coleta
    sigla_uf          : str    — UF de representação
    data              : str    — data do discurso (YYYY-MM-DD)
    tipo_discurso     : str    — tipo (Pronunciamento, Discussão, etc.)
    fase_evento       : str    — fase do evento (Ordem do Dia, etc.)
    transcricao       : str    — texto integral do discurso
    sumario           : str    — sumário (pode estar vazio)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

logger = logging.getLogger("coleta_corpus")

# =============================================================================
# Configuração geral
# =============================================================================

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"
USER_AGENT = "estruturas-nlp-discursos/0.1 (academic project)"
DEFAULT_CACHE_TTL = 7 * 24 * 3600  # 7 dias — corpus histórico, baixa volatilidade
DEFAULT_RPS = 5.0                  # rate limit defensivo (API tolera mais)
DEFAULT_TIMEOUT = 30.0
MAX_PAGE_SIZE = 100                # limite do endpoint
MAX_RETRIES = 3
BACKOFF_BASE = 1.5

# Parâmetros do corpus
LEGISLATURA = 57                   # 2023–2027
DATA_INICIO = "2024-01-01"
DATA_FIM = "2026-06-30"

# Filtros de qualidade léxica:
# A API retorna tipos em CAIXA ALTA. Os tipos mais frequentes incluem:
#   PRONUNCIAMENTO, DISCURSO ENCAMINHADO, BREVES COMUNICAÇÕES, COMO LÍDER,
#   DISCUSSÃO, PELA ORDEM, QUESTÃO DE ORDEM, HOMENAGEM, PARECER, OUTROS.
#
# Usamos blacklist (mais robusta que whitelist): apenas os tipos procedimentais
# de baixíssimo conteúdo léxico são removidos. Os tipos mantidos contemplam:
#   - pronunciamentos e discursos formais (alta densidade);
#   - debates sobre proposições (DISCUSSÃO);
#   - discursos de liderança (COMO LÍDER);
#   - pareceres de comissão (vocabulário técnico-jurídico);
#   - homenagens (vocabulário ritual);
#   - breves comunicações (diversidade temática);
#   - discursos entregues por escrito (DISCURSO ENCAMINHADO).
TIPOS_DISCURSO_EXCLUIDOS = {
    "PELA ORDEM",
    "QUESTÃO DE ORDEM",
    "OUTROS",
}
MIN_CARACTERES_TRANSCRICAO = 100

# Amostragem
SEED = 42
N_AMOSTRA_PADRAO = 8000

# Caminhos padrão
DEFAULT_DATA_DIR = Path("data")


# =============================================================================
# Cache em SQLite (GET-only, com TTL)
# =============================================================================

class SQLiteCache:
    """Cache simples para respostas HTTP GET, indexado pela URL completa.

    Justificativa do design: SQLite é zero-config, atômico em escritas, e
    suporta concorrência básica. Para o volume esperado (~50k URLs distintas
    no pior caso), a performance é excelente sem overhead operacional.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS cache (
        url        TEXT PRIMARY KEY,
        fetched_at REAL NOT NULL,
        body       TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_fetched_at ON cache(fetched_at);
    """

    def __init__(self, path: str | Path, ttl: int = DEFAULT_CACHE_TTL):
        self.path = Path(path)
        self.ttl = ttl
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, url: str) -> dict | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT fetched_at, body FROM cache WHERE url = ?", (url,)
            ).fetchone()
        if not row:
            return None
        fetched_at, body = row
        if time.time() - fetched_at > self.ttl:
            return None
        return json.loads(body)

    def set(self, url: str, payload: dict) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache(url, fetched_at, body) VALUES (?, ?, ?)",
                (url, time.time(), json.dumps(payload, ensure_ascii=False)),
            )


# =============================================================================
# Rate limiter — token bucket de janela fixa
# =============================================================================

class RateLimiter:
    """Garante intervalo mínimo entre requisições para respeitar a API.

    Implementação simples: registra o último timestamp e bloqueia até que o
    intervalo mínimo (1/rps) tenha decorrido. Mais eficiente que sleeps
    cegos e suficiente para um único cliente síncrono.
    """

    def __init__(self, rps: float = DEFAULT_RPS):
        self.min_interval = 1.0 / rps
        self._last = 0.0

    def acquire(self) -> None:
        now = time.monotonic()
        wait = self._last + self.min_interval - now
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()


# =============================================================================
# Cliente da API da Câmara (versão enxuta — apenas endpoints necessários)
# =============================================================================

@dataclass
class CamaraConfig:
    cache_path: str | Path = DEFAULT_DATA_DIR / ".camara_cache.sqlite"
    cache_ttl: int = DEFAULT_CACHE_TTL
    rps: float = DEFAULT_RPS
    timeout: float = DEFAULT_TIMEOUT
    use_cache: bool = True


class CamaraAPIError(Exception):
    """Erro do cliente que indica falha permanente (não-transiente)."""


class CamaraClient:
    """Cliente para os endpoints de deputados e discursos da Câmara.

    Apenas o subconjunto necessário para este trabalho está implementado.
    """

    def __init__(self, config: CamaraConfig | None = None):
        self.config = config or CamaraConfig()
        self._cache = (
            SQLiteCache(self.config.cache_path, self.config.cache_ttl)
            if self.config.use_cache else None
        )
        self._limiter = RateLimiter(self.config.rps)
        self._http = httpx.Client(
            base_url=API_BASE,
            timeout=self.config.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
        )

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    # ------------------------------------------------------------------ HTTP

    def _get(self, path: str, params: dict | None = None) -> dict:
        """GET com cache de leitura, rate limit e retry com backoff exponencial.

        Erros transientes (429 Too Many Requests, 5xx) entram em retry.
        Erros 4xx (exceto 429) falham imediatamente, pois indicam pedido
        malformado ou recurso inexistente.
        """
        req = self._http.build_request("GET", path, params=params)
        full_url = str(req.url)

        if self._cache:
            cached = self._cache.get(full_url)
            if cached is not None:
                return cached

        last_err: Exception | None = None
        for attempt in range(MAX_RETRIES):
            self._limiter.acquire()
            try:
                resp = self._http.send(req)
                if resp.status_code == 429 or 500 <= resp.status_code < 600:
                    raise httpx.HTTPStatusError(
                        f"transient {resp.status_code}",
                        request=req, response=resp,
                    )
                if 400 <= resp.status_code < 500:
                    raise CamaraAPIError(
                        f"erro permanente {resp.status_code}: {req.url}"
                    )
                resp.raise_for_status()
                payload = resp.json()
                if self._cache:
                    self._cache.set(full_url, payload)
                return payload
            except CamaraAPIError:
                raise
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                last_err = e
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    "  request falhou (%d/%d): %s — aguardando %.1fs",
                    attempt + 1, MAX_RETRIES, e, wait,
                )
                time.sleep(wait)
                req = self._http.build_request("GET", path, params=params)

        raise CamaraAPIError(
            f"falhou após {MAX_RETRIES} tentativas: {last_err}"
        )

    def _paginate(self, path: str, params: dict | None = None) -> Iterator[dict]:
        """Itera todas as páginas de um endpoint-coleção."""
        params = dict(params or {})
        params.setdefault("itens", MAX_PAGE_SIZE)
        params.setdefault("pagina", 1)

        while True:
            payload = self._get(path, params)
            yield from payload.get("dados", [])

            next_link = next(
                (link for link in payload.get("links", []) if link.get("rel") == "next"),
                None,
            )
            if not next_link:
                return
            params["pagina"] = int(params["pagina"]) + 1

    # --------------------------------------------------------------- ENDPOINTS

    def listar_deputados(self, id_legislatura: int) -> Iterator[dict]:
        """Itera deputados de uma legislatura específica."""
        params = {
            "idLegislatura": id_legislatura,
            "ordem": "ASC",
            "ordenarPor": "nome",
        }
        yield from self._paginate("/deputados", params)

    def listar_discursos_deputado(
        self,
        id_deputado: int,
        data_inicio: str,
        data_fim: str,
    ) -> Iterator[dict]:
        """Itera os discursos de um deputado em uma janela temporal."""
        params = {
            "dataInicio": data_inicio,
            "dataFim": data_fim,
        }
        yield from self._paginate(
            f"/deputados/{id_deputado}/discursos", params
        )


# =============================================================================
# Pipeline de coleta
# =============================================================================

def coletar_discursos_brutos(
    cli: CamaraClient,
    deputados: list[dict],
    data_inicio: str,
    data_fim: str,
) -> dict[int, list[dict]]:
    """Coleta todos os discursos de cada deputado no período.

    Retorna um dicionário {id_deputado: [discurso_bruto, ...]} contendo a
    resposta crua da API (sem filtros nem normalização).
    """
    discursos_por_deputado: dict[int, list[dict]] = {}
    total_bruto = 0

    for i, dep in enumerate(deputados, 1):
        dep_id = dep["id"]
        nome = dep.get("nome", "?")
        try:
            discursos = list(
                cli.listar_discursos_deputado(dep_id, data_inicio, data_fim)
            )
        except CamaraAPIError as e:
            logger.warning("  [%d/%d] %s — falha: %s", i, len(deputados), nome, e)
            continue

        if discursos:
            discursos_por_deputado[dep_id] = discursos
            total_bruto += len(discursos)

        if i % 25 == 0 or i == len(deputados):
            logger.info(
                "  [%d/%d] deputados processados | %d discursos brutos acumulados",
                i, len(deputados), total_bruto,
            )

    logger.info(
        "Coleta bruta finalizada: %d discursos de %d deputados ativos no período.",
        total_bruto, len(discursos_por_deputado),
    )
    return discursos_por_deputado


def _id_discurso_estavel(id_deputado: int, disc: dict) -> str:
    """Gera um ID estável e único para o discurso (determinístico)."""
    base = f"{id_deputado}|{disc.get('dataHoraInicio', '')}|{disc.get('tipoDiscurso', '')}"
    h = hashlib.md5(base.encode("utf-8")).hexdigest()[:10]
    return f"{id_deputado}-{h}"


def filtrar_e_normalizar(
    discursos_por_deputado: dict[int, list[dict]],
    deputados_index: dict[int, dict],
) -> dict[int, list[dict]]:
    """Aplica filtros de qualidade e normaliza o schema.

    Filtros (blacklist):
      1. tipoDiscurso ∉ TIPOS_DISCURSO_EXCLUIDOS
      2. len(transcricao) >= MIN_CARACTERES_TRANSCRICAO

    Saída: dicionário {id_deputado: [discurso_normalizado, ...]} já no schema
    final.
    """
    from collections import Counter

    saida: dict[int, list[dict]] = {}
    descartes_por_tipo: Counter = Counter()
    aceitos_por_tipo: Counter = Counter()
    descartados_tamanho = 0

    for dep_id, lista in discursos_por_deputado.items():
        dep_info = deputados_index.get(dep_id, {})
        normalizados: list[dict] = []

        for disc in lista:
            tipo = (disc.get("tipoDiscurso", "") or "").strip().upper()
            if tipo in TIPOS_DISCURSO_EXCLUIDOS:
                descartes_por_tipo[tipo] += 1
                continue

            transcricao = (disc.get("transcricao") or "").strip()
            if len(transcricao) < MIN_CARACTERES_TRANSCRICAO:
                descartados_tamanho += 1
                continue

            data_hora = disc.get("dataHoraInicio", "") or ""
            data = data_hora[:10] if data_hora else ""

            fase = disc.get("faseEvento") or {}
            fase_titulo = fase.get("titulo", "") if isinstance(fase, dict) else ""

            normalizados.append({
                "id_discurso": _id_discurso_estavel(dep_id, disc),
                "id_deputado": dep_id,
                "nome_deputado": dep_info.get("nome", ""),
                "sigla_partido": dep_info.get("siglaPartido", ""),
                "sigla_uf": dep_info.get("siglaUf", ""),
                "data": data,
                "tipo_discurso": tipo,
                "fase_evento": fase_titulo,
                "transcricao": transcricao,
                "sumario": (disc.get("sumario") or "").strip(),
            })
            aceitos_por_tipo[tipo] += 1

        if normalizados:
            saida[dep_id] = normalizados

    total_aceitos = sum(aceitos_por_tipo.values())
    total_desc_tipo = sum(descartes_por_tipo.values())
    logger.info(
        "Filtragem: %d aceitos | %d descartados por tipo | %d descartados por tamanho",
        total_aceitos, total_desc_tipo, descartados_tamanho,
    )
    logger.info("  Distribuição dos aceitos por tipo:")
    for tipo, n in aceitos_por_tipo.most_common():
        logger.info("    %4d  %s", n, tipo)
    if descartes_por_tipo:
        logger.info("  Descartes por tipo:")
        for tipo, n in descartes_por_tipo.most_common():
            logger.info("    %4d  %s", n, tipo)
    return saida


def amostrar_estratificado(
    grupos: dict[int, list[dict]],
    n_alvo: int,
    seed: int,
) -> list[dict]:
    """Amostragem estratificada por deputado via *largest remainder method*.

    Estratégia:
      1. Cada deputado com pelo menos 1 discurso aceito recebe quota >= 1
         (piso). Isso garante diversidade autoral máxima.
      2. As quotas restantes são distribuídas proporcionalmente ao volume
         de discursos de cada deputado, com arredondamento pela técnica
         do maior resto (Hamilton/largest remainder), evitando o viés
         sistemático de arredondamento simples.
      3. Cada deputado é capado pelo número de discursos disponíveis.
      4. Dentro de cada estrato, a amostragem é uniforme sem reposição.

    Justificativa metodológica: amostragem aleatória simples sobre o pool
    total favoreceria deputados verbosos (10–20 deputados acumulam ~30%
    dos discursos do plenário). A estratificação por autor com piso 1
    aproxima a distribuição da composição efetiva do parlamento e produz
    embeddings menos enviesados por idiossincrasias léxicas individuais.
    """
    rng = random.Random(seed)
    grupos = {k: v for k, v in grupos.items() if v}

    pool_total = sum(len(v) for v in grupos.values())
    if pool_total <= n_alvo:
        logger.info(
            "Pool (%d) <= alvo (%d): retornando todos os discursos disponíveis.",
            pool_total, n_alvo,
        )
        return [d for items in grupos.values() for d in items]

    if n_alvo < len(grupos):
        raise ValueError(
            f"n_alvo ({n_alvo}) < número de deputados elegíveis ({len(grupos)}); "
            "o piso de 1 por deputado inviabiliza a amostragem."
        )

    # Quotas fracionárias proporcionais
    quotas_float: dict[int, float] = {
        k: (len(v) / pool_total) * n_alvo for k, v in grupos.items()
    }

    # Piso de 1 + parte inteira da quota fracionária
    quotas: dict[int, int] = {k: max(1, int(q)) for k, q in quotas_float.items()}

    # Cap pela disponibilidade real
    quotas = {k: min(quotas[k], len(grupos[k])) for k in grupos}

    # Ajuste para bater exatamente n_alvo
    diff = n_alvo - sum(quotas.values())

    if diff > 0:
        # Adicionar: prioriza deputados com maior resíduo fracionário
        # e que ainda têm capacidade.
        elegiveis = [
            (k, quotas_float[k] - int(quotas_float[k]))
            for k in grupos if quotas[k] < len(grupos[k])
        ]
        elegiveis.sort(key=lambda x: -x[1])
        for k, _ in elegiveis[:diff]:
            quotas[k] += 1

    elif diff < 0:
        # Remover: prioriza menores resíduos, sem violar piso.
        elegiveis = [
            (k, quotas_float[k] - int(quotas_float[k]))
            for k in grupos if quotas[k] > 1
        ]
        elegiveis.sort(key=lambda x: x[1])
        for k, _ in elegiveis[:abs(diff)]:
            quotas[k] -= 1

    # Verifica consistência final
    total_quotas = sum(quotas.values())
    if total_quotas != n_alvo:
        logger.warning(
            "Ajuste de quotas convergiu para %d em vez de %d (diferença residual).",
            total_quotas, n_alvo,
        )

    # Amostragem dentro de cada estrato
    amostra: list[dict] = []
    for k, items in grupos.items():
        amostra.extend(rng.sample(items, quotas[k]))

    logger.info(
        "Amostragem estratificada: %d discursos sorteados de %d deputados.",
        len(amostra), len(grupos),
    )
    return amostra


def gerar_metadata(amostra: list[dict]) -> dict[str, Any]:
    """Calcula estatísticas descritivas do corpus para documentação."""
    if not amostra:
        return {}

    df = pd.DataFrame(amostra)
    n_caracteres = df["transcricao"].str.len()
    n_palavras_aprox = df["transcricao"].str.split().str.len()

    return {
        "n_discursos": int(len(df)),
        "n_deputados": int(df["id_deputado"].nunique()),
        "n_partidos": int(df["sigla_partido"].nunique()),
        "n_ufs": int(df["sigla_uf"].nunique()),
        "periodo": {
            "min": df["data"].min(),
            "max": df["data"].max(),
        },
        "tamanho_transcricao": {
            "min_caracteres": int(n_caracteres.min()),
            "max_caracteres": int(n_caracteres.max()),
            "media_caracteres": float(n_caracteres.mean()),
            "mediana_caracteres": float(n_caracteres.median()),
        },
        "tamanho_aprox_em_tokens_whitespace": {
            "total": int(n_palavras_aprox.sum()),
            "media_por_discurso": float(n_palavras_aprox.mean()),
            "mediana_por_discurso": float(n_palavras_aprox.median()),
        },
        "distribuicao_por_tipo": df["tipo_discurso"].value_counts().to_dict(),
        "top10_partidos": df["sigla_partido"].value_counts().head(10).to_dict(),
        "top10_ufs": df["sigla_uf"].value_counts().head(10).to_dict(),
    }


# =============================================================================
# Persistência
# =============================================================================

def salvar_artefatos(
    amostra: list[dict],
    metadata: dict,
    parquet_path: Path,
    metadata_path: Path,
) -> None:
    """Persiste o corpus amostrado em Parquet e o metadata em JSON."""
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(amostra)
    df = df.sort_values(["data", "id_deputado"]).reset_index(drop=True)

    df.to_parquet(parquet_path, engine="pyarrow", compression="snappy", index=False)
    logger.info(
        "Parquet salvo: %s (%.1f MB, %d linhas)",
        parquet_path, parquet_path.stat().st_size / 1e6, len(df),
    )

    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info("Metadata salvo: %s", metadata_path)


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Coleta e amostra discursos parlamentares da 57ª legislatura.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa pipeline com 5 deputados e amostra de 100 (smoke test).",
    )
    parser.add_argument(
        "--n-amostras",
        type=int,
        default=N_AMOSTRA_PADRAO,
        help=f"Tamanho da amostra estratificada final (default: {N_AMOSTRA_PADRAO}).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Diretório de saída e cache (default: {DEFAULT_DATA_DIR}).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    data_dir: Path = args.data_dir
    data_dir.mkdir(parents=True, exist_ok=True)

    cache_path = data_dir / ".camara_cache.sqlite"
    if args.dry_run:
        parquet_path = data_dir / "discursos_dryrun.parquet"
        metadata_path = data_dir / "discursos_dryrun_metadata.json"
        n_alvo = 100
    else:
        parquet_path = data_dir / "discursos.parquet"
        metadata_path = data_dir / "discursos_metadata.json"
        n_alvo = args.n_amostras

    logger.info("=" * 70)
    logger.info("Coleta de discursos — 57ª legislatura")
    logger.info("Período: %s a %s", DATA_INICIO, DATA_FIM)
    logger.info("Tipos EXCLUÍDOS: %s", ", ".join(sorted(TIPOS_DISCURSO_EXCLUIDOS)))
    logger.info("Tamanho mínimo de transcrição: %d caracteres", MIN_CARACTERES_TRANSCRICAO)
    logger.info("Amostra-alvo: %d discursos", n_alvo)
    if args.dry_run:
        logger.info(">>> MODO DRY-RUN: 5 deputados, amostra de 100 <<<")
    logger.info("=" * 70)

    config = CamaraConfig(cache_path=cache_path)
    with CamaraClient(config) as cli:
        # ---------------------------------------------------------- Deputados
        logger.info("Etapa 1/4: listando deputados da legislatura %d...", LEGISLATURA)
        deputados = list(cli.listar_deputados(id_legislatura=LEGISLATURA))
        logger.info("  %d deputados encontrados.", len(deputados))

        if args.dry_run:
            deputados = deputados[:5]
            logger.info("  Restringindo a %d deputados (dry-run).", len(deputados))

        deputados_index = {d["id"]: d for d in deputados}

        # ---------------------------------------------------- Coleta de discursos
        logger.info("Etapa 2/4: coletando discursos por deputado...")
        brutos = coletar_discursos_brutos(cli, deputados, DATA_INICIO, DATA_FIM)

        if not brutos:
            logger.error("Nenhum discurso coletado. Abortando.")
            return 1

        # --------------------------------------------- Filtragem e normalização
        logger.info("Etapa 3/4: filtrando e normalizando...")
        filtrados = filtrar_e_normalizar(brutos, deputados_index)

        if not filtrados:
            logger.error("Nenhum discurso sobreviveu aos filtros. Abortando.")
            return 1

        # -------------------------------------------------- Amostragem final
        logger.info("Etapa 4/4: amostragem estratificada...")
        amostra = amostrar_estratificado(filtrados, n_alvo=n_alvo, seed=SEED)

        # ------------------------------------------------------ Persistência
        metadata = gerar_metadata(amostra)
        salvar_artefatos(amostra, metadata, parquet_path, metadata_path)

    logger.info("=" * 70)
    logger.info("Coleta concluída com sucesso.")
    logger.info("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
