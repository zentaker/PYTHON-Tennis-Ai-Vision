# Stage 8.1 Expanded Ball Labels and Timeline Validation Report

## Verdict

- Final verdict: needs_more_labels
- Friction score: 32
- Friction level: medium friction

## Label expansion summary

| Metric | Value |
|---|---:|
| existing labels | 5 |
| new labels | 0 |
| merged labels | 5 |
| visible labels | 5 |
| frame range | 120 to 180 |
| average label gap | 15 |
| maximum label gap | 15 |

## Candidate validation summary

| Metric | Value |
|---|---:|
| candidate comparisons | 5 |
| average distance | 3.73 |
| median distance | 3.0 |
| frames within 10 px | 5 |
| frames within 25 px | 5 |
| frames within 50 px | 5 |
| frames within 100 px | 5 |
| frames within 200 px | 5 |

## Timeline validation summary

| Metric | Value |
|---|---:|
| timeline events | 5 |
| supported events | 5 |
| unsupported events | 0 |
| outside coverage events | 0 |
| adjusted confidence notes | See validated timeline CSV. |

## Product Owner interpretation

Stage 8.1 validates the Stage 8 timeline against expanded ball labels. The current run used 5 merged labels with 5 visible ball labels. Candidate quality remains strong where labels exist, but coverage is still too sparse for tactical metrics.

## Warnings

- Non-interactive mode used existing labels only; no new labels were collected.
- Label coverage is still sparse for tactical metrics; collect more labels across the rally.

## Errors

No errors.

## Next step

Run Stage 8.1 interactively across more frames, then rerun timeline validation.
