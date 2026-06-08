# Fluxo do GitHub

> Define como a equipe trabalha com issues, branches, PRs e revisões. Esta é a **source of truth viva** do projeto — issues e PRs novos são adicionados aqui automaticamente pela IA (ver mandato em [`../config/system.md`](../config/system.md)).

---

## Repositório

- **URL:** https://github.com/erickcmendes/gastosmart
- **Branch principal:** `main` (protegida socialmente; futuramente via branch protection rules)
- **Owner:** [@erickcmendes](https://github.com/erickcmendes)
- **Visibilidade:** público (exigência da disciplina)

---

## Issues ativas / conhecidas

> A IA mantém esta lista. Adiciona novas issues quando elas aparecem na conversa, no `git log`, ou são criadas pelo time. Atualiza status sempre que muda.

| # | Título | Responsável | Status | Vinculada ao PR |
|---|---|---|---|---|
| [#4](https://github.com/erickcmendes/gastosmart/issues/4) | Configurar Supabase e criar camada de repositório | @erickcmendes | em andamento | [#3](https://github.com/erickcmendes/gastosmart/pull/3) |

### Issues planejadas para a entrega final (a serem criadas)

Estas estão pré-redigidas em [`../../docs/ISSUES_GITHUB.md`](../../docs/ISSUES_GITHUB.md). Vão ser criadas na reunião do time de 08/06/2026 à noite:

- Migrar regras de negócio para `src/services.py` (Lucas)
- Manter integração com OpenWeather (Lucas)
- Atualizar suíte de testes e CI (João)
- Atualizar deploy no Render com Supabase (Cauã)
- README final + PDF de entrega (Cauã)

Quando forem criadas, **a IA atualiza esta tabela imediatamente** com os números reais (`#5`, `#6`, etc.).

---

## PRs do projeto

> A IA mantém esta lista. Adiciona novos PRs quando eles aparecem na conversa ou no `git log`. Atualiza status.

| # | Título | Autor | Branch | Status | Revisor |
|---|---|---|---|---|---|
| [#3](https://github.com/erickcmendes/gastosmart/pull/3) | feat: configuração do Supabase e camada de repositório | @erickcmendes | `feature/supabase-config-e-repository` | aberto, aguardando revisão | @lucasmalinski |

---

## Fluxo de trabalho

### 1. Pegar uma tarefa

- Olhe as issues abertas em https://github.com/erickcmendes/gastosmart/issues.
- Escolha uma sem assignee e atribua a você (`Assignees → @seu-user`).
- Mude o status para "In progress" (label, projeto kanban, ou apenas via comentário "começando").

### 2. Criar a branch

A partir da `main` atualizada:

```powershell
git checkout main
git pull
git checkout -b <prefixo>/<descricao-curta>
```

Prefixos: `feature/`, `fix/`, `chore/`, `docs/`, `ci/`.

### 3. Trabalhar

- Commits pequenos e frequentes.
- Mensagem em [Conventional Commits](../coding_conventions.md#conventional-commits).
- Antes de cada commit, rodar `ruff` e `pytest`.
- Atualizar `.ai/` se a mudança afetar arquitetura, requisitos, padrões, stack ou termos.

### 4. Antes de abrir o PR

Checklist em [`../coding_conventions.md`](../coding_conventions.md#checklist-rápido-antes-de-commitar) deve estar 100%.

### 5. Abrir o PR

```powershell
git push -u origin <nome-da-branch>
```

O terminal imprime o link `https://github.com/erickcmendes/gastosmart/pull/new/<branch>`. Abrir, preencher título e corpo.

**Título:** segue Conventional Commits. Ex.: `feat: migrar serviços para usar Supabase`.

**Corpo:** usa o template já no repositório (`.github/pull_request_template.md`). Sempre incluir:

- `Closes #N` (uma ou mais issues vinculadas)
- Lista do que foi feito
- Checkboxes "Como testar"
- Checklist do template

**Reviewer:** outro integrante da equipe (Lucas, João ou Cauã — não o autor).

### 6. CI verde

Esperar a CI rodar (~1 min). Se vermelha:

- Olhar o log.
- Corrigir local.
- Empurrar de novo (`git push`). O PR atualiza automaticamente.

### 7. Revisão

O revisor segue [`../docs/pr-review-checklist.md`](../docs/pr-review-checklist.md).

Possíveis resultados:

- **Approve** → autor pode mergear.
- **Request changes** → autor aplica mudanças e empurra de novo.
- **Comment** → discussão; autor decide se aplica.

### 8. Merge

**Estratégia: Squash and merge.** Sempre.

Após o merge:

- GitHub fecha automaticamente as issues vinculadas (`Closes #N`).
- O Render dispara auto-deploy.
- Deletar a branch quando o GitHub oferecer.
- **A IA atualiza esta lista**: muda status do PR para `mergeado` e move a issue para fechada.

---

## Convenções específicas

### Nomes de branch

- `feature/supabase-config-e-repository`
- `feature/migrar-services-para-supabase`
- `fix/categoria-invalida-mensagem`
- `chore/atualizar-ai-pos-pr5`
- `docs/readme-stack-final`
- `ci/integracao-supabase-secrets`

### Mensagens de commit

```
feat: migrar adicionar_gasto para usar repository (Closes #5)
fix(services): corrigir validacao de valor zero
chore(.ai): atualizar ARD com decisao de squash and merge
docs: ajustar README com link do deploy
ci: rodar integracao com supabase apenas em main
```

### Tamanho do PR

- Ideal: < 400 linhas de diff excluindo testes e docs.
- Se passar, o autor justifica no corpo ou divide.

### Reviewer obrigatório

- Toda PR precisa de **pelo menos 1 aprovação** de outro integrante.
- O autor **nunca** mergeia seu próprio PR sem aprovação.

---

## Casos especiais

### Commit foi parar na main por engano

1. Identifique o hash com `git log --oneline -5`.
2. `git checkout main && git pull`
3. `git revert <HASH>` → cria commit de revert.
4. `git push origin main`
5. Recrie a branch da feature limpa, traga o commit de volta via `git cherry-pick <HASH>`, empurre, abra PR.

(Esse caminho já foi exercitado uma vez no projeto — durante o PR-01.)

### Conflito de merge

- Mantenha a branch atualizada com `git fetch origin && git rebase origin/main`.
- Resolva conflito local, rode `ruff` + `pytest` de novo, empurre.

### Force-push

- **Proibido em `main`** (Regra Dura #8).
- Em branches de feature, use **apenas** `git push --force-with-lease` e avise o time.

### Branch protection rules (futuro)

Quando o time conseguir, configurar em `Settings → Branches → main`:

- Require pull request before merging
- Require status checks to pass before merging (`quality` da CI)
- Require approvals (1)
- Restrict who can push to matching branches (somente via PR)

---

## Para a IA

Quando você ler este arquivo e quiser atualizá-lo:

1. **Detectou issue ou PR novo?** Adicione a linha na tabela correspondente. Se a entrada já existe, atualize só os campos que mudaram.
2. **Detectou issue/PR fechado?** Mude status, mas mantenha a linha (histórico).
3. **Detectou mudança de fluxo (ex.: time decidiu trocar squash por rebase)?** Atualize a seção "Convenções específicas" + AD-13 em [`../docs/ARD.md`](../docs/ARD.md).
4. **Sempre mencione no resumo final** que o `github-workflow.md` foi atualizado, incluindo o que mudou.
