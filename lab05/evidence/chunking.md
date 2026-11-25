# Lab 5 Chunking Experiment

Documents: appointments_and_visits.md, lab_test_preparation.md, nhis.md, opening_hours.md, services.md

| Chunk size | Overlap | Chunks | Avg length |
|---|---|---|---|
| 300 | 50 | 21 | 282 |
| 300 | 100 | 25 | 285 |
| 500 | 50 | 14 | 398 |
| 500 | 100 | 14 | 430 |
| 800 | 50 | 10 | 537 |
| 800 | 100 | 10 | 562 |

## Choice

We use 500 characters with 100 characters of overlap. This keeps most chunks within a single paragraph or section, while the overlap preserves sentences that cross a boundary. 300 characters produced too many tiny chunks; 800 characters blended unrelated sections.