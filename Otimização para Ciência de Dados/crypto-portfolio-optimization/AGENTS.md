<!-- blueprint:start -->
## Blueprint

Crypto portfolio optimization for the course Optimização Aplicada à Ciência de Dados (CEUB): one Python package with tests, plus a Portuguese Google Colab notebook that the evaluator runs. A1 is due 2026-10-19 and A2 on 2026-12-07.

| What | Where |
|---|---|
| The documents | `docs/` |
| The plan, and one spec per task | `docs/plan.md`, `docs/specs/` |
| Where the project is, for any session | `.blueprint/state.md` |
| The decisions, each with its reason | `docs/decisions.md` |
| What is left to verify | `docs/test-plan.md` |
| Why a line of code is the way it is | Ask it: the `blueprint-explain` skill answers from the code |
| The journal: one record per session, and the milestones | `.blueprint/journal/` |

### How to work here

1. **Read `.blueprint/state.md` before you answer.** It says where the project
   is. Never act as if you remembered a conversation: it may have been another
   session, another day or another agent.
2. **One task at a time, from the plan, in order.** The task's spec says what it
   does, what it does not do, and when it is done. **Say which task you are on,
   by its number and its name, before you start it** — the person has to be able
   to tell which one you chose without reading the plan again.
3. **Every delivery says how to test it, and where to look first:** what to run
   or open, what should be seen, and the two or three riskiest places in what
   changed, hardest first. It goes in the spec's "Result of the delivery" and
   "How to test", and in what you tell the person. Risk is not size: what touches
   money, personal data, permissions or deletion comes before what is long.
4. **The code carries the id of what it serves.** A requirement that became code
   gets its id — FR-01 — in a comment where that behaviour begins, and in the
   name of the test that proves it. That one line is what lets anyone ask "why is
   this the way it is?" and be answered from the code, without reading a
   document. Not every file needs one, and an id that no document has is a
   mistake to report, not to keep.
5. **Deliver in increments someone can review.** One commit per requirement.
   About 400 changed lines or 10 files is what one person reviews in one sitting,
   new files included; past that, split the delivery and say how you split it. A
   change nobody can review is not understood, however well it is documented.
6. **Record what happened.** At the end of a session, one record in
   `.blueprint/journal/sessions/`. A decision that is costly to undo goes to
   `docs/decisions.md` with its reason, who decided and the date. A phase
   delivered goes to the milestones.
7. **A change the plan does not cover.** If it is small, do it and say in one
   line what you did. Small means: it touches one part of the code, it brings no
   decision that is costly to undo, it brings no new fact about the project (the
   first screen, the first stored data, the first personal data, the first
   command, the first call to a model), and it fits in one task. If it is not
   small, write its spec with the person before you write code.
8. **A decision that is costly to undo is the person's:** the stack, hosting,
   how personal data is handled, anything that generates cost. Bring options and
   a recommendation, and wait.
9. **Never write a key, a token or a password** in a file of this project.

### Rules of this project

- Documents are written in English. The text inside the notebooks is in Portuguese.
- The price data is never committed to GitHub. It lives in a shared Google Drive file, checked by a checksum.
- All logic goes in the package `portfolio_opt`. Notebooks only call it and explain it.
- The project uses no personal data and no company data. The old company data folder of the course is not to be read or used.
- Results must be reproducible: fixed seeds and pinned versions.

### The method

The documents and the plan of this project were written with Blueprint, and the
rules above come from it. This file, the documents and the plan are enough to go on.
<!-- blueprint:end -->
