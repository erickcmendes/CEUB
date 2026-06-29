# Deploy - GastoSmart no Render

A aplicação web (Streamlit) está publicada em **https://gastosmart-3nje.onrender.com** como Web Service do Render, rodando via Docker.

## Variáveis de ambiente

No painel do Render (https://dashboard.render.com), no serviço `gastosmart-3nje`, acessar **Environment -> Environment Variables** e garantir:

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_PUB_KEY` | Chave anon/publishable do Supabase |
| `OPENWEATHER_API_KEY` | (opcional) Chave da OpenWeather para exibir clima |
| `OPENWEATHER_CIDADE` | (opcional) Cidade padrão. Default: `Brasilia` |

Os valores de referência estão no arquivo `.env.example` do repositório. **Nunca commitar esses valores no repositório.**

> Nota: `src/config.py` aceita `SUPABASE_KEY` como fallback de compatibilidade, mas o nome oficial passou a ser `SUPABASE_PUB_KEY` (decisão AD-16 em `.ai/docs/ARD.md`).

## Configuração do serviço

Em **Settings** do serviço no Render:

- **Environment:** Docker
- **Start Command:** deixe em branco. O Render lê o `CMD` do `Dockerfile`, que executa `streamlit run src/app_web.py --server.port 8501 --server.address 0.0.0.0`.
- **Port:** o Dockerfile expõe `8501` (porta padrão do Streamlit).

## Deploy automático e manual

- **Automático:** auto-deploy a cada push na branch `main` (já configurado).
- **Manual:** clicar em **Manual Deploy -> Deploy latest commit** no canto superior direito do painel.

## Validação pós-deploy

Após o deploy concluir:

1. Acessar https://gastosmart-3nje.onrender.com - a interface web deve carregar com o logo, abas e sidebar de clima.
2. Adicionar um gasto via aba **Adicionar** e confirmar que aparece na aba **Listar** e no painel do Supabase (https://supabase.com/dashboard/project/jqetggonptxjqjpapjps -> Table editor -> `gastos`).
3. Remover um gasto via aba **Remover** e confirmar a remoção no painel do Supabase.

## Link público

https://gastosmart-3nje.onrender.com
