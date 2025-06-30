import pandas as pd
import os
import re

from helpers.utils.utils import read_from_json
from helpers.runners.model import Solver, Utility


def transform_metrics_to_markdown_table(json_file_path: str) -> str:
    data = read_from_json(json_file_path)

    solver_pattern = "|".join(
        re.escape(s)
        for s in sorted(list(Solver.__args__), key=len, reverse=True)
    )
    utility_pattern = "|".join(
        re.escape(u)
        for u in sorted(list(Utility.__args__), key=len, reverse=True)
    )
    datetime_pattern = r"(\d{2}-\d{2}T\d{2}-\d{2}-\d{2})"
    id_pattern = r"([a-zA-Z0-9]{4})"

    pattern = re.compile(
        rf"meta_{datetime_pattern}_{id_pattern}_((?:(?!_{utility_pattern}).)*)_({utility_pattern})_({solver_pattern})\.json"
    )

    all_rows_data = []

    for item in data:
        problem_path = item["problem_path"]
        filename = os.path.basename(problem_path)

        match = pattern.match(filename)
        if match:
            date_time, experiment_id, city, problem_type, method = (
                match.groups()
            )
        else:
            raise Exception(
                f"Filename '{filename}' did not match the regex pattern."
            )

        row_data = {
            "Date-Time": date_time,
            "ID": experiment_id,
            "City": city,
            "Type": problem_type,
            "Method": method,
        }

        for metric_name in item.get("metrics", []):
            metric_details = item.get(metric_name)

            if metric_details is None:
                continue

            if metric_name == "EXCLUSION_RATION":
                row_data["EXCLUSION_RATION"] = metric_details.get(
                    "exclusion_ratio"
                )
            elif metric_name == "SUM_OBJECTIVES":
                row_data["SUM_OBJECTIVES"] = metric_details.get("sum")
            elif metric_name == "EJR_PLUS":
                row_data["EJR_PLUS"] = metric_details.get("ejr_plus")
            else:
                for sub_key, sub_value in metric_details.items():
                    row_data[f"{metric_name}_{sub_key}"] = sub_value

        all_rows_data.append(row_data)

    df = pd.DataFrame(all_rows_data)

    if "Date-Time" in df.columns and "ID" in df.columns:
        df = df.drop(columns=["Date-Time", "ID"])

    if "City" in df.columns:
        df["Location-Year"] = df["City"].astype(str).str.replace("_", " ")
        df = df.drop(columns=["City"])

    if "Location-Year" in df.columns:
        cols = df.columns.tolist()
        if "Location-Year" in cols:
            cols.insert(0, cols.pop(cols.index("Location-Year")))
            df = df[cols]

    df = df.sort_values(by=["Location-Year", "Type", "Method"], ascending=True)

    return df.to_markdown(index=False)
