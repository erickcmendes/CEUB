# Deploy — GastoSmart no Render

## Variáveis de ambiente (configuração manual)

No painel do Render (https://dashboard.render.com), no serviço do GastoSmart,
acessar: **Environment → Environment Variables** e adicionar:

| Variável | Descrição |
|---|---|
| `SUPABASE_URL` | URL do projeto Supabase |
| `SUPABASE_KEY` | Chave anon/publishable do Supabase |

Os valores de referência estão no arquivo `.env.example` do repositório.
**Nunca commitar esses valores no repositório.**

## Deploy manual

Após configurar as variáveis, clicar em **Manual Deploy** no painel do Render.

## Validação

Após o deploy, testar um insert via app e confirmar o registro no painel do Supabase.

## Link do deploy

https://gastosmart-3nje.onrender.com