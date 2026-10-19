---
blueprint_state: 1
project: crypto-portfolio-optimization
starting_point: start
document_language: English
developers: 1
documents_at: docs/
tasks_at: docs/specs/
memory: journal
observability: journal
updated: 2026-10-18T23:06:00Z
updated_by: Antigravity
---

# Project state

## Project kind

| Fact | Value | Known how |
|---|---|---|
| has-screens | no | deduced |
| stores-data | yes | deduced |
| holds-personal-data | no | deduced |
| used-by-command-or-code | yes | deduced |
| calls-a-model | yes | deduced |

Deduced: A coursework optimization project in Python (exact solvers plus a metaheuristic) on public crypto price data, with an ML forecasting stage in A2; no screens and no personal data.

## Criteria the person declared

- Deadlines: A1 (stages 1 to 3) on 2026-10-19, A2 (stages 4 and 5) on 2026-12-07, from the course PDF.
- Works alone.
- Documents in English.
- Wants a high-level project with software engineering rigor.
- Only data that is legal to use: public data, no personal data, no company data.
- Delivered as a Google Colab link. The evaluator reads and runs the code there, and the student explains the work in class. If there is more than one notebook, all of them must run in Colab without errors.
- Two deliverables: the Colab notebook for the evaluator, and a thin, professional repository for the portfolio at github.com/erickcmendes/CEUB, which already exists. The repository will not hold the price data.
- Free tools only: free Colab, no paid service.
- Everything is done in notebooks, with the text inside them in Portuguese. One command (Run all) reproduces the results.
- Acceptance for A1 approved: formulation complete, exact model solved by the three solvers and reproducible with one command, genetic algorithm gap to the optimum reported.
- Tools named by the course PDF: Pyomo or PuLP, solvers CBC, Ipopt and Couenne, and DEAP or Simulated Annealing.

## Steps

| Step | Situation | Main questions |
|---|---|---|
| system-description | closed | 4 of 4 |
| requirements | closed | 3 of 3 |
| modeling | open | 3 of 4 |
| architecture | closed | 3 of 3 |
| plan | closed | 1 of 1 |

## Documents

| Document | Situation | Where |
|---|---|---|
| system-description | ready | docs/system-description.md |
| requirements | ready | docs/requirements.md |
| research | ready | docs/research.md |
| architecture | ready | docs/architecture.md |
| decisions | ready | docs/decisions.md |
| plan | ready | docs/plan.md |
| data-model | ready | docs/data-model.md |
| interface-contract | ready | docs/interface-contract.md |
| ai-features | ready | docs/ai-features.md |
| test-plan | ready | docs/test-plan.md |

## Main questions

### system-description

- [x] What problem the system solves, and for whom
- [x] What the person wants to achieve with it
- [x] How it reaches the people who use it
- [x] What stays out of the first version

### requirements

- [x] What each kind of user must be able to do
- [x] What limits the project: budget, deadline, law, what the person already uses
- [x] How to know it worked

### modeling

- [x] The journeys that cannot go wrong
- [x] What the system stores
- [x] Which commands or calls it offers
- [ ] What the model does in the product, and what the product does when it gets it wrong

### architecture

- [x] The stack and the environment (Python, solver distribution)
- [x] Where it runs (local machine or cloud)
- [x] Anything else that generates cost

### plan

- [x] What comes first

## Refinement questions left for later

- [ ] (modeling) Exact formulation choices: risk measure, cardinality limit, minimum and maximum weight, lots, transaction costs. Needed to write the formal formulation.

## Answers

### system-description · First block

- Document language: English. Developers: one, alone.
- Data: chose public crypto price data, with a portfolio selection problem under a cardinality limit (option 1 of three offered). The company data in dados/ is not used.
- Wants a high-level project with software engineering rigor, planned with Blueprint.
- Taken from the course PDF and the choice above: problem and audience (the student and the evaluator), deadlines, the five course stages, delivery as Python code plus a written analysis, and stages 4 and 5 left for A2.

### requirements · Delivery and acceptance

- Delivery: a GitHub repository (still to be created) and a Colab link. The evaluator reads and runs the code, and the student explains it in class.
- Environment: first said GitHub Codespaces, then corrected on 2026-10-16 to Google Colab (D-003). Everything in notebooks.
- Acceptance for A1: approved as proposed, (a) formulation, (b) three solvers and one command, (c) genetic algorithm gap.

### modeling · What the evaluator receives

- Yes to one command that runs everything. Delivery is a Colab link, so with more than one notebook all of them must run in Colab without errors. Taken as the journey that cannot go wrong: the evaluator opens the link, runs everything, and gets no error.
- The price data is uploaded to the Colab folder, and not to the GitHub repository. Where exactly it lives is open (D-004).
- The text inside the notebooks is in Portuguese.

### modeling · Where the data lives

- Chose option A for D-004: one price file in Google Drive shared with anyone who has the link, downloaded by the first cell with gdown and checked by a checksum.
- Taken by the agent: Pyomo is used for all three solvers, since PuLP only handles linear models.

### architecture · Data source, deliverables and cost

- Prices: extract with yfinance (D-002). The student chose it against the recommendation of a Kaggle dataset, because they have used it before and had no problem with data use.
- Two deliverables are needed in the end: a Colab notebook for the evaluator, and a thin, professional repository for the portfolio at github.com/erickcmendes/CEUB (D-005).
- Cost: free Colab, nothing paid.

### architecture and plan · Recommendations accepted

- The student accepted every recommendation: D-006 (one package with tests plus a Colab notebook that installs it at a pinned tag) and the order of the plan (extract the prices, then the formulation, then the repository structure).
- Taken by the agent: package name portfolio_opt; formulation defaults to be reviewed in task 02-01; the solver check in Colab goes first because it is the biggest risk.

## Decisions

- D-001 · Use public crypto price data, not the company data · decided
- D-002 · Which public source of crypto prices · decided
- D-003 · Delivery and run environment: Google Colab · decided
- D-004 · Where the price data lives for the Colab delivery · decided
- D-005 · Two deliverables: a Colab notebook and a portfolio repository · decided
- D-006 · How the notebook and the repository share one codebase · decided

## Open points

- Overlap with the student's earlier crypto portfolio work in another course. Depends on the student and the professor.
- Whether Couenne, Ipopt and CBC install in a fresh Colab runtime. Depends on a test (T-002).
- Yahoo Finance terms of use for the extracted prices, and whether yfinance extraction works. Depends on tests (T-001, T-004).
- The repository must be public, and the pinned tag must exist, when the evaluator runs the notebook. Depends on the student (T-005).
- The ML model's role in A2: what it predicts, and what happens when it is wrong. Not answered yet, and not needed for A1. Depends on the student.

## Next question

The plan is closed. Next: prepare the repository with blueprint-setup, then start task 01-01. The student runs the solver check in Colab and reports the result.
