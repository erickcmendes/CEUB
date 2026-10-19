# Test plan

**Project:** crypto-portfolio-optimization · **Version:** 0.1 · **Date:** 2026-10-15

> **In short:** Five things are left to verify before the model work: the terms of use of the data, the extraction itself, the solver installation in Colab, the data location and the package install from GitHub. None is done.

## To verify

| # | What to verify | Comes from | How | Situation |
|---|---|---|---|---|
| T-001 | Yahoo Finance terms of use allow the academic use of the extracted prices, and sharing the fixed snapshot with the evaluator through Drive | D-002 | Open and read the Yahoo Finance terms of use, and note the result | to do |
| T-004 | yfinance extracts the chosen assets over the chosen window from the student's environment, and the snapshot file is created. Yahoo is known to rate-limit some cloud IPs, which was not verified here | D-002 | Run the extraction script once and check the file against the data model | to do |
| T-002 | CBC, Ipopt and Couenne install in a fresh Google Colab runtime, in one setup cell, and solve a toy problem from Pyomo. The Python version there is recorded | D-003 | In a new Colab runtime, run the setup cell, solve a two-variable test model, and note python --version and the install time | to do |
| T-003 | A fresh Colab runtime finds the price data and runs all notebooks from top to bottom without errors | D-004 | Open the delivery link in a private window or a second account, use Run all, and check that gdown downloads the file and the checksum matches | to do |
| T-005 | A fresh Colab runtime installs the package from a subfolder of github.com/erickcmendes/CEUB at the pinned tag, with the repository public | D-006 | In a new runtime, run the setup cell and import the package | to do |
