"""Download Census Historical Income Table H-5 and write a tidy CSV.

Table H-5: Median and Mean Household Income by Race and Hispanic Origin of
Householder (CPS ASEC). FRED only carries the all-races total
(MEHOINUSA672N), so the race breakdown comes from Census directly.

Output: data/household_income_by_race.csv, one row per group and year,
2002 onward. 2002 is the first year of the single-race ("alone")
categories, and all years from 2000 on are deflated with the same index
(C-CPI-U), so the 2002+ series need no splicing.
"""

import re
from pathlib import Path

import pandas as pd
import requests

URL = (
    "https://www2.census.gov/programs-surveys/cps/tables/time-series/"
    "historical-income-households/h05.xlsx"
)
FIRST_YEAR = 2002

ROOT = Path(__file__).resolve().parent
RAW_PATH = ROOT / "data" / "raw" / "h05.xlsx"
OUT_PATH = ROOT / "data" / "household_income_by_race.csv"

# Column order within each block of the sheet.
COLUMNS = [
    "households_thousands",
    "median_current",
    "median_real",
    "mean_current",
    "mean_real",
]


def download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)


def parse_h5(path: Path) -> tuple[pd.DataFrame, str]:
    """Split the single-sheet table into its race blocks.

    The sheet stacks one block per group: a title row (e.g. "Black Alone (33)"),
    two header rows, then one row per year in descending order. Year labels can
    carry footnote markers, e.g. "2013 (39)".
    """
    sheet = pd.read_excel(path, header=None)
    # Row 6 states the dollar base, e.g. "... 2025 C-CPI-U ... adjusted dollars".
    dollar_note = str(sheet.iloc[5, 0])

    records = []
    group = None
    for _, row in sheet.iterrows():
        label = str(row[0]).strip()
        year_match = re.match(r"^(\d{4})\s*(.*)$", label)
        if year_match and group is not None:
            values = pd.to_numeric(row[1:6], errors="coerce").tolist()
            records.append(
                {
                    "group": group,
                    "year": int(year_match.group(1)),
                    "footnotes": year_match.group(2).strip(),
                    **dict(zip(COLUMNS, values)),
                }
            )
        elif row[1:].isna().all() and label != "nan":
            # A row with text only in column A starts a new block.
            group = re.sub(r"\s*\(\d+\)$", "", label)
    return pd.DataFrame(records), dollar_note


def main() -> None:
    download(URL, RAW_PATH)
    df, dollar_note = parse_h5(RAW_PATH)

    df = df[df["year"] >= FIRST_YEAR]

    # 2013 and 2017 appear twice per group because of method changes
    # (2013: redesigned income questions, footnotes 38/39; 2017: updated
    # processing system, footnote 40). Census lists the newer-method row
    # first, so keep the first occurrence.
    dropped = df[df.duplicated(["group", "year"], keep="first")]
    df = df.drop(dropped.index)

    df = df.sort_values(["group", "year"]).reset_index(drop=True)
    real_year = re.search(r"(\d{4}) C-CPI-U", dollar_note)
    df["real_dollar_year"] = int(real_year.group(1)) if real_year else pd.NA

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)

    print(f"Dollar base: {dollar_note}")
    print(f"Dropped older-method duplicates: "
          f"{sorted(set(zip(dropped['year'], dropped['footnotes'])))}")
    print(f"Wrote {len(df)} rows, {df['year'].min()}-{df['year'].max()}, "
          f"to {OUT_PATH.relative_to(ROOT)}")
    print(df.groupby("group")["year"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
