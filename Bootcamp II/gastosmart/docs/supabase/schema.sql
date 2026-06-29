-- =====================================================================
-- GastoSmart — Schema do banco no Supabase (Postgres)
-- =====================================================================
-- Como aplicar:
--   1. Acesse https://supabase.com/dashboard/project/jqetggonptxjqjpapjps
--   2. Vá em "SQL Editor" → "New query"
--   3. Cole o conteúdo deste arquivo e clique em "Run"
--   4. Confirme em "Table Editor" que a tabela "gastos" foi criada
-- =====================================================================

-- Tabela principal de gastos
create table if not exists public.gastos (
    id          bigserial primary key,
    descricao   text        not null check (length(trim(descricao)) > 0),
    valor       numeric(10,2) not null check (valor > 0),
    categoria   text        not null check (categoria in (
        'Alimentação','Transporte','Saúde','Lazer','Educação','Moradia','Outros'
    )),
    data        date        not null default current_date,
    criado_em   timestamptz not null default now()
);

-- Índices úteis para o resumo por categoria e ordenação cronológica
create index if not exists idx_gastos_categoria on public.gastos (categoria);
create index if not exists idx_gastos_data      on public.gastos (data desc);

-- =====================================================================
-- Row Level Security (RLS)
-- =====================================================================
-- O projeto não tem autenticação por usuário nesta etapa.
-- Política temporária: liberar leitura/escrita para a role "anon"
-- (a chave publishable usada pelo app é uma chave anon).
-- Em produção real, isso seria substituído por políticas por user_id.
-- =====================================================================

alter table public.gastos enable row level security;

drop policy if exists "anon pode ler gastos"      on public.gastos;
drop policy if exists "anon pode inserir gastos"  on public.gastos;
drop policy if exists "anon pode remover gastos"  on public.gastos;
drop policy if exists "anon pode atualizar gastos" on public.gastos;

create policy "anon pode ler gastos"
    on public.gastos for select
    to anon
    using (true);

create policy "anon pode inserir gastos"
    on public.gastos for insert
    to anon
    with check (true);

create policy "anon pode remover gastos"
    on public.gastos for delete
    to anon
    using (true);

create policy "anon pode atualizar gastos"
    on public.gastos for update
    to anon
    using (true)
    with check (true);

-- =====================================================================
-- Smoke test (opcional)
-- =====================================================================
-- insert into public.gastos (descricao, valor, categoria)
-- values ('Café da manhã', 12.50, 'Alimentação');
--
-- select * from public.gastos;
