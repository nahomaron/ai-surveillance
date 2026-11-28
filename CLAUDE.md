# CLAUDE.md — Standing instructions for RQ1 engineering agents

Claude Code leads RQ1 engineering, architecture, integration and the detailed data strategy. Codex provides independent audit and review and may implement authorized corrections or assigned work. D-67 schedules E1 worker–forklift exposure and E2 elevated-load measurement in parallel, with candidate near-miss evaluation and independent human review where feasible. This phase targets a reproducible Master's engineering prototype using synthetic data.

At session start, inspect Git state, recent contributions, `WORKPLAN.md`, decisions and open CRs. Coordinate concurrent edits through isolated branches. Record material work, audit findings and independent review in [the agent contribution register](docs/AGENT_CONTRIBUTIONS.md), and record progress in `WORKPLAN.md`.

## Documents and precedence

1. The normative contract **E-1.2.26** consists of three files:
   - `docs/contract/RQ1_Contract_Reference_E-1.2.1_FROZEN.md`;
   - `docs/contract/Package_F1_…md` **Part A and Appendix N**;
   - `docs/contract/RQ1_Contract_Appendix_T_E-1.2.3.md`, which supplies the text of every cited rule, test and fixture ID, and the amendments in sections T7 (E-1.2.4), T7.1 (E-1.2.5), T8 (E-1.2.6), T9 (E-1.2.7), T10 (E-1.2.8), T11 (E-1.2.9), T12 (E-1.2.10), T13 (E-1.2.11), T14 (E-1.2.12), T15 (E-1.2.13), T16 (E-1.2.14), T17 (E-1.2.15), T18 (E-1.2.16), T19 (E-1.2.17), T20 (E-1.2.18), T21 (E-1.2.19), T22 (E-1.2.20), T22.14 (E-1.2.21), T23 (E-1.2.22), T23.16 to T23.27 (E-1.2.23), T23.28 (E-1.2.24), T24 (E-1.2.25) and T25 (E-1.2.26).

   Precedence: F.1 Part A and Appendix N > Appendix T > E-1.2.1 body.

   T23 and its workflow tables are implemented on v02-review-ui only; on this branch only the adjudication namespace rule (T23.16, VR-E-056) and the reference accessor are implemented.

   Packages E, E.1, the E.1 Errata and the Clarification are **not** contract documents.
2. D-67 and Appendix T26 govern prospective synthetic scope, terminal D-66 closure and agent roles. The [measurement plan](docs/plan/Measurement_Improvement_and_Scientific_Validation_Plan.md) and `docs/plan/Package_F_Implementation_Agent_Handoff.md` §14 give the new work packages. Earlier role and orchestration text in Package F and F.1 Parts B and C is historical.
3. `WORKPLAN.md`: task order, stop points and progress.
4. `docs/methodology/*`: background rationale only. **Never implement from it.**

If the contract is silent or contradictory, **do not invent a definition**. Write an entry in `docs/CHANGE_REQUESTS.md`, mark the task `BLOCKED`, and move to the next task that does not depend on it.

## Agent authority to close contract gaps

You may resolve a gap yourself, without waiting for the Owner, when ALL
of these hold:
- It concerns representation or engineering only: a field type,
  nullability detail, naming, a helper or index field, an error code,
  file layout, module structure, a test-fixture detail, or wording
  missing from a rule whose intent is clear from the contract.
- Your choice changes no measured value, label, flag, denominator,
  estimator, unit, coordinate frame, timebase, sampling or leakage rule,
  reference-independence rule, acceptance criterion, E2 rule or report
  wording.
- It contradicts nothing in E-1.2.26.

How to resolve:
1. Write an "Agent Resolution" entry AR-<n> in docs/CHANGE_REQUESTS.md:
   the gap, the options you considered, your choice, why it does not
   affect measurement meaning, the files and tests affected, and how to
   reverse it.
2. Add a test that pins the choice.
3. Mention the AR in the Progress log, and continue.

As evidence when writing an AR, you may read Packages E, E.1, the E.1
Errata and the Clarification (read-only). They never override E-1.2.26.
Cite the passage you relied on.

Still raise a CR, mark the task BLOCKED, and continue with independent
tasks when:
- the gap affects measurement meaning in any of the ways listed above;
- two plausible readings would give different numbers; or
- you are unsure which category the gap is in. Treat that as
  meaning-affecting.
- A change that alters a research objective, a measurement's meaning, population or denominator, independent validation or leakage, the permissible claims, or scope or resources is a scientific decision. Raise a CR even when the code change is small.

Your authority does not cover: downloads beyond the approved cap,
installs not pre-approved in WORKPLAN §0, paid or external services,
real footage, history rewrites or deletions.

All AR entries are reviewed at the G-M0 stop, and the Owner or the
Research Architect may reverse any of them.

## Never

- Change definitions, units, coordinate frames, sampling or leakage rules, acceptance criteria, labels or reporting wording in the contract.
- **Edit an expected value in a test to make it pass.** Expected values come from Appendix N or hand calculation recorded in the test. A mismatch is a defect in the code or a contract question (CR); never adjust the expectation.
- Produce safety scores, combined safety indicators, OSHA linkage or submission, automated recordability decisions, establishment rankings, or E2 energy, fall-probability or severity quantities. Never treat monitored time as hours worked, or present simulated data as establishment evidence. Exception (D-48, T23, T23.27): the local workflow demo with fictional establishments may hold human-entered incident fields and a view-time incidence rate, on `v02-review-ui` only. These limits govern the present RQ1 work and do not exclude separately authorised future research.
- Call an automated output a "near miss", "collision" or "contact". Use "candidate", "suspected", "undetermined".
- Say "validated" for anything run on synthetic data or fixtures. Use the three statuses: implemented / verified / empirically validated (with scope).
- Download datasets, install system software (Homebrew and the like), use paid services or send data off this computer **unless `WORKPLAN.md` §0 shows the Owner pre-approved it**.
- Use real worker footage in the D-67 phase or commit datasets, videos or large binaries to Git. D-21 is historical for this phase.
- Open or process the closed SDG final test or any of its derivatives. D-66 is permanent. Cite published aggregate reports. Maintain reservations on all other evaluation data unless a formal amendment is explicitly approved.
- Force-push, rewrite history or delete branches.
- Run code from before E-1.2.23 against `out/review/`.

## Work loop (every task)

1. Read the task in `WORKPLAN.md` and every contract section it cites.
2. **Write the tests first**, using expected values from Appendix N or a recorded hand calculation.
3. Implement until the task's tests **and the full suite** pass.
4. Run the full suite a second time. Exact-class outputs must be identical (same artifact IDs).
5. Tick the task, append an entry to the Progress log in `WORKPLAN.md` (template in §6), commit, and **push**.
6. At a **STOP** task, write the request in `DECISIONS_NEEDED.md`, push, and stop working on anything that depends on it. Continue only with tasks marked independent of it.
7. Never commit or push in a command chain that does not stop on a failed test run. Use `pytest ... && git commit ... && git push`, or check the exit status explicitly. A push with a failing suite is recorded in the Progress log.

## Engineering conventions

- Python, in the project virtual environment `.venv` (see WORKPLAN S-01). Pin dependencies in `requirements.lock`.
- Package layout `src/rq1/<module>/`, tests in `tests/`, fixtures in `fixtures/`, generated outputs in `out/` (git-ignored).
- Determinism: no wall-clock time or unseeded randomness in data payloads; seeds come from configuration; inputs are sorted canonically before solvers.
- Commit subjects use `[CLAUDE] Description` or `[CODEX] Description`. Include the task ID where useful. Use non-Owner Git authorship or commit metadata and record joint contributions accurately. Preserve previous history. Push at least at the end of every task and every session. Tag milestones (`m0-verified`, `m1a-complete`, …).
- Keep sessions small: finish and push one task (or a clearly marked part of one) before starting the next, so an interrupted session loses little.
