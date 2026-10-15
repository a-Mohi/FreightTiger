from datetime import timedelta

import pandas as pd


def load_weekly_costs(shipments_csv):
    df = pd.read_csv(shipments_csv)
    df["shipment_date"] = pd.to_datetime(df["shipment_date"])

    df["route"] = df["origin"] + "-" + df["destination"]

    df["week_of"] = df["shipment_date"].apply(lambda d: d - timedelta(days=d.weekday()))

    df["tonne_km"] = df["quantity_tonnes"] * df["distance_km"]

    weekly = df.groupby(["route", "route_type", "week_of"]).agg(
        total_cost=("freight_cost_inr", "sum"),
        total_tonne_km=("tonne_km", "sum"),
    ).reset_index()
    weekly["cost_per_tonne_km"] = weekly["total_cost"] / weekly["total_tonne_km"]
    return weekly.sort_values(["route", "week_of"]).reset_index(drop=True)


def add_comparisons(weekly):
    """Add comparison percentages and the suspicious flag."""
    own_pct = []
    peer_pct = []

    for i in range(len(weekly)):
        row = weekly.iloc[i]

        same_route = weekly[weekly["route"] == row["route"]]
        earlier = same_route[same_route["week_of"] < row["week_of"]]
        last_8 = earlier.tail(8)
        if len(last_8) == 0:
            own_pct.append(None)
        else:
            own_avg = last_8["cost_per_tonne_km"].mean()
            own_pct.append((row["cost_per_tonne_km"] / own_avg - 1) * 100)

        others = weekly[(weekly["route_type"] == row["route_type"])
                        & (weekly["week_of"] == row["week_of"])
                        & (weekly["route"] != row["route"])]
        if len(others) == 0:
            peer_pct.append(None)
        else:
            peer_avg = others["cost_per_tonne_km"].mean()
            peer_pct.append((row["cost_per_tonne_km"] / peer_avg - 1) * 100)

    weekly["vs_own_pct"] = own_pct
    weekly["vs_peer_pct"] = peer_pct

    suspicious = []
    for own, peer in zip(weekly["vs_own_pct"], weekly["vs_peer_pct"]):
        if own is None or pd.isna(own):
            suspicious.append(False)
        elif own >= 10:
            suspicious.append(True)
        elif own >= 5 and peer is not None and not pd.isna(peer) and peer >= 15:
            suspicious.append(True)
        else:
            suspicious.append(False)
    weekly["suspicious"] = suspicious
    return weekly
