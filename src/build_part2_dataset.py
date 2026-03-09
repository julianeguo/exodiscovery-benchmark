"""
Build a 12-planet borderline exoplanet benchmark from NASA PSCompPars CSV.

Selection plan:
- 4 near flux thresholds:
    * 1 below 0.25 and 1 above/equal 0.25 within ±0.05
    * 1 below 1.10 and 1 above/equal 1.10 within ±0.05
- 4 near radius thresholds:
    * 1 below 0.50 and 1 above/equal 0.50 within ±0.05
    * 1 below 1.60 and 1 above/equal 1.60 within ±0.05
- 4 near mass thresholds:
    * 1 below 0.10 and 1 above/equal 0.10 within ±0.05
    * 1 below 3.00 and 1 above/equal 3.00 within ±0.05

Rules:
- Planets must be unique across all 12 selections.
- Ignore comment lines beginning with '#'.
- Ignore current habitable / non-habitable label.
- Allow a planet to qualify for multiple buckets, but once selected it cannot be reused.
- Fail loudly if any bucket cannot be filled.

Output CSV columns:
    anon_id
    pl_name
    pl_rade
    pl_bmasse
    pl_insol
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List, Set, Tuple

import pandas as pd


WINDOW = 0.05


def load_nasa_csv(path: Path) -> pd.DataFrame:
    """Load NASA PSCompPars CSV, skipping comment lines that start with '#'."""
    df = pd.read_csv(path, comment="#")

    required_cols = ["pl_name", "pl_rade", "pl_bmasse", "pl_insol"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Keep only rows with all three numeric values present
    df = df[required_cols].copy()
    df = df.dropna(subset=["pl_name", "pl_rade", "pl_bmasse", "pl_insol"])

    return df


def eligible_indices(
    df: pd.DataFrame,
    col: str,
    threshold: float,
    side: str,
    window: float,
    used_names: Set[str],
) -> List[int]:
    """
    Return eligible row indices for a threshold bucket.

    side:
        'below' -> threshold - window < value < threshold
        'above' -> threshold <= value < threshold + window
    """
    values = df[col]

    if side == "below":
        mask = (values > threshold - window) & (values < threshold)
    elif side == "above":
        mask = (values >= threshold) & (values < threshold + window)
    else:
        raise ValueError(f"Invalid side: {side}")

    mask &= ~df["pl_name"].isin(used_names)
    return df.index[mask].tolist()


def pick_one(
    df: pd.DataFrame,
    col: str,
    threshold: float,
    side: str,
    window: float,
    used_names: Set[str],
    rng: random.Random,
) -> Tuple[int, pd.Series]:
    """Randomly pick one unused planet from the eligible set."""
    candidates = eligible_indices(df, col, threshold, side, window, used_names)
    if not candidates:
        raise ValueError(
            f"No eligible planet found for bucket: "
            f"{col}, threshold={threshold}, side={side}, window={window}"
        )

    idx = rng.choice(candidates)
    row = df.loc[idx]
    return idx, row


def build_selection(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Construct the 12-planet borderline selection."""
    rng = random.Random(seed)
    used_names: Set[str] = set()
    selected_rows: List[dict] = []

    # (column, threshold, side)
    buckets = [
        ("pl_insol", 0.25, "below"),
        ("pl_insol", 0.25, "above"),
        ("pl_insol", 1.10, "below"),
        ("pl_insol", 1.10, "above"),
        ("pl_rade", 0.50, "below"),
        ("pl_rade", 0.50, "above"),
        ("pl_rade", 1.60, "below"),
        ("pl_rade", 1.60, "above"),
        ("pl_bmasse", 0.10, "below"),
        ("pl_bmasse", 0.10, "above"),
        ("pl_bmasse", 3.00, "below"),
        ("pl_bmasse", 3.00, "above"),
    ]

    def side_label(col: str, threshold: float, side: str) -> str:
        """Return whether this side is on the habitable or non-habitable side."""
        habitable_side_map = {
            ("pl_insol", 0.25): "above",
            ("pl_insol", 1.10): "below",
            ("pl_rade", 0.50): "above",
            ("pl_rade", 1.60): "below",
            ("pl_bmasse", 0.10): "above",
            ("pl_bmasse", 3.00): "below",
        }

        hab_side = habitable_side_map[(col, threshold)]
        return "1" if side == hab_side else "0"

    for col, threshold, side in buckets:
        _, row = pick_one(
            df=df,
            col=col,
            threshold=threshold,
            side=side,
            window=WINDOW,
            used_names=used_names,
            rng=rng,
        )

        used_names.add(row["pl_name"])

        selected_rows.append({
            "pl_name": row["pl_name"],
            "pl_rade": row["pl_rade"],
            "pl_bmasse": row["pl_bmasse"],
            "pl_insol": row["pl_insol"],
            "selected_threshold": f"{col}@{threshold:.2f}",
            "threshold_side": side_label(col, threshold, side),
        })

    out = pd.DataFrame(selected_rows).reset_index(drop=True)

    # Assign anonymized IDs
    out.insert(0, "anon_id", [f"B{i:02d}" for i in range(1, len(out) + 1)])

    return out[
        [
            "anon_id",
            "pl_name",
            "pl_rade",
            "pl_bmasse",
            "pl_insol",
            "selected_threshold",
            "threshold_side",
        ]
    ]

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample 12 unique borderline exoplanets from NASA PSCompPars."
    )
    parser.add_argument("input_csv", type=Path, help="Path to NASA PSCompPars CSV")
    parser.add_argument("output_csv", type=Path, help="Path to output CSV")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    args = parser.parse_args()

    df = load_nasa_csv(args.input_csv)
    selected = build_selection(df, seed=args.seed)
    selected.to_csv(args.output_csv, index=False)

    print(f"Wrote {len(selected)} planets to: {args.output_csv}")
    print(selected.to_string(index=False))


if __name__ == "__main__":
    main()