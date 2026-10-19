# Repository skeleton

**Phase:** 1 · Foundations · **Situation:** not started

## What it does

The project folder inside github.com/erickcmendes/CEUB with the layout of the architecture: `pyproject.toml` with pinned dependencies, empty modules, `pytest` set up, an English README, and the Blueprint documents in `docs/`. The folder name follows the repository's own organisation.

## What it does not do

It does not hold any model or data code yet, and it does not make the repository public.

## Done when

- [ ] The repository's current organisation was read, and the project folder fits it
- [ ] `pip install` of the package from a subfolder works on a clean machine
- [ ] `pytest` runs and passes with the placeholder test
- [ ] The student agreed to give access to the repository first

## Comes from

NFR-06, D-005, D-006. Needs the student's permission to attach the repository. These are the identifiers the code will carry as anchors, so that anyone can ask why that code exists and get the answer from the code itself.

## Result of the delivery

Delivered `pyproject.toml`, English `README.md`, `src/portfolio_opt` structure, and automated testing via `pytest`. Installed `portfolio_opt` in editable mode and verified `pytest` passing.

## How to test

Run `python -m pytest` from the root of `crypto-portfolio-optimization`. Verify that the test suite runs and `tests/test_skeleton.py` passes.
