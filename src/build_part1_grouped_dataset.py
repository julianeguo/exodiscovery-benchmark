
#!/usr/bin/env python3
"""
Build a grouped Part 1 exoplanet benchmark dataset.

Workflow:
1. Read HWC conservative CSV.
2. Randomly sample 20 planets from HWC.
3. Read NASA PSCompPars CSV (ignoring comment lines starting with '#').
4. Locate the sampled HWC planet names in NASA by exact name match.
5. Sample 40 negative planets from NASA whose names are not among the sampled 20.
6. Combine, shuffle, assign group IDs and anonymized IDs, and write one final CSV.

Final CSV columns:
    group_id
    anon_id
    pl_name
    pl_rade
    pl_bmasse
    pl_insol
    label_habitable
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Set

import pandas as pd

HWC_NAME_COL = "Name"
NASA_NAME_COL = "pl_name"
NASA_KEEP_COLS = ["pl_name", "pl_rade", "pl_bmasse", "pl_insol"]
FINAL_COLS = ["group_id", "anon_id", "pl_name", "pl_rade", "pl_bmasse", "pl_insol", "label_habitable"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build grouped exoplanet benchmark dataset.")
    parser.add_argument("--hwc", type=Path, default=Path("data/hwc_table_conservative.csv"))
    parser.add_argument("--nasa", type=Path, default=Path("data/PSCompPars.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/part1_grouped_dataset.csv"))
    parser.add_argument("--num_positive", type=int, default=20)
    parser.add_argument("--num_negative", type=int, default=40)
    parser.add_argument("--group_size", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def load_hwc_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"HWC CSV not found: {path}")
    df = pd.read_csv(path, comment="#")
    if HWC_NAME_COL not in df.columns:
        raise ValueError(
            f"HWC CSV must contain column '{HWC_NAME_COL}'. Available columns: {list(df.columns)}"
        )
    df = df[[HWC_NAME_COL]].copy()
    df[HWC_NAME_COL] = df[HWC_NAME_COL].astype(str).str.strip()
    df = df[df[HWC_NAME_COL] != ""].drop_duplicates(subset=[HWC_NAME_COL]).reset_index(drop=True)
    return df


def load_nasa_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"NASA CSV not found: {path}")
    df = pd.read_csv(path, comment="#")
    missing = [col for col in NASA_KEEP_COLS if col not in df.columns]
    if missing:
        raise ValueError(
            f"NASA CSV is missing required columns: {missing}. Available columns: {list(df.columns)}"
        )
    df = df[NASA_KEEP_COLS].copy()
    df[NASA_NAME_COL] = df[NASA_NAME_COL].astype(str).str.strip()
    df = df[df[NASA_NAME_COL] != ""].reset_index(drop=True)
    return df


def sample_hwc_positives(hwc_df: pd.DataFrame, nasa_df: pd.DataFrame, num_positive: int, seed: int) -> pd.DataFrame:
    nasa_name_set: Set[str] = set(nasa_df[NASA_NAME_COL].tolist())

    hwc_valid = hwc_df[hwc_df[HWC_NAME_COL].isin(nasa_name_set)].copy()
    hwc_missing = hwc_df[~hwc_df[HWC_NAME_COL].isin(nasa_name_set)].copy()

    if len(hwc_valid) < num_positive:
        raise ValueError(
            f"Requested {num_positive} HWC planets, but only {len(hwc_valid)} exist exactly in NASA PSCompPars.\n"
            f"Missing HWC names include:\n" + "\n".join(hwc_missing[HWC_NAME_COL].tolist())
        )

    if not hwc_missing.empty:
        print("Warning: the following HWC planets were not found exactly in NASA and were excluded:")
        for name in sorted(hwc_missing[HWC_NAME_COL].tolist()):
            print(f"  - {name}")

    return hwc_valid.sample(n=num_positive, random_state=seed).reset_index(drop=True)


def lookup_positives_in_nasa(sampled_hwc_df: pd.DataFrame, nasa_df: pd.DataFrame) -> pd.DataFrame:
    sampled_names: List[str] = sampled_hwc_df[HWC_NAME_COL].tolist()
    sampled_name_set: Set[str] = set(sampled_names)

    positives = nasa_df[nasa_df[NASA_NAME_COL].isin(sampled_name_set)].copy()
    missing_names = sorted(sampled_name_set - set(positives[NASA_NAME_COL].tolist()))
    if missing_names:
        raise ValueError(
            "Some sampled HWC planet names were not found exactly in NASA PSCompPars:\n"
            + "\n".join(missing_names)
        )

    name_to_order = {name: idx for idx, name in enumerate(sampled_names)}
    positives["_sample_order"] = positives[NASA_NAME_COL].map(name_to_order)
    positives = positives.sort_values("_sample_order").drop(columns=["_sample_order"]).reset_index(drop=True)

    dupes = positives[positives.duplicated(subset=[NASA_NAME_COL], keep=False)]
    if not dupes.empty:
        dup_names = sorted(dupes[NASA_NAME_COL].unique().tolist())
        raise ValueError(
            "NASA PSCompPars contains duplicate rows for sampled positive planet name(s):\n"
            + "\n".join(dup_names)
        )

    positives["label_habitable"] = 1
    return positives


def sample_nasa_negatives(nasa_df: pd.DataFrame, positive_names: Set[str], num_negative: int, seed: int) -> pd.DataFrame:
    negative_pool = nasa_df[~nasa_df[NASA_NAME_COL].isin(positive_names)].copy()
    negative_pool = negative_pool.drop_duplicates(subset=[NASA_NAME_COL]).reset_index(drop=True)
    if len(negative_pool) < num_negative:
        raise ValueError(
            f"Requested {num_negative} negative planets, but only {len(negative_pool)} are available."
        )
    negatives = negative_pool.sample(n=num_negative, random_state=seed).reset_index(drop=True)
    negatives["label_habitable"] = 0
    return negatives


def assign_groups_and_ids(df: pd.DataFrame, group_size: int) -> pd.DataFrame:
    total = len(df)
    if total % group_size != 0:
        raise ValueError(f"Total number of planets ({total}) is not divisible by group size ({group_size}).")
    df = df.reset_index(drop=True).copy()
    group_ids = []
    anon_ids = []
    for idx in range(total):
        group_num = idx // group_size + 1
        pos_in_group = idx % group_size + 1
        group_ids.append(group_num)
        anon_ids.append(f"G{group_num:02d}_P{pos_in_group}")
    df["group_id"] = group_ids
    df["anon_id"] = anon_ids
    return df


def build_dataset(args: argparse.Namespace) -> pd.DataFrame:
    hwc_df = load_hwc_csv(args.hwc)
    nasa_df = load_nasa_csv(args.nasa)

    sampled_hwc = sample_hwc_positives(hwc_df, nasa_df, args.num_positive, args.seed)
    positives = lookup_positives_in_nasa(sampled_hwc, nasa_df)

    positive_names = set(positives[NASA_NAME_COL].tolist())
    negatives = sample_nasa_negatives(nasa_df, positive_names, args.num_negative, args.seed)

    combined = pd.concat([positives, negatives], ignore_index=True)
    combined = combined.sample(frac=1.0, random_state=args.seed).reset_index(drop=True)
    combined = assign_groups_and_ids(combined, args.group_size)

    return combined[FINAL_COLS].copy()


def print_summary(df: pd.DataFrame) -> None:
    num_positive = int(df["label_habitable"].sum())
    num_negative = int((df["label_habitable"] == 0).sum())
    num_groups = int(df["group_id"].nunique())

    print("Dataset build complete.")
    print(f"  Total planets:   {len(df)}")
    print(f"  Positives:       {num_positive}")
    print(f"  Negatives:       {num_negative}")
    print(f"  Groups:          {num_groups}")
    print(f"  Group size:      {len(df) // num_groups if num_groups else 0}")


def main() -> None:
    args = parse_args()
    final_df = build_dataset(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(args.out, index=False)
    print_summary(final_df)
    print(f"  Output written:  {args.out}")


if __name__ == "__main__":
    main()
