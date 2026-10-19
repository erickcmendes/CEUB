# Decisions

Every decision of the project, in one place, newest last. A decision is never
rewritten: when it changes, a new entry replaces it and says which one.

## D-001 · Use public crypto price data, not the company data

- **Decision:** The project uses public daily price data of crypto assets. The company data that was in dados/ is not used.
- **Reason:** The company data holds sensitive personal data and bank details, and a trade secret, so it fails the declared criterion of legal data. Public prices cover all five course stages and fit the 2026-10-19 deadline.
- **Alternatives:** Company data (not legal without written authorization and removal of identifiers, and poor quality anyway); health service location in the Distrito Federal (joining datasets is risky in four days, and no ready dataset was confirmed); feature selection as an optimization problem (the exact model would feel artificial).
- **Decided by:** the student · **Date:** 2026-10-15
- **Sources:** structure of the company files inspected locally on 2026-10-15, without reading personal values; see research.md.
- **Situation:** decided
- **To test:** -

## D-002 · Which public source of crypto prices

- **Decision:** The student extracts the prices once with yfinance (Yahoo Finance) and keeps them as a fixed snapshot file in Drive (D-004). The evaluator never calls yfinance.
- **Reason:** The student has used yfinance before and had no problem with the use of its data. They chose it against the recommendation.
- **Alternatives:** A Kaggle dataset with a stated open license (the recommendation, not taken); a public market data API such as CoinGecko.
- **Decided by:** the student · **Date:** 2026-10-16
- **Sources:** a Kaggle listing seen on 2026-10-15; no dataset page opened.
- **Situation:** decided
- **To test:** T-001 and T-004. Yahoo's terms of use for the extracted data, and that the extraction works from the student's environment.

## D-003 · Delivery and run environment: Google Colab

- **Decision:** The project is delivered as a Google Colab link. The evaluator runs it there, and with more than one notebook all of them must run without errors.
- **Reason:** It is how the student will hand it in, and it needs nothing installed by the evaluator.
- **Alternatives:** GitHub Codespaces, mentioned on 2026-10-15 and dropped before any work was done.
- **Decided by:** the student · **Date:** 2026-10-16
- **Sources:** -
- **Situation:** decided
- **To test:** T-002. The solvers must install in a fresh Colab runtime.

## D-004 · Where the price data lives for the Colab delivery

- **Decision:** The price data is one file in Google Drive, shared with anyone who has the link. The first notebook cell downloads it with gdown by file ID and checks a checksum. The file is not in GitHub.
- **Reason:** A fresh Colab runtime does not keep files uploaded to it, and the evaluator needs the data to run without errors.
- **Alternatives:** Download from the public source at run time (depends on the source being up, and the results can change); upload by hand into the session folder (the evaluator's runtime would not have it); mount the student's Drive (the evaluator would need access and to authorize it).
- **Decided by:** the student · **Date:** 2026-10-16
- **Sources:** -
- **Situation:** decided
- **To test:** T-003. gdown must work on a fresh runtime, and the checksum must match.

## D-005 · Two deliverables: a Colab notebook and a portfolio repository

- **Decision:** The project ends with two deliverables: a Colab notebook that the evaluator reads and runs, and a thin, professional repository for the student's portfolio at github.com/erickcmendes/CEUB. How they share code is D-006.
- **Reason:** The student needs both: the evaluator takes a Colab link, and the portfolio needs a clean repository. They chose it against the recommendation of a single self-contained notebook.
- **Alternatives:** One self-contained notebook for A1 (the recommendation, not taken).
- **Decided by:** the student · **Date:** 2026-10-16
- **Sources:** -
- **Situation:** decided
- **To test:** -

## D-006 · How the notebook and the repository share one codebase

- **Decision:** One Python package with tests in the repository, and a Colab notebook that installs it at a pinned version and prints the source of its main functions on screen.
- **Reason:** One codebase means the notebook and the repository cannot drift apart, and the work is done once, which matters with the deadline on 2026-10-19.
- **Alternatives:** Two copies, a self-contained notebook and a separate repository version: it works without GitHub, but it doubles the work and the two can diverge.
- **Decided by:** the student, by taking the recommendation · **Date:** 2026-10-17
- **Sources:** -
- **Situation:** decided
- **To test:** T-005. That a fresh Colab runtime installs the package from GitHub at the pinned tag, with the repository public.
