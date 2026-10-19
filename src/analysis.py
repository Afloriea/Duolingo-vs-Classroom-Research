"""Survey analysis: rebuilds every chart in figures/ and prints the headline numbers.

Run from the repo root:
    python src/analysis.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "survey_responses.csv"
FIGURES = ROOT / "figures"

HIGHLIGHT = "#2a9d8f"
MUTED = "#c9d1d3"
INK = "#1f2a30"
INK_SOFT = "#5b6b73"

FACTORS = {
    "f_cost": "Cost",
    "f_flexibility": "Flexibility",
    "f_time": "Time",
    "f_prestige": "Prestige",
    "f_convenience": "Convenience",
    "f_entertainment": "Entertainment",
}
FOCUS = ["Designated Course", "Duolingo"]

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.edgecolor": MUTED,
    "axes.labelcolor": INK_SOFT,
    "axes.titlecolor": INK,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.titlelocation": "left",
    "xtick.color": INK_SOFT,
    "ytick.color": INK_SOFT,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})


def load() -> pd.DataFrame:
    return pd.read_csv(DATA)


def explode_multiselect(df: pd.DataFrame, main: str, other: str) -> pd.DataFrame:
    """One row per (respondent, method). Merges the 'Other:' free-text column into the picklist."""
    parts = []
    for col in (main, other):
        s = df.set_index("respondent_id")[col].dropna().str.split(",").explode().str.strip()
        parts.append(s)
    out = pd.concat(parts)
    out = out[(out != "") & (out != "Other:")]
    return out.rename("method").reset_index().drop_duplicates()


def save(fig, name: str) -> None:
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def label_bars(ax, bars, fmt="{:.0f}") -> None:
    for b in bars:
        ax.text(b.get_width() + 0.3, b.get_y() + b.get_height() / 2, fmt.format(b.get_width()),
                va="center", color=INK, fontsize=10)


def plot_most_effective(df: pd.DataFrame) -> pd.Series:
    eff = explode_multiselect(df, "most_effective", "most_effective_other")
    counts = eff["method"].value_counts()
    counts = counts[counts >= 2].sort_values()
    fig, ax = plt.subplots(figsize=(9, 5.2))
    colors = [HIGHLIGHT if m in FOCUS else MUTED for m in counts.index]
    bars = ax.barh(counts.index, counts.values, color=colors, height=0.62)
    label_bars(ax, bars)
    ax.set_title("Which method do learners find most effective?")
    ax.set_xlabel("Respondents naming the method (multi-select, n = 57)")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.grid(True, color="#eef1f2")
    ax.set_axisbelow(True)
    save(fig, "most_effective_methods.png")
    return counts


def plot_usage_vs_effectiveness(df: pd.DataFrame) -> pd.DataFrame:
    """For each method: share of respondents who use it vs. share who call it most effective."""
    n = len(df)
    used = explode_multiselect(df, "learning_method", "learning_method_other")["method"].value_counts()
    eff = explode_multiselect(df, "most_effective", "most_effective_other")["method"].value_counts()
    methods = ["Self-Study", "Duolingo", "Designated Course", "Tutor", "Study Abroad"]
    table = pd.DataFrame({
        "use_it": used.reindex(methods).fillna(0) / n * 100,
        "most_effective": eff.reindex(methods).fillna(0) / n * 100,
    })

    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = range(len(methods))
    for i, m in enumerate(methods):
        a, b = table.loc[m, "use_it"], table.loc[m, "most_effective"]
        color = HIGHLIGHT if m in FOCUS else INK_SOFT
        ax.plot([a, b], [i, i], color=MUTED, linewidth=2, zorder=1)
        ax.scatter(a, i, s=70, color="white", edgecolor=color, linewidth=2, zorder=2)
        ax.scatter(b, i, s=70, color=color, zorder=3)
        ax.text(a + (1.5 if a >= b else -1.5), i, f"{a:.0f}%", va="center",
                ha="left" if a >= b else "right", fontsize=9, color=INK_SOFT)
        ax.text(b + (-1.5 if a >= b else 1.5), i, f"{b:.0f}%", va="center",
                ha="right" if a >= b else "left", fontsize=9, color=INK)
    ax.set_yticks(list(y), methods)
    ax.invert_yaxis()
    ax.set_xlim(0, 75)
    ax.set_xlabel("% of respondents (n = 57)")
    ax.set_title("Usage vs. perceived effectiveness")
    ax.scatter([], [], s=60, color="white", edgecolor=INK_SOFT, linewidth=2, label="Uses the method")
    ax.scatter([], [], s=60, color=INK_SOFT, label="Names it most effective")
    ax.legend(loc="lower right", frameon=False)
    ax.xaxis.grid(True, color="#eef1f2")
    ax.set_axisbelow(True)
    save(fig, "usage_vs_effectiveness.png")
    return table.round(1)


def plot_priorities(df: pd.DataFrame) -> pd.DataFrame:
    """Respondents ranked six factors 1 (most important) to 6. Summarised as the share ranking each top-2."""
    summary = pd.DataFrame({
        "top2_share": {lbl: (df[col] <= 2).mean() * 100 for col, lbl in FACTORS.items()},
        "mean_rank": {lbl: df[col].mean() for col, lbl in FACTORS.items()},
    }).sort_values("top2_share")

    fig, ax = plt.subplots(figsize=(9, 4.4))
    colors = [HIGHLIGHT if f in ("Flexibility", "Cost") else MUTED for f in summary.index]
    bars = ax.barh(summary.index, summary["top2_share"], color=colors, height=0.6)
    label_bars(ax, bars, "{:.0f}%")
    ax.set_xlim(0, 60)
    ax.set_title("What learners prioritise when choosing a method")
    ax.set_xlabel("% ranking the factor 1st or 2nd of 6 (n = 57)")
    ax.xaxis.grid(True, color="#eef1f2")
    ax.set_axisbelow(True)
    save(fig, "priority_top2.png")

    # Full rank distributions (the report's Figure 2), shared y-axis so panels compare.
    fig, axs = plt.subplots(2, 3, figsize=(12, 6), sharey=True)
    for ax, (col, lbl) in zip(axs.flat, FACTORS.items()):
        dist = df[col].value_counts().reindex(range(1, 7), fill_value=0)
        ax.bar(dist.index, dist.values, color=[HIGHLIGHT if r <= 2 else MUTED for r in dist.index], width=0.7)
        ax.set_title(lbl, fontsize=12)
        ax.set_xticks(range(1, 7))
        ax.yaxis.grid(True, color="#eef1f2")
        ax.set_axisbelow(True)
    fig.supxlabel("Rank (1 = most important, 6 = least)", color=INK_SOFT)
    fig.supylabel("Respondents", color=INK_SOFT)
    fig.suptitle("How each factor was ranked", x=0.01, ha="left", fontweight="bold", color=INK)
    fig.tight_layout()
    save(fig, "priority_rank_distributions.png")
    return summary.sort_values("top2_share", ascending=False).round(1)


def plot_profile(df: pd.DataFrame) -> None:
    order = ["No Proficiency", "Elementary Proficiency", "Limited Working Proficiency",
             "Professional Working Proficiency", "Full Professional Working Proficiency",
             "Native/Bilingual Proficiency"]
    prof = df["proficiency"].value_counts().reindex(order, fill_value=0)
    langs = df["foreign_language"].dropna().str.split(",").explode().str.strip().value_counts().head(8).sort_values()

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    bars = a1.barh([o.replace(" Proficiency", "") for o in prof.index], prof.values, color=HIGHLIGHT, height=0.6)
    label_bars(a1, bars)
    a1.invert_yaxis()
    a1.set_title("Self-rated proficiency (ILR scale)", fontsize=12)
    bars = a2.barh(langs.index, langs.values, color=HIGHLIGHT, height=0.6)
    label_bars(a2, bars)
    a2.set_title("Languages being learned (top 8)", fontsize=12)
    for ax in (a1, a2):
        ax.xaxis.grid(True, color="#eef1f2")
        ax.set_axisbelow(True)
    fig.suptitle("Who answered", x=0.01, ha="left", fontweight="bold", color=INK)
    fig.tight_layout()
    save(fig, "respondent_profile.png")


def main() -> None:
    df = load()
    print(f"Responses: {len(df)}  |  median age {df['age'].median():.0f}  |  "
          f"{df['foreign_language'].str.split(',').explode().str.strip().nunique()} languages\n")

    print("Most effective method (respondents):")
    print(plot_most_effective(df).sort_values(ascending=False).to_string(), "\n")

    print("Usage vs. perceived effectiveness (% of respondents):")
    print(plot_usage_vs_effectiveness(df).to_string(), "\n")

    print("Priorities (share ranking top-2, mean rank):")
    print(plot_priorities(df).to_string(), "\n")

    print("Weekly hours / budget (USD) per respondent:")
    print(df[["time_allocated", "budget"]].describe().loc[["count", "50%", "mean", "max"]].round(1).to_string())

    plot_profile(df)
    print(f"\nFigures written to {FIGURES.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
