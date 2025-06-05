import pandas as pd
import os
import re
import numpy as np

from src.helpers.utils.utils import read_from_json


def transform_metrics_to_markdown_table(json_file_path: str) -> str:
    data = read_from_json(json_file_path)

    # Regex pattern to extract components from the filename
    pattern = re.compile(
        r"meta_(\d{2}-\d{2}T\d{2}-\d{2}-\d{2})_([^_]+)_([^_]+)_(\d{4})_([^_]+)_([^\.]+)\.json"
    )

    all_rows_data = []

    for item in data:
        problem_path = item["problem_path"]
        filename = os.path.basename(problem_path)

        match = pattern.match(filename)
        if match:
            date_time, experiment_id, city, year, problem_type, method = (
                match.groups()
            )
        else:
            date_time, experiment_id, city, year, problem_type, method = [
                None
            ] * 6

        row_data = {
            "Date-Time": date_time,
            "ID": experiment_id,
            "City": city,
            "Year": year,
            "Type": problem_type,
            "Method": method,
        }

        for metric_name in item.get("metrics", []):  # Safely get metrics list
            metric_details = item.get(metric_name)

            if metric_details is None:
                continue

            if metric_name == "NON_ZERO_OBJECTIVES":
                non_zero_count = metric_details.get("non_zero_count", 0)
                zero_count = metric_details.get("zero_count", 0)
                row_data["Zero/Non-Zero Ratio"] = (
                    zero_count / non_zero_count
                    if non_zero_count > 0
                    else np.nan
                )
            elif metric_name == "SUM_OBJECTIVES":
                row_data["SUM_OBJECTIVES (sum)"] = metric_details.get("sum")
            else:
                for sub_key, sub_value in metric_details.items():
                    row_data[f"{metric_name}_{sub_key}"] = sub_value

        all_rows_data.append(row_data)

    df = pd.DataFrame(all_rows_data)

    # Post-processing steps
    if "Date-Time" in df.columns and "ID" in df.columns:
        df = df.drop(columns=["Date-Time", "ID"])

    if "City" in df.columns and "Year" in df.columns:
        # Convert Year to string before concatenation to ensure compatibility if it's numeric
        df["Location-Year"] = (
            df["City"].astype(str) + " " + df["Year"].astype(str)
        )
        df = df.drop(columns=["City", "Year"])

    if "Location-Year" in df.columns:
        cols = df.columns.tolist()
        # Move 'Location-Year' to the first position
        cols.insert(0, cols.pop(cols.index("Location-Year")))
        df = df[cols]

    df = df.sort_values(by=["Location-Year", "Type", "Method"], ascending=True)

    return df.to_markdown(index=False)
