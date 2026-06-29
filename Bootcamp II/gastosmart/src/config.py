"""
Configuração centralizada do GastoSmart.

Carrega variáveis de ambiente (com suporte a .env) e expõe o cliente Supabase
para as demais camadas do app.
"""

import os

from supabase import Client, create_client

# Carrega .env automaticamente se python-dotenv estiver disponível.
# Em produção (Render, CI), as variáveis vêm do ambiente real, então o import
# falhar silenciosamente é aceitável.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def get_supabase_client() -> Client:
    """
    Cria e retorna um cliente Supabase autenticado com as variáveis de ambiente.

    Variáveis esperadas:
        - SUPABASE_URL: URL do projeto Supabase
        - SUPABASE_PUB_KEY: chave publishable/anon do projeto

    Raises:
        RuntimeError: quando alguma variável obrigatória está ausente.
    """
    url = os.getenv("SUPABASE_URL")
    # Aceita SUPABASE_PUB_KEY (padrão atual) e cai pra SUPABASE_KEY (legado) por compatibilidade.
    key = os.getenv("SUPABASE_PUB_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_PUB_KEY precisam estar definidas. "
            "Copie .env.example para .env e preencha, ou exporte as variáveis no shell."
        )

    return create_client(url, key)
