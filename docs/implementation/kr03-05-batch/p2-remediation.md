# KR03–KR05 batch review P2 remediation

Baseline review: Issue #6 comments 7220402787 / 7221120084.
Review base: 62760bfd4690279cf2a703be8cc908a92ef1d755.
Candidate registration: 52414a1b2781390d4a262b55d1259d9b15e60ad3.

Status: both P2 items have builder remediation and local regression evidence. They remain pending an independent exact-head delta review; this document is not an independent verdict.

## P2-01 — shared ModelSpec parameter-domain guard

Added model-domain-constraints.json and the shared tools.knowledge_import.model_spec validator. Every consumer must load the versioned domain contract and validate exact parameter names, strict numeric types (booleans rejected), ModelSpec lower/upper bounds, and model-specific constraints before formula evaluation.

- K10 Brier y0/y1: integer values in {0,1}.
- K10 fixed HLR half_life: strictly positive; lag remains nonnegative.
- K12 rectangle a/b: strictly positive.
- check_consumption.py uses the shared guard rather than duplicating these model-specific checks.
- Seven explicit fixtures: fractional/boolean Brier labels, zero HLR half-life, zero rectangle side, and valid controls. Result: 7/7 expected dispositions; shared guard unit tests: 4/4.

This is a shared knowledge-package execution contract, not a claim that a generic production runtime already exists.

## P2-02 — self-contained cross adapter and fail-closed domains

- X01 now carries explicit p/s/g/t values and a canonical parameter-preset digest; its 41/50 output is derived only from those fixture inputs and the bound BKT ModelSpec.
- Schedule adapter rejects booleans/non-numeric inputs, target outside (0,1), negative budget/cost, and nonpositive half-life; the half-life rule is enforced by the shared ModelSpec guard.
- Transfer adapter requires a positive integer day count (booleans, strings and floats HOLD), strict boolean flags and nonempty target identities.
- Added invalid X29–X41 fixtures covering target=2, negative budget/cost, boolean half-life/cost/target, days=true, days="1", days=0, days=1.0, and invalid BKT probability/boolean parameters. X42–X43 additionally reject both target endpoints.
- Builder replay: 43/43 cross fixtures; 36 exact source/receipt bindings retained.

These are bounded synthetic adapter tests only. Cross-version bindings are not canonical graph edges or generic runtime guarantees.

## Preserved limitations

P3-01 remains open: stable source-version/authority pinning, source proposition boundaries, BKT/Pashler missing source HOLD, and NIST/Belmont not being legal permission. Rights remain HOLD; CQ/LC NOT_RUN; no learner-effect, qualification, G03 or release claim.
