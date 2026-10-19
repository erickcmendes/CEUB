# Release and delivery

**Phase:** 3 · A1 delivery · **Situation:** not started

## What it does

A tag on the repository, the repository made public, the Drive file shared by link, a final Run all in a private window, and the Colab link ready to submit by 2026-10-19.

## What it does not do

It does not add features: anything new after the final run waits for A2.

## Done when

- [ ] The tag exists and the notebook installs exactly that tag
- [ ] The Drive link works for someone who is not the student
- [ ] The final Run all passed on the day of delivery
- [ ] The Colab link was submitted

## Comes from

FR-05, NFR-05, NFR-06, T-003, T-005. Waits for the student to make the repository public and to submit. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Prepared release readiness: verified package installation, checksum calculation (`10d98d487cc565341296462c5cb29efa876e0dbf56cdcde46310aa73b21eaba8`), consolidated deployment checklist in `docs/pendencias_consolidadas.md`, and documented instructions for GitHub repository tagging and Google Drive link sharing.

## How to test

Follow the checklist in `docs/pendencias_consolidadas.md`:
1. Push code to `github.com/erickcmendes/CEUB` and tag `v0.1.0`.
2. Share `data/crypto_prices.csv` via Google Drive and update `drive_file_id` in the notebook if needed.
3. Open `notebooks/a1_colab_pt.ipynb` in a private browsing window on Google Colab, execute "Run all", and verify end-to-end execution.
