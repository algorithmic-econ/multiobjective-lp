## V3 - buckets
import logging
import sys
from pathlib import Path
from typing import List, Union

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from src.helpers.analyzers.model import AnalyzerResult
from src.helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)


def main(result: Union[AnalyzerResult, List[AnalyzerResult]]) -> None:
    # --- 1. Data Processing ---

    data_source = result if isinstance(result, list) else [result]

    processed_data = []

    metric_display_map = {
        "EXCLUSION_RATION": ("exclusion_ratio", "Exclusion Ratio"),
        "SUM_OBJECTIVES": ("sum", "Sum Objectives"),
        "TOTAL_COST": ("total_cost", "Total Cost"),
        "EJR_PLUS": ("ejr_plus", "EJR Plus"),
        # "CONSTRAINTS": ("invalid_count", "Constraints (Invalid)"),
    }

    for entry in data_source:
        solver = entry.get("solver", "Unknown")
        options = entry.get("solver_options", {})
        solver_label = f"{solver}_{options}" if options else solver

        instance_size = entry.get("INSTANCE_SIZE", {}).get("size")
        metrics_list = entry.get("metrics", [])

        for metric_key in metrics_list:
            if metric_key in metric_display_map:
                val_key, display_name = metric_display_map[metric_key]
                val = entry.get(metric_key, {}).get(val_key)
                if val is not None:
                    processed_data.append(
                        {
                            "Instance Size": instance_size,
                            "Solver": solver_label,
                            "Metric": display_name,
                            "Value": val,
                            "City": entry.get("city"),
                        }
                    )

        if "time" in entry:
            processed_data.append(
                {
                    "Instance Size": instance_size,
                    "Solver": solver_label,
                    "Metric": "running time (s.)",
                    "Value": entry["time"],
                    "City": entry.get("city"),
                }
            )

    df = pd.DataFrame(processed_data)

    # Normalize SUM_OBJECTIVES relative to GREEDY baseline
    sum_obj_label = metric_display_map["SUM_OBJECTIVES"][1]
    mask = df["Metric"] == sum_obj_label
    sum_df = df[mask]
    greedy_baseline = sum_df[
        sum_df["Solver"].str.startswith("GREEDY")
    ].set_index("City")["Value"]
    df.loc[mask, "Value"] = df.loc[mask].apply(
        lambda row: (
            row["Value"] / greedy_baseline[row["City"]]
            if row["City"] in greedy_baseline.index
            else row["Value"]
        ),
        axis=1,
    )
    df.loc[mask, "Value"] = df.loc[mask, "Value"].clip(upper=5.0)
    df.loc[mask, "Metric"] = "Sum Objectives (rel. to Greedy)"

    # Normalize TOTAL_COST relative to GREEDY baseline
    cost_label = metric_display_map["TOTAL_COST"][1]
    cost_mask = df["Metric"] == cost_label
    cost_df = df[cost_mask]
    greedy_cost_baseline = cost_df[
        cost_df["Solver"].str.startswith("GREEDY")
    ].set_index("City")["Value"]
    df.loc[cost_mask, "Value"] = df.loc[cost_mask].apply(
        lambda row: (
            row["Value"] / greedy_cost_baseline[row["City"]]
            if row["City"] in greedy_cost_baseline.index
            else row["Value"]
        ),
        axis=1,
    )
    df.loc[cost_mask, "Value"] = df.loc[cost_mask, "Value"].clip(upper=5.0)
    df.loc[cost_mask, "Metric"] = "Total Cost (rel. to Greedy)"

    if df.empty:
        logger.warning("No data found to plot.")
        return

    # df = df[(df["Solver"] == "GREEDY") | (df["Solver"] == "PHRAGMEN_{'kappa': 1.0, 'increasing_scalings': False}") | (df["Solver"] == "PHRAGMEN_{'kappa': 1.0, 'increasing_scalings': True}")]
    # --- 2. Binning & Aggregation ---

    # Create buckets of size 10 (e.g., 30, 40, 50...)
    bucket_size = 10
    df["Bucket"] = (df["Instance Size"] // bucket_size) * bucket_size

    # Group by Bucket + Solver + Metric and calculate the Mean
    df_agg = df.groupby(["Bucket", "Solver", "Metric"], as_index=False)[
        "Value"
    ].mean()

    # Sort by Bucket to ensure proper line connections
    df_agg = df_agg.sort_values(by="Bucket")

    # Add zoomed Total Cost panel (IQR-filtered, no outliers)
    cost_rows = df_agg[
        df_agg["Metric"] == "Total Cost (rel. to Greedy)"
    ].copy()
    if not cost_rows.empty:
        q1 = cost_rows["Value"].quantile(0.25)
        q3 = cost_rows["Value"].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        zoomed = cost_rows[
            (cost_rows["Value"] >= lo) & (cost_rows["Value"] <= hi)
        ].copy()
        zoomed["Metric"] = "Total Cost (zoomed)"
        df_agg = pd.concat([df_agg, zoomed], ignore_index=True)

    # Order "Total Cost (zoomed)" directly after "Total Cost (rel. to Greedy)"
    desired_order = []
    for m in df_agg["Metric"].unique():
        desired_order.append(m)
        if m == "Total Cost (rel. to Greedy)":
            desired_order.append("Total Cost (zoomed)")
    col_order = list(dict.fromkeys(desired_order))

    # --- 3. Jitter / Dodge Logic ---

    unique_solvers = sorted(df_agg["Solver"].unique())
    n_solvers = len(unique_solvers)

    # Shift scale: Since buckets are 10 units wide, a shift of ~2.0 is visible but safe
    shift_scale = 0
    solver_offsets = {
        solver: (i - (n_solvers - 1) / 2) * shift_scale
        for i, solver in enumerate(unique_solvers)
    }

    # Apply shift to the Bucket value for plotting X-axis
    df_agg["Bucket Plot"] = df_agg.apply(
        lambda row: row["Bucket"] + solver_offsets[row["Solver"]], axis=1
    )

    # --- 4. Visualization Style ---

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
            "lines.linewidth": 1.5,
            "lines.markersize": 7,
            "axes.edgecolor": "black",
            "axes.linewidth": 1.0,
        }
    )

    # --- 5. Plotting ---

    markers_list = ["D", "o", "s", "^", "v", "X", "*"]

    g = sns.relplot(
        data=df_agg,
        x="Bucket Plot",  # Use the shifted bucket values
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

    # --- 6. Customizing Axes & Legend ---

    for ax in g.axes.flat:
        title = ax.get_title()
        clean_title = title.split("=")[-1].strip()
        ax.set_title("")
        ax.set_ylabel(clean_title, fontweight="bold")
        ax.set_xlabel("instance size (grouped by 10)", fontweight="bold")

        if "running time" in clean_title.lower():
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

    output_filename = "../resources/pabulib-all-single-auto.png"
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    logger.info(f"Chart saved to {output_filename}")


if __name__ == "__main__":
    analyzer_result = read_from_json(Path(sys.argv[1]))
    main(analyzer_result)

## V2 - academic + jitter
# import logging
# import sys
# from pathlib import Path
# from typing import List, Union
#
# import pandas as pd
# import seaborn as sns
# import matplotlib.pyplot as plt
#
# from helpers.utils.logger import setup_logging
# from helpers.analyzers.model import AnalyzerResult
# from helpers.utils.utils import read_from_json
#
# logger = logging.getLogger(__name__)
#
#
# def main(result: Union[AnalyzerResult, List[AnalyzerResult]]) -> None:
#     # --- 1. Data Processing ---
#
#     # Ensure we are working with a list of results
#     data_source = result if isinstance(result, list) else [result]
#
#     processed_data = []
#
#     # Dictionary to map internal keys to display names matching the academic style
#     metric_display_map = {
#         'EXCLUSION_RATION': ('exclusion_ratio', 'Exclusion Ratio'),
#         'SUM_OBJECTIVES': ('sum', 'Sum Objectives'),
#         'EJR_PLUS': ('ejr_plus', 'EJR Plus'),
#         'CONSTRAINTS': ('invalid_count', 'Constraints (Invalid)'),
#     }
#
#     for entry in data_source:
#         solver = entry.get('solver', 'Unknown')
#         options = entry.get('solver_options', {})
#         # Create a combined label for Solver + Options
#         solver_label = f"{solver}_{options}" if options else solver
#
#         instance_size = entry.get('INSTANCE_SIZE', {}).get('size')
#         metrics_list = entry.get('metrics', [])
#
#         # Extract standard metrics
#         for metric_key in metrics_list:
#             if metric_key in metric_display_map:
#                 val_key, display_name = metric_display_map[metric_key]
#                 val = entry.get(metric_key, {}).get(val_key)
#                 if val is not None:
#                     processed_data.append({
#                         'Instance Size': instance_size,
#                         'Solver': solver_label,
#                         'Metric': display_name,
#                         'Value': val
#                     })
#
#         # Extract Time
#         if 'time' in entry:
#             processed_data.append({
#                 'Instance Size': instance_size,
#                 'Solver': solver_label,
#                 'Metric': 'running time (s.)',
#                 'Value': entry['time']
#             })
#
#     df = pd.DataFrame(processed_data)
#
#     # df = df[df["Instance Size"] <= 100] # TODO FILTERS
#     df = df[(df["Solver"] == "GREEDY") | (df["Solver"] == "PHRAGMEN_{'kappa': 1.0, 'increasing_scalings': False}") | (df["Solver"] == "PHRAGMEN_{'kappa': 1.0, 'increasing_scalings': True}")]
#
#
#     if df.empty:
#         logger.warning("No data found to plot.")
#         return
#
#     # Sort by size to ensure lines connect in correct order
#     df = df.sort_values(by='Instance Size')
#
#     # --- 2. Jitter / Dodge Logic ---
#     # Manually shift X-values slightly for each solver to avoid perfect overlap
#     unique_solvers = sorted(df['Solver'].unique())
#     n_solvers = len(unique_solvers)
#
#     # Define a small shift per solver (e.g., -0.6, -0.2, +0.2, +0.6)
#     # Adjust 'shift_scale' based on how close your instance sizes are.
#     # If instance sizes differ by ~2-5, a shift of 0.5 is safe.
#     shift_scale = 0
#     solver_offsets = {
#         solver: (i - (n_solvers - 1) / 2) * shift_scale
#         for i, solver in enumerate(unique_solvers)
#     }
#
#     # Apply the shift to create a new plotting column
#     df['Instance Size Plot'] = df.apply(
#         lambda row: row['Instance Size'] + solver_offsets[row['Solver']],
#         axis=1
#     )
#
#     # --- 3. Visualization Style Configuration ---
#
#     sns.set_theme(style="whitegrid", rc={"grid.linestyle": ":"})
#
#     # Update matplotlib params for "Academic/LaTeX" look
#     plt.rcParams.update({
#         "font.family": "serif",
#         "font.serif": ["Times New Roman", "DejaVu Serif", "serif"],
#         "axes.labelsize": 12,
#         "axes.titlesize": 12,
#         "font.size": 11,
#         "legend.fontsize": 11,
#         "xtick.labelsize": 10,
#         "ytick.labelsize": 10,
#         "lines.linewidth": 1.5,
#         "lines.markersize": 7,
#         "axes.edgecolor": "black",
#         "axes.linewidth": 1.0,
#     })
#
#     # --- 4. Plotting ---
#
#     # Define distinct markers
#     markers_list = ['D', 'o', 's', '^', 'v', 'X', '*']
#
#     g = sns.relplot(
#         data=df,
#         x='Instance Size Plot',  # Use the shifted X-axis
#         y='Value',
#         col='Metric',
#         hue='Solver',
#         style='Solver',
#         kind='line',
#         markers=markers_list[:len(unique_solvers)],
#         dashes=False,
#         col_wrap=1,
#         height=6,
#         aspect=1.5,
#         facet_kws={'sharey': False, 'sharex': False, 'legend_out': False},
#         alpha=0.85         # Slight transparency to show overlaps
#     )
#
#     # --- 5. Customizing Axes & Legend ---
#
#     for ax in g.axes.flat:
#         title = ax.get_title()
#         clean_title = title.split('=')[-1].strip()
#         ax.set_title("")
#         ax.set_ylabel(clean_title, fontweight='bold')
#         # Manually set X-label since we used the jittered column name
#         ax.set_xlabel("number of projects", fontweight='bold')
#
#         # Apply Log Scale specifically to Time
#         if "running time" in clean_title.lower():
#             ax.set_yscale('log')
#
#         ax.set_axisbelow(True)
#
#     # Re-create legend at bottom
#     if g.legend:
#         g.legend.remove()
#
#     handles, labels = g.axes[0].get_legend_handles_labels()
#
#     g.fig.legend(
#         handles, labels,
#         loc='lower center',
#         bbox_to_anchor=(0.5, 0.02),
#         ncol=len(unique_solvers),
#         frameon=True,
#         edgecolor='black',
#         fancybox=False
#     )
#
#     g.fig.subplots_adjust(bottom=0.18, wspace=0.25, hspace=0.3)
#
#     # --- 6. Save ---
#     output_filename = "../resources/experiment_results_academic.png"
#     plt.savefig(output_filename, dpi=300, bbox_inches='tight')
#     logger.info(f"Chart saved to {output_filename}")
#
#
# if __name__ == "__main__":
#     analyzer_result = read_from_json(Path(sys.argv[1]))
#     main(analyzer_result)


## V1
# import logging
# import sys
# from pathlib import Path
#
# import matplotlib.pyplot as plt
# import pandas as pd
# import seaborn as sns
#
# from helpers.analyzers.model import AnalyzerResult
# from helpers.utils.utils import read_from_json
#
# logger = logging.getLogger(__name__)
#
#
# def main(result: list[AnalyzerResult]) -> None:
#     processed_data = []
#
#     for entry in result:
#         solver = entry.get("solver", "Unknown")
#         options = entry.get("solver_options", {})
#
#         solver_full = f"{solver}_{options}" if options else solver
#
#         # Get grouping variable (x-axis)
#         instance_size = entry.get("INSTANCE_SIZE", {}).get("size")
#
#         metrics_list = entry.get("metrics", [])
#
#         # Mapping known metrics to their specific value keys
#         # You can extend this mapping if new metrics are added
#         metric_value_map = {
#             "EXCLUSION_RATION": ("exclusion_ratio", "Exclusion Ratio"),
#             "SUM_OBJECTIVES": ("sum", "Sum Objectives"),
#             "EJR_PLUS": ("ejr_plus", "EJR Plus"),
#             "CONSTRAINTS": ("invalid_count", "Constraints Invalid Count"),
#         }
#
#         # Add explicitly listed metrics
#         for metric_key in metrics_list:
#             if metric_key in metric_value_map:
#                 val_key, display_name = metric_value_map[metric_key]
#                 val = entry.get(metric_key, {}).get(val_key)
#                 if val is not None:
#                     processed_data.append(
#                         {
#                             "Instance Size": instance_size,
#                             "Solver": solver_full,
#                             "Metric": display_name,
#                             "Value": val,
#                         }
#                     )
#
#         # Optionally add 'Time' if it's not in the metrics list but present in the root
#         if "time" in entry:
#             processed_data.append(
#                 {
#                     "Instance Size": instance_size,
#                     "Solver": solver_full,
#                     "Metric": "Time (s)",
#                     "Value": entry["time"],
#                 }
#             )
#
#     df = pd.DataFrame(processed_data)
#
#     if df.empty:
#         logger.warning("No data found to plot.")
#         return
#
#     # Sort to ensure line plots connect points in order
#     df = df.sort_values(by="Instance Size")
#
#     # 2. Use seaborn graphing library to create charts
#     # 2.1 Charts should be line plots
#     # 2.2 Results grouped by instance size (x-axis)
#     # 2.2 Each metric has its own subplot (y-axis is Value, col is Metric)
#     sns.set_theme(style="whitegrid")
#
#     # greedy pokrywa się z PHRAGMEN_{'kappa': 0.0, 'increasing_scalings': True} ?
#     df = df[(df["Solver"] == "GREEDY") | (df["Solver"] == "PHRAGMEN_{'kappa': 0.0, 'increasing_scalings': False}") | (df["Solver"] == "PHRAGMEN_{'kappa': 1.0, 'increasing_scalings': True}")]
#
#     g = sns.relplot(
#         data=df,
#         x="Instance Size",
#         y="Value",
#         col="Metric",
#         hue="Solver",
#         style="Solver",
#         kind="line",
#         markers=True,
#         dashes=False,
#         col_wrap=2,  # Adjust columns per row as needed
#         facet_kws={"sharey": False},  # Allow independent y-axis scales
#         alpha=0.8
#     )
#
#     g.set_titles("{col_name}")
#     g.tight_layout()
#
#     # Save the figure
#     output_filename = "../resources/experiment_results.png"
#     plt.savefig(output_filename)
#     logger.info(f"Chart saved to {output_filename}")
#
#
# if __name__ == "__main__":
#     analyzer_result: list[AnalyzerResult] = read_from_json(Path(sys.argv[1]))
#     main(analyzer_result)
