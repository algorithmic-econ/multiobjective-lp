import logging
from pathlib import Path

import pandas as pd

from helpers.utils.utils import read_from_json

logger = logging.getLogger(__name__)


def transform_metrics_to_markdown_table(
    json_file_path: Path, limit: int | None
) -> str:
    data = read_from_json(json_file_path)

    all_rows_data = []

    for idx, item in enumerate(data):
        if "error_type" in item:
            logger.warning(
                "Skip failed result item from result table",
                extra={"result_item": idx, "meta_path": item.get("meta_path")},
            )
            continue

        row_data = {
            "City": item["city"],
            "Type": item["utility"],
            "Method": item["solver"],
        }

        for metric_name in item.get("metrics", []):
            logger.debug(f"Calculating metric {metric_name}")
            metric_details = item.get(metric_name)

            if metric_details is None:
                continue

            if metric_name == "EXCLUSION_RATION":
                row_data["Exclusion ratio"] = round(
                    metric_details.get("exclusion_ratio"), 4
                )
            elif metric_name == "SUM_OBJECTIVES":
                row_data["Sum objectives"] = metric_details.get("sum")
            elif metric_name == "EJR_PLUS":
                row_data["EJR+ violations"] = metric_details.get("ejr_plus")
            else:
                for sub_key, sub_value in metric_details.items():
                    row_data[f"{metric_name}_{sub_key}"] = sub_value

        all_rows_data.append(row_data)

    if not all_rows_data:
        return "no analyzable rows"

    df = pd.DataFrame(all_rows_data)

    df["Location-Year"] = df["City"].astype(str).str.replace("_", " ")
    df = df.drop(columns=["City"])

    cols = df.columns.tolist()
    cols.insert(0, cols.pop(cols.index("Location-Year")))
    df = pd.DataFrame(df[cols])

    df = df.sort_values(by=["Location-Year", "Type", "Method"], ascending=True)

    df_limited = df.head(limit) if limit is not None else df
    # buf=None -> to_markdown returns str; stubs say str | None
    return df_limited.to_markdown(index=False) or ""
