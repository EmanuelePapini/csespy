import argparse
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import csespy_dev as csespy


def find_suspect_orbits(df, min_lat_span=0.01, min_lon_span=0.01, min_unique_frac=0.01):
    stats = df.groupby("orbitn").agg(
        lat_min=("lat", "min"),
        lat_max=("lat", "max"),
        lon_min=("lon", "min"),
        lon_max=("lon", "max"),
        lat_unique=("lat", lambda s: s.nunique(dropna=True)),
        lon_unique=("lon", lambda s: s.nunique(dropna=True)),
        n=("lat", "size"),
    )
    stats["lat_span"] = stats["lat_max"] - stats["lat_min"]
    stats["lon_span"] = stats["lon_max"] - stats["lon_min"]
    stats["lon_span_circ"] = df.groupby("orbitn")["lon"].apply(_circular_span_deg)
    stats["lat_uniq_frac"] = stats["lat_unique"] / stats["n"]
    stats["lon_uniq_frac"] = stats["lon_unique"] / stats["n"]
    suspect = stats[
        (stats["lat_span"] < min_lat_span)
        | (stats["lon_span"] < min_lon_span)
            | (stats["lon_span_circ"] < min_lon_span)
        | (stats["lon_uniq_frac"] < min_unique_frac)
    ]
    return suspect.sort_values(
        ["lat_span", "lon_span", "lat_uniq_frac", "lon_uniq_frac"]
    )


def _circular_span_deg(lon_values):
    """Compute minimal circular span in degrees for longitudes (wrap-aware)."""
    lon = np.asarray(lon_values, dtype=float)
    if lon.size == 0:
        return np.nan
    lon = np.mod(lon, 360.0)
    lon = np.sort(lon)
    gaps = np.diff(np.concatenate([lon, lon[:1] + 360.0]))
    max_gap = np.nanmax(gaps) if gaps.size else 0.0
    return 360.0 - max_gap


def _max_flat_run(values):
    """Return longest run of equal consecutive values."""
    if len(values) == 0:
        return 0
    max_run = run = 1
    prev = values[0]
    for v in values[1:]:
        if v == prev:
            run += 1
            if run > max_run:
                max_run = run
        else:
            run = 1
            prev = v
    return max_run


def orbit_diagnostics(
    df,
    round_decimals=3,
    max_const_frac=0.9,
    max_flat_run_frac=0.5,
    flat_round_decimals=3,
):
    def _stats(g):
        lat = g["lat"]
        lon = g["lon"]
        n = len(g)
        t_unique = g.index.nunique()
        lat_std = float(lat.std(skipna=True))
        lon_std = float(lon.std(skipna=True))
        lat_step = float(np.nanmedian(np.abs(np.diff(lat.values)))) if n > 1 else 0.0
        lon_step = float(np.nanmedian(np.abs(np.diff(lon.values)))) if n > 1 else 0.0
        lat_round = lat.round(round_decimals)
        lon_round = lon.round(round_decimals)
        lat_round_unique = lat_round.nunique(dropna=True)
        lon_round_unique = lon_round.nunique(dropna=True)

        lat_eq_frac = float(np.nanmean(np.diff(lat.values) == 0)) if n > 1 else 1.0
        lon_eq_frac = float(np.nanmean(np.diff(lon.values) == 0)) if n > 1 else 1.0

        lat_flat_vals = lat.round(flat_round_decimals).to_numpy()
        lon_flat_vals = lon.round(flat_round_decimals).to_numpy()
        lat_flat_run = _max_flat_run(lat_flat_vals)
        lon_flat_run = _max_flat_run(lon_flat_vals)
        lat_flat_run_frac = lat_flat_run / n if n else 0
        lon_flat_run_frac = lon_flat_run / n if n else 0
        lon_span_circ = _circular_span_deg(lon.values)
        return pd.Series(
            {
                "n": n,
                "t_unique": t_unique,
                "t_dup_frac": 1 - (t_unique / n if n else 1),
                "lat_std": lat_std,
                "lon_std": lon_std,
                "lat_step_med": lat_step,
                "lon_step_med": lon_step,
                "lat_round_unique": lat_round_unique,
                "lon_round_unique": lon_round_unique,
                "lat_round_frac": lat_round_unique / n if n else 0,
                "lon_round_frac": lon_round_unique / n if n else 0,
                "lat_eq_frac": lat_eq_frac,
                "lon_eq_frac": lon_eq_frac,
                "lat_flat_run": lat_flat_run,
                "lon_flat_run": lon_flat_run,
                "lat_flat_run_frac": lat_flat_run_frac,
                "lon_flat_run_frac": lon_flat_run_frac,
                "lon_span_circ": lon_span_circ,
            }
        )

    stats = df.groupby("orbitn", sort=False).apply(_stats, include_groups=False)
    stats["score"] = (
        (stats["t_dup_frac"] > 0.01).astype(int)
        + (stats["lat_std"] < 1e-4).astype(int)
        + (stats["lon_std"] < 1e-4).astype(int)
        + (stats["lat_step_med"] < 1e-5).astype(int)
        + (stats["lon_step_med"] < 1e-5).astype(int)
        + (stats["lat_round_frac"] < 0.01).astype(int)
        + (stats["lon_round_frac"] < 0.01).astype(int)
        + (stats["lat_eq_frac"] > max_const_frac).astype(int)
        + (stats["lon_eq_frac"] > max_const_frac).astype(int)
        + (stats["lat_flat_run_frac"] > max_flat_run_frac).astype(int)
        + (stats["lon_flat_run_frac"] > max_flat_run_frac).astype(int)
    )
    return stats.sort_values(
        ["score", "lat_std", "lon_std", "lat_step_med", "lon_step_med"],
        ascending=True,
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Diagnose CSES orbit DB anomalies")
    parser.add_argument(
        "--odbfile",
        default="./CSES01_orbitdb.h5",
        help="Path to orbit DB HDF5 file",
    )
    parser.add_argument("--t0", default=None, help="Start time ISO (UTC)")
    parser.add_argument("--t1", default=None, help="End time ISO (UTC)")
    parser.add_argument(
        "--min-lat-span", type=float, default=0.01, help="Minimum latitude span"
    )
    parser.add_argument(
        "--min-lon-span", type=float, default=0.01, help="Minimum longitude span"
    )
    parser.add_argument(
        "--min-unique-frac",
        type=float,
        default=0.01,
        help="Minimum unique fraction",
    )
    parser.add_argument(
        "--round-decimals",
        type=int,
        default=3,
        help="Decimals for rounding checks",
    )
    parser.add_argument(
        "--flat-round-decimals",
        type=int,
        default=3,
        help="Decimals for flat-run checks",
    )
    parser.add_argument(
        "--max-const-frac",
        type=float,
        default=0.9,
        help="Max fraction of consecutive equal values before flagging",
    )
    parser.add_argument(
        "--max-flat-run-frac",
        type=float,
        default=0.5,
        help="Max fraction in longest constant run before flagging",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="How many suspect orbits to print",
    )
    parser.add_argument(
        "--print-rows",
        action="store_true",
        help="Print sample rows for selected orbits",
    )
    parser.add_argument(
        "--rows-per-orbit",
        type=int,
        default=5,
        help="How many rows to print per orbit",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    odb = csespy.CSES_database(dbbuf=args.odbfile)
    db = odb.db

    if args.t0 and args.t1:
        t0 = datetime.fromisoformat(args.t0).replace(tzinfo=timezone.utc)
        t1 = datetime.fromisoformat(args.t1).replace(tzinfo=timezone.utc)
        mask = (db.index >= t0) & (db.index <= t1)
        db = db.loc[mask]

    print(f"DB time range: {db.index.min()} -> {db.index.max()}")
    print(f"DB rows: {len(db):,} | orbits: {db['orbitn'].nunique():,}")

    suspect = find_suspect_orbits(
        db,
        min_lat_span=args.min_lat_span,
        min_lon_span=args.min_lon_span,
        min_unique_frac=args.min_unique_frac,
    )
    print(f"Suspect orbits (basic): {len(suspect)}")
    if len(suspect):
        print(suspect.head(args.top))

    diag = orbit_diagnostics(
        db,
        round_decimals=args.round_decimals,
        max_const_frac=args.max_const_frac,
        max_flat_run_frac=args.max_flat_run_frac,
        flat_round_decimals=args.flat_round_decimals,
    )
    sus_diag = diag[diag["score"] > 0].sort_values("score", ascending=False)
    print(f"Diagnostic suspects: {len(sus_diag)}")
    if len(sus_diag):
        print(sus_diag.head(args.top))
        if args.print_rows:
            for orbitn in sus_diag.head(3).index:
                print(f"\n[Sample] orbitn={orbitn}")
                print(db[db["orbitn"] == orbitn].head(args.rows_per_orbit))

    # Always show most constant candidates even if no hard flags
    print("\nMost constant candidates (by smallest spans):")
    span_stats = diag.copy()
    span_stats["lat_span"] = db.groupby("orbitn")["lat"].max() - db.groupby("orbitn")["lat"].min()
    span_stats["lon_span"] = db.groupby("orbitn")["lon"].max() - db.groupby("orbitn")["lon"].min()
    if "lon_span_circ" not in span_stats.columns:
        span_stats["lon_span_circ"] = db.groupby("orbitn")["lon"].apply(_circular_span_deg)
    if "lon_span_circ" in span_stats.columns:
        top_constant = span_stats.sort_values(["lat_span", "lon_span_circ"]).head(args.top)
    else:
        top_constant = span_stats.sort_values(["lat_span", "lon_span"]).head(args.top)
    cols = [c for c in ["n", "t_unique", "t_dup_frac", "score", "lat_span", "lon_span", "lon_span_circ"] if c in top_constant.columns]
    print(top_constant[cols].to_string())
    if args.print_rows:
        for orbitn in top_constant.index[:3]:
            print(f"\n[Constant sample] orbitn={orbitn}")
            print(db[db["orbitn"] == orbitn].head(args.rows_per_orbit))


if __name__ == "__main__":
    main()
