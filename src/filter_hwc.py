# this file filters out the conservative habitable planets (29 planets) from the HWC .csv file
# which contains ~70 planets in total.

import csv
import re
import sys
from typing import Optional

MASS_COL = "Mass<br>(M<sub>E</sub>)"
RADIUS_COL = "Radius<br>(R<sub>E</sub>)"

# Criteria bounds: strict lower, inclusive upper
R_MIN, R_MAX = 0.5, 1.6
M_MIN, M_MAX = 0.1, 3.0

def is_conservative(mass, radius):
    if (mass > M_MIN and mass <= M_MAX) or radius > R_MIN and radius <= R_MAX:
        return True
    else:
        return False
    
def main():
    if len(sys.argv) != 3:
        print("Usage: python filter_conservative.py input.csv output_conservative.csv", file=sys.stderr)
        return 2
    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise RuntimeError("No header row found.")

        # Validate required columns
        missing = [c for c in (MASS_COL, RADIUS_COL) if c not in reader.fieldnames]
        if missing:
            raise KeyError(
                f"Missing required column(s): {missing}\n"
                f"Found columns: {reader.fieldnames}"
            )

        kept_rows = []
        for row in reader:
            radius = row.get(RADIUS_COL, "")
            mass = row.get(MASS_COL, "")
            if is_conservative(float(mass), float(radius)):
                kept_rows.append(row)
        
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)

    print(f"Input rows: {sum(1 for _ in open(in_path, 'r', encoding='utf-8-sig')) - 1}")
    print(f"Kept rows:  {len(kept_rows)}")
    print(f"Wrote:      {out_path}")
    return 0


if __name__ == "__main__":
    main()
