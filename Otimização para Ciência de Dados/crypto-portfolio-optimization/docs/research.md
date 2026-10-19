# Research

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-15

> **In short:** Three data scenarios were compared and public crypto prices won. The company data was inspected and ruled out. No specific dataset was chosen or checked yet.

## Which data base fits the project?

- **Decision:** Public daily crypto prices (D-001).
- **Reason:** Legality first, then fit with the five course stages, then the four days to A1.
- **Alternatives:** Company data: 209,560 rows and 40 columns, with CPF, name, e-mail, phone, birth date and surgery and risk data, plus bank details in the complaints files; sensitive personal data under LGPD arts. 5 II and 11, trade secret, collected for another purpose, and 95% of the rows are one specialty. Health service location in the DF: not confirmed that a ready dataset exists. Feature selection: weak exact model.
- **Sources:** Kaggle crypto dataset listing, [baselight.app mirror](https://baselight.app/u/kaggle/dataset/patrickhallila1994_daily_prices_for_2700_cryptocurrencies), read 2026-10-15, not the official page and licenses not checked; local profile of the company files, 2026-10-15.

## Which route installs Couenne and Ipopt?

- **Decision:** Left open.
- **Reason:** Only search results were seen. The IDAES documentation on [binary packages](https://idaes-pse.readthedocs.io/en/stable/_sources/tutorials/getting_started/binaries.rst) is the lead, read as a search result on 2026-10-15, page not opened.
- **Alternatives:** Not compared yet.
- **Sources:** [Running Pyomo on Google Colab, ND Pyomo Cookbook](https://nbviewer.jupyter.org/github/jckantor/ND-Pyomo-Cookbook/blob/master/notebooks/01.02-Running-Pyomo-on-Google-Colab.ipynb) and [AMPL on Colab](https://ampl.com/colab/getting-started.html), both seen as search results on 2026-10-16, pages not opened.

## Which source for the crypto prices (D-002)?

- **Decision:** The student chose yfinance (Yahoo Finance), against the recommendation of a Kaggle dataset with a stated open license. The prices are extracted once and kept as a fixed snapshot in Drive (D-004).
- **Reason:** The student has used yfinance before and had no problem with the use of its data.
- **Alternatives:** A Kaggle dataset with a stated license (recommended, not taken); the CoinGecko API, which needs a key and whose terms were not read.
- **Sources:** [Kaggle crypto dataset listing](https://baselight.app/u/kaggle/dataset/maharshipandya_cryptocurrency_historical_prices_dataset), a search result seen on 2026-10-16; opening it returned an unrelated page, so nothing was read from it. [CoinGecko API pricing](https://www.coingecko.com/en/api/pricing), a search result seen on 2026-10-16, page not opened. The Yahoo Finance terms were not read.

## How should the Colab notebook and the portfolio repository relate (D-005, D-006)?

- **Decision:** D-005 decided: both deliverables are needed. D-006 decided: one package with tests in the repository, and a Colab notebook that installs it at a pinned version. The student took the recommendation.
- **Reason:** One codebase, no drift, and the work is done once.
- **Alternatives:** Two copies kept in step by hand.
- **Sources:** reasoning from the requirements; no external source.

## Not verified

- The license and coverage of any specific crypto price dataset (T-001).
- Whether Couenne and Ipopt install and run in a fresh Google Colab runtime (T-002).
- Whether a ready public dataset exists for the health service option.
- That pip installs the package from a subfolder of github.com/erickcmendes/CEUB at a tag inside Colab (T-005).
- The Yahoo Finance terms of use for the extracted prices (T-001), and whether yfinance extraction works from the student's environment (T-004).
- That Pyomo with CBC, Ipopt and Couenne installs in one setup cell in Colab.
