import os

import pandas as pd

from vrp_cli import run_on_instance


def run_all_instances_in_directory(directory_path, visualize=False, stdout=True):
    results = []

    for file_name in os.listdir(directory_path):
        if file_name.endswith(".vrp"):
            instance_path = os.path.join(directory_path, file_name)
            try:
                for result in run_on_instance(instance_path, visualize=visualize, stdout=stdout):
                    result["instance_file"] = file_name  # optionally add file name for traceability
                    results.append(result)
            except Exception as e:
                if stdout:
                    print(f"❌ Error running instance {file_name}: {e}")
                results.append({
                    "instance_name": file_name,
                    "error": str(e)
                })

    return results

def summarize_algorithm_performance(results):
    df = pd.DataFrame(results)

    # Remove errored runs
    if "error" in df.columns:
        df = df[df["error"].isna()]

    # Group by algorithm name and compute averages
    summary = df.groupby("name").agg(
        avg_total_distance=("total_distance", "mean"),
        avg_execution_time=("execution_time", "mean"),
        num_instances=("instance_file", "count")
    ).reset_index()

    summary = summary.sort_values(by="avg_total_distance")  # Sort by best distance

    return summary

if __name__ == '__main__':
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)  # Optional: Adjust display width for wide DataFrames
    pd.set_option('display.max_colwidth', None)  # Optional: Prevent truncation of column content
    results = run_all_instances_in_directory("data/Vrp-Set-A/A", visualize=False, stdout=True)
    summary_df = summarize_algorithm_performance(results)
    print(summary_df)
