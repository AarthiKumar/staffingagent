# Candidate Deduplication Pathways (Feasibility Review)

This note summarizes two practical deduplication pathways for the staffing-agent ingestion flow.

## Pathway A: Strict Identity-Based Dedup (Current + Hardening)

- **Signals**: normalized email, normalized phone, optional exact full-name match.
- **Pros**:
  - deterministic, explainable, low operational risk.
  - easy to audit and rollback.
- **Cons**:
  - misses duplicates when contact info changes or is missing.
  - sensitive to extraction errors.
- **Fit**: best as the default hard gate for auto-link/auto-merge candidates.

## Pathway B: Probabilistic Profile Dedup (Recommended as Secondary)

- **Signals**:
  - soft name similarity (token overlap / edit distance),
  - overlapping employers, role titles, skills, certifications,
  - optional embedding similarity on summary/experience text.
- **Pros**:
  - catches "same person, different email/phone/CV version" cases.
  - can recover value where strict keys are unavailable.
- **Cons**:
  - needs threshold tuning and QA feedback loop.
  - should be human-review first (not auto-merge).
- **Fit**: best as a review queue (`requires_approval`) after strict checks.

## Recommended Hybrid Flow

1. Run strict identity match first (Pathway A).
2. If no strict match, run probabilistic scoring (Pathway B).
3. If score exceeds high threshold, create merge proposal and require manual approval.
4. Log accepted/rejected proposals for threshold tuning.

## Data Model/Implementation Notes

- Keep both CV documents regardless of merge outcome.
- Track dedup source (`strict`, `probabilistic`) and confidence in proposal metadata.
- Add observability counters for proposal frequency and acceptance rate.
