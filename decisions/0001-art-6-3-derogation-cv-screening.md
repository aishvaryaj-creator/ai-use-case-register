# 0001 — Rejecting the Art. 6(3) derogation for SYS-001

**Status:** accepted · **Date:** 2026-08-01

## Question
Talent argued that the CV screening tool falls outside high-risk because it only
"improves the result of a previously completed human activity" — recruiters read the
same applications either way, and a human makes every rejection.

## Options
1. Accept the derogation, record the justification, register under Art. 6(4).
2. Reject it and treat the system as Annex III point 4(a) high-risk.

## Decision
Option 2. Art. 6(3) closes with an unconditional carve-out: a system is always high-risk
where it performs profiling of natural persons. Scoring candidates against a role profile
to produce a ranking is profiling within GDPR Art. 4(4), which the AI Act adopts. The
strength of the human-override argument is irrelevant once the carve-out bites.

## Consequence
The classifier encodes this as a hard override rather than a warning: any entry claiming
a filter condition while `profiling: true` is returned as high-risk with the claimed
ground named in the rationale. Deployer obligations under Art. 26 apply from 2027-12-02,
including the Art. 26(7) duty to inform workers and their representatives.

## What would change this
A redesign in which the tool returns no per-candidate score or ordering — for example,
extracting stated qualifications into fields without evaluation. That is a different
system and would need a new entry, not an amendment to this one.
