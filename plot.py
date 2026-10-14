"""First look at the racial household income gap, 2002-2025.

Reads data/household_income_by_race.csv (written by get_data.py) and saves
two figures, one for median and one for mean household income:
  figures/income_gap_by_race.png       (median)
  figures/income_gap_by_race_mean.png  (mean)
Each has two panels:
  left:  real household income by group
  right: each group's income as a ratio of the reference group's

Styled after The Economist's charts: red rule and tag at the top, bold
left-aligned title with a plain subtitle, horizontal gridlines only, y-axis
labels on the right and a solid baseline.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parent
DATA_PATH = ROOT / "data" / "household_income_by_race.csv"
FIG_DIR = ROOT / "figures"

# Per-statistic settings: CSV column, wording, left-panel y-axis, output file.
STATS = {
    "median": {
        "column": "median_real",
        "noun": "median",
        "yticks": range(0, 141, 20),
        "file": "income_gap_by_race.png",
        "note": "",
    },
    "mean": {
        "column": "mean_real",
        "noun": "mean",
        "yticks": range(0, 181, 30),
        "file": "income_gap_by_race_mean.png",
        "note": "Means are pulled up by the highest incomes, so they are more "
                "sensitive than medians to how Census caps (top-codes) very "
                "large incomes.\n",
    },
}

# Non-Hispanic White is the reference because "White Alone" includes most
# Hispanic householders, which would blur the Hispanic comparison.
REFERENCE = "White Alone, Not Hispanic"

# Fixed color per group, so a group keeps its color in both panels.
GROUPS = {
    "White Alone, Not Hispanic": ("White, non-Hispanic", "#006BA2"),
    "Black Alone": ("Black", "#DB444B"),
    "Hispanic (any race)": ("Hispanic", "#3EBCD2"),
    "Asian Alone": ("Asian", "#EBB434"),
}

# Lowest line in every panel; its end label goes below the line so it does
# not collide with the line just above it.
LOWEST = "Black Alone"

# Census method changes inside the window (footnotes 39 and 40 of H-5).
METHOD_BREAKS = {2013: "question\nredesign", 2017: "new\nprocessing"}

ACCENT_RED = "#E3120B"
INK = "#0C0C0C"
INK_SECONDARY = "#3F5661"
INK_MUTED = "#758D99"
GRID = "#B7C6CF"
SURFACE = "#FFFFFF"

plt.rcParams["font.family"] = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]


def style_axis(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(INK)
    ax.spines["bottom"].set_linewidth(1.2)
    ax.yaxis.tick_right()
    ax.tick_params(axis="y", length=0, pad=4, labelsize=10, colors=INK)
    ax.tick_params(axis="x", length=4, color=INK, labelsize=10, colors=INK)
    for year in METHOD_BREAKS:
        ax.axvline(year, color=INK_MUTED, linewidth=0.8, linestyle=(0, (2, 3)))


def panel_title(ax, title, subtitle) -> None:
    ax.text(0, 1.13, title, transform=ax.transAxes, fontsize=12,
            fontweight="bold", color=INK, va="bottom")
    ax.text(0, 1.05, subtitle, transform=ax.transAxes, fontsize=10,
            color=INK, va="bottom")


def label_line_end(ax, x, y, text, below=False) -> None:
    ax.annotate(
        text, (x, y), xytext=(-2, -7 if below else 7), textcoords="offset points",
        ha="right", va="top" if below else "bottom",
        fontsize=9.5, fontweight="bold", color=INK,
    )


def draw(df: pd.DataFrame, stat: dict) -> Path:
    real_year = int(df["real_dollar_year"].iloc[0])
    noun = stat["noun"]
    wide = df.pivot(index="year", columns="group", values=stat["column"])
    ratio = wide.div(wide[REFERENCE], axis=0)
    first, last = wide.index.min(), wide.index.max()

    fig, (ax_level, ax_ratio) = plt.subplots(
        1, 2, figsize=(13, 6.6), facecolor=SURFACE,
        gridspec_kw={"wspace": 0.22},
    )

    for group, (name, color) in GROUPS.items():
        ax_level.plot(wide.index, wide[group] / 1000, color=color,
                      linewidth=2.4, label=name, solid_capstyle="round")
        label_line_end(ax_level, last, wide.loc[last, group] / 1000,
                       f"{wide.loc[last, group] / 1000:.0f}",
                       below=group == LOWEST)

    for group, (name, color) in GROUPS.items():
        if group == REFERENCE:
            continue
        ax_ratio.plot(ratio.index, ratio[group], color=color,
                      linewidth=2.4, solid_capstyle="round")
        label_line_end(ax_ratio, last, ratio.loc[last, group],
                       f"{ratio.loc[first, group]:.2f} → "
                       f"{ratio.loc[last, group]:.2f}",
                       below=group == LOWEST)
    ax_ratio.axhline(1.0, color=INK, linewidth=1.2)
    ax_ratio.annotate("Parity with White, non-Hispanic", (first, 1.0),
                      xytext=(2, 5), textcoords="offset points",
                      fontsize=9, color=INK_SECONDARY)

    style_axis(ax_level)
    style_axis(ax_ratio)
    ax_level.set_ylim(0, max(stat["yticks"]))
    ax_level.set_yticks(stat["yticks"])
    ax_ratio.set_ylim(0.4, 1.6)
    ax_ratio.set_yticks([0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6])
    for ax in (ax_level, ax_ratio):
        ax.set_xlim(first - 0.5, last + 0.5)
        ax.set_xticks(range(2002, last + 1, 4))
    for year, label in METHOD_BREAKS.items():
        ax_level.annotate(label, (year, 1), xycoords=("data", "axes fraction"),
                          xytext=(-3, -2), textcoords="offset points",
                          fontsize=8, color=INK_MUTED, ha="right", va="top")

    panel_title(ax_level, f"{noun.capitalize()} household income",
                f"$'000, {real_year} prices")
    panel_title(ax_ratio, "Relative to White, non-Hispanic households",
                f"Ratio of {noun}s")

    # Red rule across the top and the small red tag at the left.
    fig.add_artist(Rectangle((0, 0.995), 1, 0.005, transform=fig.transFigure,
                             color=ACCENT_RED, linewidth=0))
    fig.add_artist(Rectangle((0.04, 0.955), 0.035, 0.016, transform=fig.transFigure,
                             color=ACCENT_RED, linewidth=0))
    fig.text(0.04, 0.905, "Uneven progress", fontsize=19, fontweight="bold",
             color=INK, va="bottom")
    fig.text(0.04, 0.868,
             f"United States, household income by race and Hispanic origin "
             f"of householder, {first}–{last}",
             fontsize=12, color=INK, va="bottom")
    fig.legend(*ax_level.get_legend_handles_labels(), loc="upper left",
               bbox_to_anchor=(0.035, 0.86), ncol=4, frameon=False,
               fontsize=10, handlelength=1.6, columnspacing=1.6)

    fig.text(
        0.04, 0.015,
        "Source: U.S. Census Bureau, CPS ASEC, Historical Income Table H-5. "
        "Race groups are single-race (\"alone\"); Hispanic may be of any race.\n"
        f"Inflation-adjusted: every year's income is converted to {real_year} "
        "dollars with the Chained Consumer Price Index (C-CPI-U), so years "
        "compare in real purchasing power.\n"
        f"{stat['note']}"
        "Dotted lines mark Census method changes, each reported twice in H-5; "
        "the newer-method estimate is shown.\n"
        "2013: the 2014 survey tested redesigned income questions on part of "
        "the sample (about 30,000 of 98,000 addresses); the estimate from that "
        "redesigned-question subsample is used.\n"
        "2017: estimates come from Census's updated data processing system, "
        "which Census recommends for comparisons with 2018 and later.",
        fontsize=8, color=INK_SECONDARY, va="bottom", linespacing=1.5,
    )
    fig.subplots_adjust(left=0.04, right=0.95, top=0.70, bottom=0.25)

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    path = FIG_DIR / stat["file"]
    fig.savefig(path, dpi=200, facecolor=SURFACE)
    plt.close(fig)
    return path


def main() -> None:
    df = pd.read_csv(DATA_PATH)
    for stat in STATS.values():
        path = draw(df, stat)
        print(f"Saved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
