import pandas as pd

from main import run
from rag import build_note_database, find_notes

LABELS = [
    ("Delhi-Jaipur",      "2024-11-11", "UNEXPLAINED", ""),
    ("Ahmedabad-Mumbai",  "2025-01-20", "JUSTIFIED",   "N002"),
    ("Chennai-Bangalore", "2025-02-24", "JUSTIFIED",   "N001"),
    ("Chennai-Bangalore", "2025-03-03", "JUSTIFIED",   "N001"),
    ("Chennai-Bangalore", "2025-03-10", "UNEXPLAINED", ""),
    ("Chennai-Bangalore", "2025-03-17", "UNEXPLAINED", ""),
    ("Mumbai-Delhi",      "2025-05-12", "JUSTIFIED",   "N003"),
    ("Mumbai-Pune",       "2025-09-15", "UNEXPLAINED", ""),
    ("Mumbai-Pune",       "2025-12-08", "UNEXPLAINED", ""),
    ("Delhi-Chennai",     "2025-02-03", "NOT_FLAGGED", ""),
    ("Mumbai-Delhi",      "2024-07-29", "NOT_FLAGGED", ""),
    ("Kolkata-Bhubaneswar", "2025-06-09", "NOT_FLAGGED", ""),
]

output = run(out_csv="outputs/eval_run_output.csv")
collection = build_note_database("data/context_notes.csv")

correct = 0
retrieval_hits = 0
retrieval_total = 0
for route, week, expected, expected_note in LABELS:
    match = output[(output["route"] == route) & (output["week_of"] == week)]
    if len(match) == 0:
        got, got_note = "NOT_FLAGGED", ""
    else:
        got = "JUSTIFIED" if match.iloc[0]["flagged"] == "No (justified)" else "UNEXPLAINED"
        got_note = match.iloc[0]["matched_note_id"]
        got_note = "" if pd.isna(got_note) else got_note

    ok = (got == expected and got_note == expected_note)
    correct += ok
    print(("OK       " if ok else "MISMATCH ") + f"{route:20s} {week}  expected {expected} {expected_note}  got {got} {got_note}")

    if expected == "JUSTIFIED":
        retrieval_total += 1
        found = [n["note_id"] for n in find_notes(collection, route, pd.Timestamp(week))]
        retrieval_hits += expected_note in found

print(f"\nCorrect: {correct}/{len(LABELS)}")
print(f"Vector search found the right note: {retrieval_hits}/{retrieval_total}")
