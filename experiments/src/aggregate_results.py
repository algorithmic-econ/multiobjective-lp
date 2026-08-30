import logging
import sys
from pathlib import Path

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from helpers.analyzers.model import AggregatorConfig, AnalyzerResult
from helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)

# metric key -> (value key inside the metric dict, display name)
METRIC_DISPLAY_MAP = {
    "EXCLUSION_RATION": ("exclusion_ratio", "Exclusion Ratio"),
    "SUM_OBJECTIVES": ("sum", "Sum Objectives"),
    "TOTAL_COST": ("total_cost", "Total Cost"),
    "EJR_PLUS": ("ejr_plus", "EJR Plus"),
}

TIME_METRIC = "running time (s.)"
SUM_OBJECTIVES_LABEL = METRIC_DISPLAY_MAP["SUM_OBJECTIVES"][1]
TOTAL_COST_LABEL = METRIC_DISPLAY_MAP["TOTAL_COST"][1]


def load_rows(metrics_json_path: Path) -> list[AnalyzerResult]:
    raw = read_from_json(metrics_json_path)
    entries = raw if isinstance(raw, list) else [raw]

    rows = []
    for entry in entries:
        try:
            rows.append(AnalyzerResult.model_validate(entry))
        except Exception as exc:
            logger.warning("Skipping invalid row: %s", exc)
    return rows


def _solver_label(row: AnalyzerResult) -> str:
    return (
        f"{row.solver}_{row.solver_options}"
        if row.solver_options
        else str(row.solver)
    )


def _city_year(city: str) -> tuple[str, str]:
    try:
        name, year = city.rsplit("_", 1)
        return name.capitalize(), year
    except ValueError:
        return city, ""


def _rows_to_frame(rows: list[AnalyzerResult], group_by: str) -> pd.DataFrame:
    records = []
    for row in rows:
        solver_label = _solver_label(row)
        if group_by == "city":
            city_display, _ = _city_year(row.city)
        else:
            city_display = row.city

        for metric_key, (val_key, display_name) in METRIC_DISPLAY_MAP.items():
            metric_dict = getattr(row, metric_key)
            val = metric_dict.get(val_key) if metric_dict else None
            if val is None:
                continue
            record = {
                "City": city_display,
                "Solver": solver_label,
                "Metric": display_name,
                "Value": val,
            }
            if group_by == "instance_size_bucket":
                instance_size = (
                    row.INSTANCE_SIZE.get("size")
                    if row.INSTANCE_SIZE
                    else None
                )
                record["Instance Size"] = instance_size
            records.append(record)

        time_record = {
            "City": city_display,
            "Solver": solver_label,
            "Metric": TIME_METRIC,
            "Value": row.time,
        }
        if group_by == "instance_size_bucket":
            instance_size = (
                row.INSTANCE_SIZE.get("size") if row.INSTANCE_SIZE else None
            )
            time_record["Instance Size"] = instance_size
        records.append(time_record)

    return pd.DataFrame(records)


def _apply_filters(df: pd.DataFrame, config: AggregatorConfig) -> pd.DataFrame:
    if config.exclude_cities:
        df = df.loc[~df["City"].isin(config.exclude_cities)]
    if config.include_solvers is not None:
        df = df.loc[df["Solver"].isin(config.include_solvers)]
    return df


def _normalize_relative_to_baseline(
    df: pd.DataFrame,
    metric_label: str,
    baseline_solver: str,
    clip_upper: float,
    new_label: str,
) -> pd.DataFrame:
    mask = df["Metric"] == metric_label
    metric_df = df[mask]
    # groupby+mean (not set_index) so duplicate City rows (e.g. multiple
    # utilities/instance sizes sharing a city) collapse to one scalar
    # baseline instead of crashing the per-row division below.
    baseline = (
        metric_df[metric_df["Solver"].str.startswith(baseline_solver)]
        .groupby("City")["Value"]
        .mean()
    )

    df.loc[mask, "Value"] = df.loc[mask].apply(
        lambda row: (
            row["Value"] / baseline[row["City"]]
            if row["City"] in baseline.index
            else row["Value"]
        ),
        axis=1,
    )
    df.loc[mask, "Value"] = df.loc[mask, "Value"].clip(upper=clip_upper)
    df.loc[mask, "Metric"] = new_label
    return df


def _add_zoomed_cost_panel(df_agg: pd.DataFrame) -> pd.DataFrame:
    cost_rows = df_agg[
        df_agg["Metric"] == "Total Cost (rel. to Greedy)"
    ].copy()
    if cost_rows.empty:
        return df_agg
    q1 = cost_rows["Value"].quantile(0.25)
    q3 = cost_rows["Value"].quantile(0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    zoomed = cost_rows[
        (cost_rows["Value"] >= lo) & (cost_rows["Value"] <= hi)
    ].copy()
    zoomed["Metric"] = "Total Cost (zoomed)"
    return pd.concat([df_agg, zoomed], ignore_index=True)


def _build_bucket_dataframe(
    df: pd.DataFrame, config: AggregatorConfig
) -> pd.DataFrame:
    if config.normalize_baseline is not None:
        baseline = str(config.normalize_baseline)
        df = _normalize_relative_to_baseline(
            df,
            SUM_OBJECTIVES_LABEL,
            baseline,
            config.clip_upper,
            "Sum Objectives (rel. to Greedy)",
        )
        df = _normalize_relative_to_baseline(
            df,
            TOTAL_COST_LABEL,
            baseline,
            config.clip_upper,
            "Total Cost (rel. to Greedy)",
        )

    if df.empty:
        return df

    df["Bucket"] = (
        df["Instance Size"] // config.bucket_size
    ) * config.bucket_size
    df_agg = df.groupby(["Bucket", "Solver", "Metric"], as_index=False)[
        "Value"
    ].mean()
    df_agg = df_agg.sort_values(by="Bucket")

    if config.normalize_baseline is not None:
        df_agg = _add_zoomed_cost_panel(df_agg)

    return df_agg


def _build_city_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df_agg = df.groupby(["City", "Solver", "Metric"], as_index=False)[
        "Value"
    ].mean()
    return df_agg.sort_values(by="City")


def build_dataframe(
    rows: list[AnalyzerResult], config: AggregatorConfig
) -> pd.DataFrame:
    df = _rows_to_frame(rows, config.group_by)
    if df.empty:
        return df

    df = _apply_filters(df, config)
    if df.empty:
        return df

    if config.group_by == "instance_size_bucket":
        return _build_bucket_dataframe(df, config)
    return _build_city_dataframe(df)


def _metric_col_order(df_agg: pd.DataFrame) -> list[str]:
    desired_order = []
    for metric in df_agg["Metric"].unique():
        desired_order.append(metric)
        if metric == "Total Cost (rel. to Greedy)":
            desired_order.append("Total Cost (zoomed)")
    return list(dict.fromkeys(desired_order))


def _apply_style() -> None:
    sns.set_theme(style="whitegrid", rc={"grid.linestyle": ":"})
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
            "axes.labelsize": 12,
            "axes.titlesize": 12,
            "font.size": 11,
            "legend.fontsize": 11,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "axes.edgecolor": "black",
            "axes.linewidth": 1.0,
        }
    )


def _plot_bucket(df_agg: pd.DataFrame, output_path: Path) -> None:
    _apply_style()
    plt.rcParams.update({"lines.linewidth": 1.5, "lines.markersize": 7})

    unique_solvers = sorted(df_agg["Solver"].unique())
    markers_list = ["D", "o", "s", "^", "v", "X", "*"]
    col_order = _metric_col_order(df_agg)

    g = sns.relplot(
        data=df_agg,
        x="Bucket",
        y="Value",
        col="Metric",
        col_order=col_order,
        hue="Solver",
        style="Solver",
        kind="line",
        markers=markers_list[: len(unique_solvers)],
        dashes=False,
        col_wrap=1,
        height=5,
        aspect=1.5,
        facet_kws={"sharey": False, "sharex": False, "legend_out": False},
        alpha=0.85,
    )

    for ax in g.axes.flat:
        title = ax.get_title()
        clean_title = title.split("=")[-1].strip()
        ax.set_title("")
        ax.set_ylabel(clean_title, fontweight="bold")
        ax.set_xlabel("instance size (grouped by bucket)", fontweight="bold")
        if TIME_METRIC in clean_title.lower():
            ax.set_yscale("log")
        ax.set_axisbelow(True)

    if g.legend:
        g.legend.remove()
    handles, labels = g.axes[0].get_legend_handles_labels()
    g.fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.02),
        ncol=len(unique_solvers),
        frameon=True,
        edgecolor="black",
        fancybox=False,
    )
    g.fig.subplots_adjust(bottom=0.18, wspace=0.25, hspace=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(g.fig)
    logger.info("Chart saved to %s", output_path)


def _plot_city(df_agg: pd.DataFrame, output_path: Path) -> None:
    _apply_style()

    g = sns.catplot(
        data=df_agg,
        x="City",
        y="Value",
        col="Metric",
        hue="Solver",
        kind="bar",
        col_wrap=1,
        height=4,
        aspect=2.0,
        sharey=False,
        sharex=True,
        legend_out=True,
        palette="viridis",
        edgecolor="black",
        alpha=0.9,
    )

    for ax in g.axes.flat:
        title = ax.get_title()
        clean_title = title.split("=")[-1].strip()
        ax.set_title("")
        ax.set_ylabel(clean_title, fontweight="bold")
        ax.set_xlabel("City (Avg. over available years)", fontweight="bold")
        if TIME_METRIC in clean_title.lower():
            ax.set_yscale("log")
        ax.set_axisbelow(True)

    if g.legend:
        g.legend.set_title("Solver")
    g.fig.subplots_adjust(top=0.9, hspace=0.3)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(g.fig)
    logger.info("Chart saved to %s", output_path)


def plot(df: pd.DataFrame, config: AggregatorConfig) -> None:
    if df.empty:
        logger.warning("No data found to plot.")
        return

    output_path = Path(config.output_path)
    if config.group_by == "instance_size_bucket":
        _plot_bucket(df, output_path)
    else:
        _plot_city(df, output_path)


def main(config_path: Path) -> Path:
    config = AggregatorConfig.model_validate(read_from_json(config_path))
    rows = load_rows(Path(config.metrics_json_path))
    df = build_dataframe(rows, config)
    plot(df, config)
    return Path(config.output_path)


if __name__ == "__main__":
    result_path = main(Path(sys.argv[1]))
    logger.info("Chart saved", extra={"result_path": str(result_path)})
