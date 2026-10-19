# Estruturas de Dados para Processamento de Linguagem Natural

### Skip-gram e busca semântica sobre discursos parlamentares brasileiros

> Defesa arquitetural — Trabalho final da disciplina **Estruturas para Ciência de
> Dados** (graduação em Data Science e Machine Learning, CEUB).
> Autores: **Erick Cardoso Mendes,** RA 22509170; **Lanna Correa Soares**, RA: 22505387

---

## Sumário

1. [Introdução e contexto](#1-introdução-e-contexto)
2. [Definição do problema](#2-definição-do-problema)
3. [Visão geral do pipeline](#3-visão-geral-do-pipeline)
4. [As quatro estruturas de dados](#4-as-quatro-estruturas-de-dados)
5. [Validação empírica](#5-validação-empírica)
6. [Resultados qualitativos](#6-resultados-qualitativos)
7. [Limitações e trabalhos futuros](#7-limitações-e-trabalhos-futuros)
8. [Reprodutibilidade](#8-reprodutibilidade)
9. [Referências](#9-referências)

---

## 1. Introdução e contexto

Este projeto implementa, **do zero** — sem PyTorch, TensorFlow, JAX, Gensim ou
qualquer biblioteca de embeddings ou de diferenciação automática pronta —, um
pipeline completo de **embeddings distribucionais** (Word2Vec/Skip-gram com
*hierarchical softmax*) e de **busca semântica aproximada** sobre um corpus de
discursos da Câmara dos Deputados.

A disciplina exige o uso integrado e justificado de pelo menos quatro estruturas
de dados clássicas. O princípio que orienta todo o trabalho é que **cada
estrutura deve ser introduzida porque a matemática do problema a exige, não
porque a tarefa a permite**. A escolha do Word2Vec não é acidental: cada um de
seus componentes faz emergir uma estrutura de dados como consequência direta de
uma necessidade de complexidade ou de uma propriedade matemática — e, em mais de
um caso, com amarração explícita à teoria da informação.

A única dependência numérica transversal é o **NumPy**, usado como ferramenta de
álgebra linear (matrizes de embeddings, gradientes, produtos internos). Ele *não*
conta como uma das quatro estruturas protagonistas.

---

## 2. Definição do problema

**O que o sistema faz.** Treina representações vetoriais densas (embeddings) de
palavras a partir de discursos parlamentares e, com elas, realiza busca semântica
sobre o corpus. Ao final, o usuário pode (i) submeter uma palavra e receber as
mais próximas no espaço aprendido, e (ii) submeter uma consulta textual livre e
receber os discursos mais semanticamente similares.

**O corpus.** Coletado da [API de Dados Abertos da Câmara dos
Deputados](https://dadosabertos.camara.leg.br/), 57ª legislatura, período de
**06/02/2024 a 10/06/2026**. Após filtros de qualidade (exclusão de tipos
procedimentais como *Pela Ordem*; mínimo de 100 caracteres) e **amostragem
estratificada por deputado** (*largest remainder method* com piso de 1 discurso
por parlamentar), o corpus final tem:

| Métrica                   | Valor                                              |
| -------------------------- | -------------------------------------------------- |
| Discursos                  | 7.997 (8.000 amostrados − 3 duplicatas técnicas) |
| Deputados                  | 559                                                |
| Partidos / UFs             | 22 / 27                                            |
| Tokens (whitespace)        | ≈ 4,0 milhões                                    |
| Mediana de tokens/discurso | 427                                                |

A estratificação é metodologicamente importante: uma amostragem aleatória simples
favoreceria os ~10–20 deputados mais verbosos (que acumulam ~30% do volume),
enviesando os embeddings por idiossincrasias léxicas individuais. No corpus final,
o top-10 de deputados responde por apenas ~18% dos discursos.

**Aviso metodológico.** Embora o domínio seja político, o trabalho é
deliberadamente **técnico**. O sistema faz **recuperação/ranqueamento**, nunca
geração ou interpretação de conteúdo: o modelo devolve documentos e similaridades;
qualquer resumo exibido é metadado oficial da própria API. Observações se limitam
ao plano estrutural ("no espaço aprendido, os termos X e Y ocupam regiões
próximas"), sem atribuir posições a partidos ou parlamentares.

---

## 3. Visão geral do pipeline

```
 API Câmara ──(coleta_corpus.py, Etapa 1)──▶ corpus .parquet (7.997 discursos)
                                                     │
                                                     ▼
            Etapa 2 ┌──────────────────────────────────────────────┐
                    │  DICIONÁRIO (hash table)                       │
                    │  token→id, freq, prob_keep (subsampling)       │
                    └──────────────────────────────────────────────┘
                                                     │ frequências
                                                     ▼
            Etapa 3 ┌──────────────────────────────────────────────┐
                    │  HEAP ──▶ ÁRVORE DE HUFFMAN                    │
                    │  hierarchical softmax (código de prefixo ótimo)│
                    └──────────────────────────────────────────────┘
                                                     │
            Etapas 4–6 ┌───────────────────────────────────────────┐
                       │  PILHA (fita do mini-autograd)             │
                       │  forward empilha ops; backward desempilha  │
                       │  ──▶ treino Skip-gram (SGD) ──▶ W_in        │
                       └───────────────────────────────────────────┘
                                                     │ embeddings (W_in)
                                                     ▼
            Etapas 7–8  documentos = média dos embeddings dos tokens
                                                     │
            Etapa 8 ┌──────────────────────────────────────────────┐
                    │  GRAFO (HNSW)                                  │
                    │  índice navegável de vizinhos aproximados      │
                    └──────────────────────────────────────────────┘
                                                     │
            Etapa 9       buscar(query, k)  ──▶  MIN-HEAP de tamanho K  ──▶ top-K
```

Cada etapa é uma unidade coesa com entradas, saídas e *sanity checks* visíveis no
`notebook.ipynb`. As estruturas aparecem na ordem em que a construção do método
as exige.

---

## 4. As quatro estruturas de dados

### 4.1 Dicionário (hash table) — vocabulário

**Dado armazenado.** Mapeamento bidirecional `token → id` (`dict`) e `id → token`
(lista densa de inteiros contíguos), frequências absolutas, probabilidades de
*subsampling* (`prob_keep`) e a distribuição de unigrama elevada a 0,75 para o
*negative sampling* futuro. O vocabulário final tem **V = 23.485 tokens**
(`min_count = 5`), cobrindo **98,4%** de todas as ocorrências.

**Justificativa de complexidade.** Durante o treino, a cada token de cada janela
de contexto consultam-se ID, frequência e probabilidade de descarte. Com
V ≈ 23 mil e N ≈ 4 milhões de tokens, uma busca linear em lista — O(V) por
consulta — tornaria o treino inviável (O(N·V) só de *lookups*). A hash table dá
acesso médio **O(1)**, reduzindo o custo total de *lookup* a O(N). A construção do
vocabulário é O(N), feita uma única vez. Aqui a escolha não é de conveniência: é a
única estrutura que sustenta a complexidade-alvo.

**Ruído controlado.** O *subsampling* de Mikolov (2013b) — manter o token *w* com
probabilidade `P_keep(w) = √(t/f(w))`, t = 10⁻⁵ — é uma forma deliberada de
injeção de ruído: descarta agressivamente *stopwords* (no corpus, `de` é mantido
em ~1,5% das ocorrências) e expande a janela efetiva de contexto.

### 4.2 Heap → Árvore de Huffman — hierarchical softmax

**Dado armazenado.** (a) Na construção, uma **min-heap** (`heapq`) das
(sub)árvores ordenadas por frequência acumulada; (b) o resultado é uma **árvore
binária** com **23.484 nós internos** (= V − 1), cada um carregando um vetor de
parâmetros θₙ ∈ ℝ¹⁰⁰ — os parâmetros do *hierarchical softmax*; cada palavra é uma
folha, com um `code` (bits da raiz à folha) e um `path` (nós internos
atravessados).

**Justificativa de complexidade.** O softmax pleno custa O(V) por avaliação — com
N atualizações, O(N·V), proibitivo. O *hierarchical softmax* substitui a
normalização global por uma sequência de decisões binárias ao longo do caminho da
palavra na árvore, custando O(|code(w)|) por par. A construção via heap é
O(V log V), feita uma vez.

**Conexão com a teoria da informação (o ponto central da defesa).** A topologia da
árvore é livre, e o custo esperado por atualização é o comprimento médio de
caminho ponderado pela frequência, L = Σ p(w)·|code(w)|. Minimizar L é exatamente
o problema que a **árvore de Huffman (1952)** resolve de forma ótima: ela é o
código de prefixo de menor comprimento esperado para uma distribuição de
probabilidades. O **teorema de codificação de fonte de Shannon (1948)** garante o
limite

```
H(W) ≤ L < H(W) + 1,   com   H(W) = −Σ p(w) log₂ p(w).
```

Ou seja, **a mesma estrutura que minimiza os bits para codificar a fonte minimiza
o trabalho computacional do softmax**. O custo esperado do HS fica da ordem de
H(W) — tipicamente bem abaixo de log₂V. A Seção 5 confirma essa desigualdade
empiricamente.

### 4.3 Pilha — grafo computacional do *autograd*

**Dado armazenado.** Uma fita (*tape*) que registra, na ordem de execução do
*forward pass*, as funções de *backward* de cada operação — cada uma capturando
referências aos tensores operandos e ao resultado. O mini-autograd suporta apenas
o necessário para o Skip-gram com HS: `embed`, `add`, `mul`, `dot`, `sigmoid`,
`log`.

**Justificativa de complexidade.** A *backpropagation* aplica a regra da cadeia em
**ordem reversa** à execução do *forward*: a última operação é a primeira a ser
diferenciada, e seu gradiente alimenta as anteriores. Uma pilha (*Last-In,
First-Out*) modela exatamente essa inversão temporal — empilhar na ida,
desempilhar na volta. *Push* e *pop* são O(1); o *backward* percorre a pilha uma
única vez, em **O(n)** no número de operações. LIFO aqui não é uma escolha entre
alternativas: é a estrutura matemática do problema. Frameworks reais (PyTorch,
TensorFlow, JAX) implementam o mesmo princípio com *tape* ou grafo dinâmico.

### 4.4 Grafo — HNSW para busca aproximada

**Dado armazenado.** Um grafo navegável de pequeno mundo hierárquico
(*Hierarchical Navigable Small World*, Malkov & Yashunin, 2016) em camadas. Cada
nó é um documento (representado pela média normalizada dos embeddings dos seus
tokens); cada aresta liga documentos próximos no espaço vetorial. As camadas
superiores são esparsas (arestas de longo alcance); a camada 0 contém todos os
nós com arestas curtas. Parâmetros: M = 16, efConstruction = 200.

**Justificativa de complexidade.** A busca exata de vizinhos custa O(N·D) por
consulta. KD-trees são O(log N) apenas em baixa dimensão e **degradam para
varredura quase completa acima de D ≈ 20** (maldição da dimensionalidade) — com
D = 100, seriam ineficazes. O HNSW navega o grafo de forma gulosa, das camadas
esparsas às densas, com custo **O(log N) amortizado** mesmo em alta dimensão; é o
método usado em FAISS, Pinecone, Qdrant e Weaviate. A construção é O(N log N).

**Heaps na busca.** Cada busca por camada usa duas *heaps* (candidatos +
resultados), e a seleção final dos K mais similares usa uma **min-heap de tamanho
K** — O(N log K) contra O(N log N) de ordenar todos os candidatos. A árvore de
Huffman e o HNSW, portanto, fazem a heap reaparecer naturalmente em dois pontos do
pipeline.

---

## 5. Validação empírica

Cada estrutura tem ao menos um *sanity check* visível no notebook. Os mais
relevantes para a defesa:

**Lei de Zipf (dicionário).** O gráfico log-log de frequência × *rank* exibe a
reta característica de inclinação ≈ −1, confirmando que o corpus se comporta como
linguagem natural e que a contagem do vocabulário está correta.

**Optimalidade de Huffman (heap + árvore + entropia).** Sobre a distribuição
empírica do vocabulário:

| Métrica                         | Valor (bits)      |
| -------------------------------- | ----------------- |
| Entropia de Shannon, H(W)        | **10,0585** |
| Comprimento médio de Huffman, L | **10,0854** |
| Redundância, L − H             | **0,0269**  |
| Código de tamanho fixo, log₂V  | 14,5195           |

A desigualdade H(W) ≤ L < H(W)+1 é confirmada, com redundância de apenas **0,027
bit** — demonstração viva da optimalidade. Contra uma árvore balanceada
(log₂V ≈ 14,52 bits), o HS economiza ~4,4 bits por atualização. A igualdade de
Kraft, Σ 2^(−|code(w)|) = 1,000000000000, confirma que o código é de prefixo
completo. Profundidade da árvore: mínima 5, média 17,38, máxima 20.

**Corretude do autograd (pilha).** Os gradientes calculados pelo mini-autograd
foram comparados com diferenças finitas centrais em uma reprodução de uma
atualização de HS. Erro máximo: **~1,3 × 10⁻¹¹** — onze ordens de grandeza abaixo
do limite de 10⁻⁵ exigido.

**Forward do modelo.** Com W_out inicializada em zeros, σ(0) = 0,5 em cada nó, e a
perda inicial de qualquer par é exatamente |code(o)|·ln2 — valor previsto e
confirmado (6,931472 para um caminho de 10 nós). A localidade do gradiente também
foi verificada: apenas a linha da palavra-centro e os nós do caminho recebem
gradiente.

**Treino (5 épocas, ~25,5 milhões de pares).** A perda média cai de ~10,0 para
~9,0 e estabiliza, com decaimento linear da taxa de aprendizado de 0,025 a
0,0001. (No HS, a perda é a soma de −log σ ao longo do caminho de ~10–14 nós, de
modo que o valor absoluto não tende a zero; o que importa é a queda e a qualidade
semântica resultante.)

**Recall do HNSW (grafo).** Sobre 100 consultas, comparando o HNSW com a busca
exata por força bruta: **recall@10 = 0,999** (99/100 consultas com recall
perfeito). A aproximação recupera praticamente os mesmos vizinhos da busca exata,
a uma fração do custo. Construção do índice (7.997 documentos): ~18 s; grau médio
na camada 0 = 32 (= 2·M); nível máximo = 4.

---

## 6. Resultados qualitativos

Os embeddings capturaram estrutura semântica real a partir de pura coocorrência.
Exemplos de vizinhos mais próximos (similaridade do cosseno):

- **saúde** → sus, atendimento, pacientes, tratamento, cuidados, acesso
- **amazônia** → floresta, cerrado, amazônica, desmatamento, biodiversidade, pantanal
- **criança** → adolescente, eca, gestante, bullying, estatuto
- **imposto** → isenção, isentar, impostos, tributar, pagam, renda

A projeção t-SNE de um conjunto temático curado exibe **agrupamentos limpos e
separados** por tema (saúde, educação, economia, ambiente, segurança), o que
valida o pipeline de ponta a ponta.

A busca semântica por consulta livre retorna documentos relevantes. Por exemplo,
*"reforma tributária e isenção de imposto de renda"* recupera, no topo, discursos
sobre o PL 1.087/2025 (isenção do IR até R$ 5 mil); *"proteção de crianças e
adolescentes contra a violência"* recupera discursos sobre o combate ao abuso e à
exploração sexual. O ranqueamento é integralmente produto do modelo; os resumos
exibidos são metadados oficiais da API.

---

## 7. Limitações e trabalhos futuros

**Limitações.**

- O treino é SGD puro, par a par, em NumPy de thread único — fiel ao Skip-gram
  clássico, porém computacionalmente custoso (não há aceleração por GPU, por
  decisão de projeto de implementar tudo do zero).
- A representação de documentos pela média simples dos embeddings ignora ordem e
  importância relativa dos termos.
- O *recall* do HNSW, embora altíssimo, é aproximado por construção.

**Trabalhos futuros.**

- *Negative sampling* como alternativa ao *hierarchical softmax*, com comparação
  direta — conecta-se à tese de ruído controlado.
- Representação de documentos por média ponderada por TF-IDF.
- Comparação com um modelo pré-treinado de PT-BR (ex.: NILC) como oráculo de
  qualidade.
- Análise de deslocamento semântico temporal (treinar em janelas separadas).
- **Interface de busca e disponibilização (deploy).** Expor a busca em uma
  interface simples para consulta por usuários finais, retornando não só os
  discursos mais similares, mas também agregações úteis: quem discursou sobre o
  tema, com que frequência, e se o assunto é recorrente ao longo do tempo.

---

## 8. Reprodutibilidade

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python coleta_corpus.py            # Etapa 1 — gera data/discursos.parquet (~15 min)
jupyter lab notebook.ipynb         # Etapas 2–9 — vocabulário, Huffman, autograd,
                                   #              treino, inspeção, índice e busca
```

**Determinismo.** Todas as fontes de aleatoriedade usam `SEED = 42`
(amostragem, inicialização de W_in, geração de pares, construção do HNSW). O cache
HTTP em SQLite torna a coleta reexecutável a custo zero.

**Artefatos.** O treino completo está atrás do flag `EXECUTAR_TREINO_COMPLETO`
(§8.4 do notebook). Ele gera `artefatos/embeddings.npy`; as demais células
serializam `vocab.pkl`, `huffman_tree.pkl` e `indice_busca.pkl`. Os diretórios
`data/` e `artefatos/` não são versionados (são regeneráveis); `coleta_corpus.py`
é o contrato de reprodução do corpus.

---

## 9. Referências

* FIRTH, J. R. A synopsis of linguistic theory, 1930–1955. In: **Studies in linguistic analysis**. Oxford: Blackwell, 1957. p. 1–32.
* HARRIS, Z. S. Distributional structure. **Word**, [s. l.], v. 10, n. 2–3, p. 146–162, 1954. DOI: 10.1080/00437956.1954.11659520. Disponível em: https://doi.org/10.1080/00437956.1954.11659520.
* HUFFMAN, D. A. A method for the construction of minimum-redundancy codes. **Proceedings of the IRE**, [s. l.], v. 40, n. 9, p. 1098–1101, 1952. DOI: 10.1109/JRPROC.1952.273898. Disponível em: https://doi.org/10.1109/JRPROC.1952.273898.
* LEVY, O.; GOLDBERG, Y. Neural word embedding as implicit matrix factorization. In: **Advances in Neural Information Processing Systems (NeurIPS)**, 27., 2014. Anais [...]. [S. l.]: Curran Associates, 2014. p. 2177–2185. Disponível em: https://papers.nips.cc/paper/2014/hash/feab05aa91085b7a8012516bc3533958-Abstract.html.
* MALKOV, Y. A.; YASHUNIN, D. A. Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. **IEEE Transactions on Pattern Analysis and Machine Intelligence**, [s. l.], v. 42, n. 4, p. 824–836, 2020. DOI: 10.1109/TPAMI.2018.2889473. Disponível em: https://arxiv.org/abs/1603.09320.
* MIKOLOV, T.; CHEN, K.; CORRADO, G.; DEAN, J. Efficient estimation of word representations in vector space. **arXiv**, 2013a. DOI: 10.48550/arXiv.1301.3781. Disponível em: https://arxiv.org/abs/1301.3781.
* MIKOLOV, T.; SUTSKEVER, I.; CHEN, K.; CORRADO, G.; DEAN, J. Distributed representations of words and phrases and their compositionality. In: **Advances in Neural Information Processing Systems (NeurIPS)**, 26., 2013b. Anais [...]. [S. l.]: Curran Associates, 2013. p. 3111–3119. Disponível em: https://arxiv.org/abs/1310.4546.
* MORIN, F.; BENGIO, Y. Hierarchical probabilistic neural network language model. In: **International Workshop on Artificial Intelligence and Statistics (AISTATS)**, 10., 2005, Barbados. Proceedings [...]. [S. l.: s. n.], 2005. p. 246–252. Disponível em: https://proceedings.mlr.press/r5/morin05a.html.
* SHANNON, C. E. A mathematical theory of communication. **Bell System Technical Journal**, [s. l.], v. 27, n. 3, p. 379–423, 1948. DOI: 10.1002/j.1538-7305.1948.tb01338.x. Disponível em: https://doi.org/10.1002/j.1538-7305.1948.tb01338.x.
* CÂMARA DOS DEPUTADOS. **Dados Abertos da Câmara dos Deputados**. Brasília, [2024]. Disponível em: https://dadosabertos.camara.leg.br/.
