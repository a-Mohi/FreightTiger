# README

This project finds route-weeks where freight cost per tonne-km is unusually high and checks the supplied notes for a possible explanation. Weeks without a matching note are reported as unexplained.

## Quick start

```bash
pip install -r requirements.txt
python main.py
python eval.py
python check_repeat.py
```

`main.py` writes `outputs/output.csv`. The first run downloads the approximately 90 MB `all-MiniLM-L6-v2` embedding model. No API key is required.

## Project files

| File | Purpose |
|---|---|
| `costs.py` | Calculates weekly cost per tonne-km, historical and peer comparisons, and the flagging rule. |
| `rag.py` | Embeds the notes, stores them in an in-memory ChromaDB collection, and retrieves similar notes. |
| `main.py` | Runs the analysis and writes the output CSV. |
| `eval.py` | Checks selected results against hand-labelled cases. |
| `check_repeat.py` | Runs the pipeline repeatedly and compares the generated files. |

## Detection rules

- A route is represented as `origin-destination`.
- Weeks run from Monday to Sunday, with the Monday stored in `week_of`.
- Cost per tonne-km is total freight cost divided by the sum of `quantity * distance` for that route and week.
- The historical comparison uses the previous eight weekly values for the route, or all available previous values when fewer than eight exist. The current week is never included. A route's first week therefore cannot be flagged.
- The peer comparison uses the same week's other routes with the same `route_type`.
- A week is flagged when it is at least 10% above its own history, or at least 5% above its history and 15% above similar routes.

## Note matching

For each flagged week, the program embeds a question about the route and date, then retrieves the four closest notes for that route or for all routes. A note is used as an explanation only when:

- it describes an event that increases cost;
- it applies to the route or to all routes; and
- it is dated in the same week or within the preceding seven days.

Notes describing normal or unaffected costs are excluded. Explanations use the matched note's own text, ID, and date. When no note qualifies, `matched_note_id` is blank and the row remains flagged as unexplained.

## Output

`outputs/output.csv` contains suspicious weeks with these columns:

```text
route, week_of, cost_per_tonne_km, vs_own_history, vs_similar_routes, flagged, matched_note_id, reason
```

The output follows `data/sample_output_format_v2.csv`. `flagged` is either `Yes` or `No (justified)`, and `matched_note_id` is populated only for justified rows.

## Checks

Run the evaluation set with:

```bash
python eval.py
```

The repeat check runs the pipeline three times and compares the output hashes:

```bash
python check_repeat.py
```

The calculations and note selection are deterministic. Ties between equally close notes are resolved by note ID.

## Validation

I checked the results in three ways:

- `eval.py` tests 12 hand-labelled weeks covering justified increases, unexplained increases, and weeks that should not be flagged. It currently reports 12/12 correct, and the expected note was retrieved in all four cases where retrieval was required.
- The generated CSV reproduces the reference rows for Delhi-Jaipur on 2024-11-11, Ahmedabad-Mumbai on 2025-01-20, and Mumbai-Pune on 2025-09-15.
- `check_repeat.py` runs the full pipeline three times and compares the results. The files are identical on each run.

The labels in `eval.py` were written from the supplied notes, so this check confirms that the implementation follows those examples. It does not prove that the chosen thresholds are the only reasonable thresholds.

## Limitations

- The seven-day matching window does not cover a long-running event beyond its first applicable weeks.
- Keyword-based note checks can miss differently worded explanations.
- The size of a rise mentioned in a note is not compared with the observed increase.
- Weekly values are based on only three to five shipments, and some route types have just one peer.
- A sustained increase without a supporting note produces repeated unexplained flags and should be reviewed manually.
- The plain-English question interface and generated explanations are not implemented.
