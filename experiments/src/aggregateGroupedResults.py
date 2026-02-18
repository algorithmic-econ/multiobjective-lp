import logging
import sys
from pathlib import Path
from typing import List, Union

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Adjust these imports to match your project structure if necessary
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
        "EJR_PLUS": ("ejr_plus", "EJR Plus"),
        "CONSTRAINTS": ("invalid_count", "Constraints (Invalid)"),
        "INSTANCE_SIZE": ("size", "Instance Size"),
    }

    for entry in data_source:
        solver = entry.get("solver", "Unknown")
        options = entry.get("solver_options", {})
        solver_label = f"{solver}_{options}" if options else solver

        # --- Parse City and Year ---
        # Format is expected to be {city_name}_{year}, e.g., "warszawa_2023"
        raw_city_field = entry.get("city", "Unknown_0000")
        try:
            # Split from the right to safely handle city names with underscores (e.g., "new_york_2023")
            city_name, year_str = raw_city_field.rsplit("_", 1)
            # Capitalize for display
            city_display = city_name.capitalize()
        except ValueError:
            # Fallback if format doesn't match
            city_display = raw_city_field

        metrics_list = entry.get("metrics", [])

        for metric_key in metrics_list:
            if metric_key in metric_display_map:
                val_key, display_name = metric_display_map[metric_key]
                val = entry.get(metric_key, {}).get(val_key)
                if val is not None:
                    processed_data.append(
                        {
                            "City": city_display,
                            "Solver": solver_label,
                            "Metric": display_name,
                            "Value": val,
                        }
                    )

        if "time" in entry:
            processed_data.append(
                {
                    "City": city_display,
                    "Solver": solver_label,
                    "Metric": "running time (s.)",
                    "Value": entry["time"],
                }
            )

    df = pd.DataFrame(processed_data)

    if df.empty:
        logger.warning("No data found to plot.")
        return

    # --- 2. Aggregation (Average by Year) ---
    # Group by City + Solver + Metric and calculate the Mean (averaging over years)
    df = df[(df["City"] != "Zabrze") & (df["City"] != "Amsterdam")]
    df_agg = df.groupby(["City", "Solver", "Metric"], as_index=False)[
        "Value"
    ].mean()

    # Sort so the cities appear in consistent order (Alphabetical)
    df_agg = df_agg.sort_values(by="City")

    # unique_solvers = sorted(df_agg["Solver"].unique())

    # --- 3. Visualization Style ---

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

    # --- 4. Plotting ---

    # Using catplot with kind='bar' is best for Categorical X (City) vs Numerical Y (Value)
    g = sns.catplot(
        data=df_agg,
        x="City",
        y="Value",
        col="Metric",
        hue="Solver",
        kind="bar",
        col_wrap=1,  # Stack plots vertically
        height=4,  # Height of each subplot
        aspect=2.0,  # Width aspect ratio
        sharey=False,  # Independent Y-axes
        sharex=True,
        legend_out=True,
        palette="viridis",  # Good color palette for distinguishing solvers
        edgecolor="black",  # Add border to bars for clarity
        alpha=0.9,
    )

    # --- 5. Customizing Axes & Legend ---

    for ax in g.axes.flat:
        title = ax.get_title()
        # Clean up title "Metric = Something" -> "Something"
        clean_title = title.split("=")[-1].strip()
        ax.set_title("")
        ax.set_ylabel(clean_title, fontweight="bold")
        ax.set_xlabel("City (Avg. over available years)", fontweight="bold")

        # Log scale for time if needed
        if "running time" in clean_title.lower():
            ax.set_yscale("log")

        ax.set_axisbelow(True)

    # Clean up the automatic legend title
    if g.legend:
        g.legend.set_title("Solver")
        # Optional: Move legend to bottom if preferred, similar to previous script
        # sns.move_legend(g, "lower center", bbox_to_anchor=(.5, 1), ncol=len(unique_solvers))

    g.fig.subplots_adjust(top=0.9, hspace=0.3)

    output_filename = "../resources/experiment_results_by_city.png"
    # Create directory if it doesn't exist
    Path(output_filename).parent.mkdir(parents=True, exist_ok=True)

    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    logger.info(f"Chart saved to {output_filename}")


if __name__ == "__main__":
    # Example usage: python aggregateResults.py path/to/results.json
    if len(sys.argv) > 1:
        analyzer_result = read_from_json(Path(sys.argv[1]))
        main(analyzer_result)
    else:
        logger.error("Please provide a path to the results JSON file.")
