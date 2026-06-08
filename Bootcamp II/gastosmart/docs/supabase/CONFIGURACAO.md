# Configuração do Supabase

Guia rápido para conectar o GastoSmart ao projeto Supabase do grupo.

## Dados do projeto

- URL: `https://jqetggonptxjqjpapjps.supabase.co`
- Chave (publishable): `sb_publishable_XaI_Sb_1onqHfiFMHwwU5Q_wrcAXTxf`

> A chave acima é a chave pública (anon). Mesmo assim, **não commite** o `.env`. Apenas o `.env.example` deve viver no repositório.

## Passo a passo

### 1. Aplicar o schema

1. Abrir o dashboard do projeto.
2. Menu lateral → **SQL Editor** → **New query**.
3. Colar o conteúdo de [`schema.sql`](./schema.sql) e clicar em **Run**.
4. Conferir em **Table Editor** que a tabela `gastos` aparece.

### 2. Configurar `.env` local

Copie `.env.example` para `.env` na raiz do projeto e preencha:

```bash
SUPABASE_URL=https://jqetggonptxjqjpapjps.supabase.co
SUPABASE_KEY=sb_publishable_XaI_Sb_1onqHfiFMHwwU5Q_wrcAXTxf

# Opcional
OPENWEATHER_API_KEY=
OPENWEATHER_CIDADE=Brasilia
```

### 3. Testar a conexão

```bash
python -c "from supabase import create_client; import os; c = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_KEY']); print(c.table('gastos').select('*').execute())"
```

Saída esperada: estrutura `APIResponse` com `data=[]` (ou com registros se já houver).

### 4. Configurar deploy (Render)

No painel do Render, em **Environment** do serviço `gastosmart-3nje`:

- `SUPABASE_URL` = mesma URL acima
- `SUPABASE_KEY` = mesma key acima
- (manter) `OPENWEATHER_API_KEY` se já existir

Após salvar, dispare um deploy manual em **Manual Deploy → Deploy latest commit**.

### 5. Configurar secrets no GitHub (para CI de integração)

Em **Settings → Secrets and variables → Actions**:

- `SUPABASE_URL`
- `SUPABASE_KEY`

Esses secrets só são usados pelo job opcional de testes de integração (ver Issue #5).

## Como derrubar / recriar a tabela

```sql
drop table if exists public.gastos cascade;
```

E rode o `schema.sql` de novo.
