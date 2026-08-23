# AI use-case register with risk classification

A working AI system inventory for a fictional EU/UK HR-tech SaaS company. Entries are
YAML, validated against a JSON Schema, classified against the EU AI Act by a rules
engine, and rendered to a published register. CI fails the build on a malformed entry
or an overdue review, so the register cannot rot silently.

> All data is synthetic. This is a portfolio project, not a record of client work, and
> nothing here is legal advice. No text from any ISO standard is reproduced; controls
> are referenced by identifier only.

## Run it

```bash
pip install -r requirements.txt
python src/build.py
```

## What the classifier actually decides

Evaluation follows the Act's own order: Art. 5 prohibitions → role determination →
Annex III enumeration → the Art. 6(3) filter conditions → Art. 50 transparency → GPAI.

Two decisions carry most of the weight, and the sample entries are chosen to exercise them:

- **Art. 6(3) with the profiling carve-out.** `SYS-001` claims the "improving a previously
  completed human activity" ground for CV screening. The engine rejects it, because the
  derogation is unavailable where the system profiles natural persons — and names the
  rejected ground in the rationale rather than silently overriding. See
  [`decisions/0001`](decisions/0001-art-6-3-derogation-cv-screening.md).
- **Art. 25 role flip.** `SYS-003` is recorded as a deployer but is white-labelled and
  substantially modified, so it is classified as a **provider**. For a company buying AI
  tooling this is the single most expensive misclassification available.

## Timeline position

Deadlines reflect Regulation (EU) 2026/1744 (Digital Omnibus on AI), in force 27 July 2026:
Annex III high-risk obligations 2 December 2027, Annex I 2 August 2028, Art. 50 transparency
unchanged at 2 August 2026 with Art. 50(2) reaching legacy systems on 2 December 2026.
Constants live in `DEADLINES` at the top of `src/classify.py`.

## Structure

```
schema/system.schema.json   the record contract CI enforces
register/systems/*.yaml     one file per use case — the source of truth
src/classify.py             the AI Act decision tree
src/build.py                validate → classify → render
templates/register.md.j2    published output
decisions/                  why each contested call was made
docs/                       generated; do not edit
```

## Cross-references

`vendor_ref`, `retention_ref` and `iso_42001_controls` are foreign keys into the companion
repositories (vendor privacy review, retention schedule, ISO/IEC 27701:2025 control library).
The register is the spine those hang off.
