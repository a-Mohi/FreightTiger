import sys
from datetime import timedelta

import pandas as pd

from costs import add_comparisons, load_weekly_costs
from rag import build_note_database, find_notes

NO_EFFECT_PHRASES = ["not significantly", "no significant", "no major", "stable", "without a rate change",
                     "not part of", "returned to normal", "improved", "remained normal"]
RAISES_COST_PHRASES = ["surcharge", "higher", "pushing up", "rose"]


def check_note(note, week_start):
    """Return whether a note explains the cost rise."""
    text = note["text"].lower()
    week_end = week_start + timedelta(days=6)
    days_before_week = (week_start - note["date"]).days

    if any(p in text for p in NO_EFFECT_PHRASES):
        return False, "it says costs were not affected / conditions were normal"
    if not any(p in text for p in RAISES_COST_PHRASES):
        return False, "it does not describe anything that raises cost"
    if note["date"] > week_end:
        return False, "it is dated after this week"
    if days_before_week > 7:
        return False, "it is dated more than a week before this week"
    return True, "ok"


def run(shipments_csv="data/shipment_records.csv", notes_csv="data/context_notes.csv",
        out_csv="outputs/output.csv"):
    weekly = add_comparisons(load_weekly_costs(shipments_csv))
    collection = build_note_database(notes_csv)

    rows = []
    suspicious_weeks = weekly[weekly["suspicious"]].sort_values(["week_of", "route"])
    for _, w in suspicious_weeks.iterrows():
        retrieved = find_notes(collection, w["route"], w["week_of"])

        matched = None
        rejected = []
        for note in retrieved:
            ok, why = check_note(note, w["week_of"])
            if ok:
                matched = note
                break
            rejected.append((note, why))

        if matched is not None:
            flagged = "No (justified)"
            note_id = matched["note_id"]
            reason = (f"Matches note {matched['note_id']} dated {matched['date']:%Y-%m-%d}: "
                      f"\"{matched['text']}\" The cost rise has a clear explanation.")
        else:
            flagged = "Yes"
            note_id = ""
            closest = None
            if rejected:
                closest, why = min(rejected, key=lambda r: (abs((r[0]["date"] - w["week_of"]).days), r[0]["note_id"]))
                if abs((closest["date"] - w["week_of"]).days) > 90:
                    closest = None
            if closest is not None:
                reason = (f"The closest note ({closest['note_id']}, {closest['date']:%Y-%m-%d}) says: "
                          f"\"{closest['text']}\" It cannot explain this rise because {why}. "
                          f"No genuine justification found; flagged for review.")
            else:
                reason = ("No matching note found for this route or date range. "
                          "Cost rise looks unexplained and worth a human review.")

        rows.append({
            "route": w["route"],
            "week_of": f"{w['week_of']:%Y-%m-%d}",
            "cost_per_tonne_km": f"{w['cost_per_tonne_km']:.2f}",
            "vs_own_history": f"{w['vs_own_pct']:+.1f}% vs this route's past average",
            "vs_similar_routes": f"{w['vs_peer_pct']:+.1f}% vs similar-length routes this week",
            "flagged": flagged,
            "matched_note_id": note_id,
            "reason": reason,
        })

    output = pd.DataFrame(rows, columns=["route", "week_of", "cost_per_tonne_km", "vs_own_history",
                                         "vs_similar_routes", "flagged", "matched_note_id", "reason"])
    output.to_csv(out_csv, index=False)
    return output


if __name__ == "__main__":
    out = run()
    print(out[["route", "week_of", "vs_own_history", "flagged", "matched_note_id"]].to_string(index=False))
    print(f"\n{len(out)} suspicious weeks, {(out['flagged'] == 'Yes').sum()} unexplained. Saved outputs/output.csv")
