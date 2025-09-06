"""
Script to collect and process metrics from multiple JSON files created 
during running the agents.
"""
import argparse
import os
import json

import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

METRIC_FILE_COLS = ['metric_name', 'metric_type', 'default_value', 'required']

plt.style.use(['./colors.mplstyle', './plots.mplstyle'])

def verify_metric_file(mtc: pd.DataFrame):
    """
    Verify the metrics to collect file for correct formatting and values.

    Args:
        mtc:
            Pandas DataFrame containing the metrics to collect.
        
    Raises:
        ValueError:
            If the DataFrame is empty, does not contain the required columns,
            or contains invalid values in the 
            'metric_type' or 'required' columns.
    """
    if mtc.empty:
        raise ValueError(
            """
            The metrics to collect file is empty or not formatted correctly.
            """
            )
    if not all(col in mtc.columns for col in METRIC_FILE_COLS):
        print(mtc.columns)
        raise ValueError(
            """
            The metrics to collect file must contain the columns:
            metric_name, metric_type, default_value, required.
            """
            )

    for _, row in mtc.iterrows():
        if row['metric_type'] not in ['add', 'append','add_b']:
            raise ValueError(
                f"""
                Invalid metric type '{row['metric_type']}'
                for metric '{row['metric_name']}'.
                Must be 'add', 'add_b' or 'append'.
                """
                )
        if row['required'] not in [True, False]:
            raise ValueError(
                f"""Invalid required value '{row['required']}'
                for metric '{row['metric_name']}'.
                Must be True or False.
                """
                )
        if row['default_value'] is None and row['required'] is False:
            raise ValueError(
                f"""Metric '{row['metric_name']}' is not required
                but has no default value.
                Please provide a default value or set 'required' to True.
                """
                )
        if row['default_value'] is not None and row['required'] is True:
            print(
                  f"""
                  Warning: Metric '{row['metric_name']}' has a default value set
                  but is marked as required.
                  This may lead to unexpected behavior.
                  """
                  )


def combine_metric_files(
        files: list[str],
        mtc: pd.DataFrame,
        exclusion_criteria: dict
        )-> tuple[pd.DataFrame, dict, bool]:
    """
    Combine multiple metric files into a single DataFrame for additive metrics
    and a dictionary for append metrics.

    Args:
        files:
            List of file paths to the metric files to combine.
        mtc:
            Pandas DataFrame containing the metrics to collect.
        exclusion_criteria:
            Dictionary containing the exclusion criteria for the metrics.
    Returns:
        df_add:
            DataFrame containing the combined additive metrics.
        combined_dict_append:
            Dictionary containing the combined append metrics.
        skip:
            Boolean indicating whether to skip due to missing required metrics.

    """
    combined_dict_add = {}
    combined_dict_append = {}
    skip = False

    for file in files:
        print(f'Processing file: {file}')
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for _, row in mtc.iterrows():
            metric = row['metric_name']
            type_ = row['metric_type']
            required = row['required']

            if type_ == 'append' and metric not in combined_dict_append:
                combined_dict_append[metric] = []

            if metric in data:
                if type_ == 'add':
                    if metric in combined_dict_add:
                        combined_dict_add[metric] += data[metric]
                    else:
                        combined_dict_add[metric] = data[metric]
                elif type_ == 'append':
                    combined_dict_append[metric].extend(data[metric])
                elif type_ == 'add_b':
                    if metric in combined_dict_add:
                        if data[metric]:
                            combined_dict_add[metric] += 1
                    else:
                        if data[metric]:
                            combined_dict_add[metric] = 1
                        else:
                            combined_dict_add[metric] = 0


    # Check for metrics that are missing and handle required/default values
    for _, row in mtc.iterrows():
        metric = row['metric_name']
        type_ = row['metric_type']
        required = row['required']
        default_value = row['default_value']

        if (metric not in combined_dict_add
            and metric not in combined_dict_append):
            if required:
                print(
                    f"""
                    Warning: Metric '{metric}' is required
                    but not found in file '{files}'. Skipping this run.
                    """
                    )
                skip = True
            elif type_ == 'add':
                combined_dict_add[metric] = default_value
            elif type_ == 'append':
                combined_dict_append[metric] = [default_value]
            elif type_ == 'add_b':
                combined_dict_add[metric] = default_value
    
    exclusion_criteria = exclusion_criteria.get('list', [])
    for ec in exclusion_criteria:
        print(f'Checking exclusion criteria: {ec}')
        ex_metric = ec['metric']
        if ex_metric not in combined_dict_add:
            print(f"Exclusion metric {ex_metric} not found in data")
            continue
        ex_type = ec['type']
        ex_value = ec['value']
        value = combined_dict_add[ex_metric]
        if ex_type == '<':
            if value < ex_value:
                skip = True
                print(f"Exclusion criteria met for {ex_metric}: {value} < {ex_value}")
                break
        elif ex_type == '>':
            if value > ex_value:
                skip = True
                print(f"Exclusion criteria met for {ex_metric}: {value} > {ex_value}")
                break
        elif ex_type == '==':
            if value == ex_value:
                skip = True
                print(f"Exclusion criteria met for {ex_metric}: {value} == {ex_value}")
                break

    # Convert combined_dict_add to a single-row DataFrame
    if combined_dict_add:
        df_add = pd.DataFrame([combined_dict_add])
    else:
        df_add = pd.DataFrame()

    return df_add, combined_dict_append, skip



def correlate_metrics(data_add: pd.DataFrame, work_dir: str):
    """
    Create a correlation matrix for the additive metrics and save it as image.

    Args:
        data_add:
            Pandas DataFrame containing the additive metrics.
        work_dir:
            Directory where the correlation matrix image will be saved.
    """
    if data_add.empty:
        print('No additive metrics to correlate.')
        return

    correlation_matrix = data_add.corr()

    plt.figure(figsize=(14, 12))
    ax = sns.heatmap(correlation_matrix,
                     cmap = 'coolwarm',
                     annot = False,
                     fmt = '.2f',
                     square = True,
                     cbar_kws = {'shrink': 0.75},
                     vmin = -1,  # Set minimum of color scale
                     vmax = 1,   # Set maximum of color scale
                     xticklabels = True,
                     yticklabels = True
                     )

    ax.set_xticklabels(ax.get_xticklabels(), rotation=90,
                        ha='center', fontsize=15)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=15)
    ax.figure.axes[-1].yaxis.label.set_size(12)  # Colorbar label
    ax.figure.axes[-1].tick_params(labelsize=10)  # Colorbar ticks

    ax.invert_yaxis()

    plt.title('Correlation Matrix of Additive Metrics', fontsize=14, pad=20)
    plt.tight_layout()

    correlation_matrix_file = os.path.join(work_dir, 'correlation_matrix.png')
    plt.savefig(correlation_matrix_file, dpi=300)
    plt.close()
    print(f'Correlation matrix saved to {correlation_matrix_file}')

    return correlation_matrix


def histogram_metrics(data_add: pd.DataFrame, work_dir: str):
    """
    Create histograms for each additive metric and save them as images.

    Args:
        data_add:
            Pandas DataFrame containing the additive metrics.
        work_dir:
            Directory where the histogram images will be saved.
    """
    if data_add.empty:
        print('No additive metrics to plot histograms.')
        return

    for column in data_add.columns:
        plt.figure()
        data_add[column].hist(bins=20, edgecolor='black')
        plt.title(f'Histogram of {column}')
        plt.xlabel(column)
        plt.ylabel('Frequency')
        histogram_file = os.path.join(work_dir, f'histogram_{column}.png')
        plt.savefig(histogram_file)
        plt.close()
        print(f'Histogram for {column} saved to {histogram_file}')


def main(work_dir: str, metrics_to_collect_file: str, strict=False, exclusion_criteria_file=None, histogram=False):
    """
    Collect and process metrics from multiple JSON files created
    during running the agents.

    Args:
        work_dir:
            Directory where the folders containing metric files are stored
            and the results will be saved.
            Files in subfolders starting with 'metrics_' will be processed.
        metrics_to_collect_file:
            Path to the CSV file containing the metrics to collect.
            The file should contain columns: metric_name, metric_type,
            default_value, required.
        strict:
            If True, only JSON files will be processed.
        exclusion_criteria_file:
            Path to a JSON file containing exclusion criteria.
    Raises:
        FileNotFoundError:
            If the specified work directory does not exist.
        ValueError:
            If the metrics to collect file is empty or not formatted correctly.
    """
    if not os.path.exists(work_dir):
        raise FileNotFoundError(
            f'The specified work directory does not exist: {work_dir}'
            )

    mtc = pd.read_csv(metrics_to_collect_file)
    verify_metric_file(mtc)
    if exclusion_criteria_file:
        with open(exclusion_criteria_file, 'r', encoding='utf-8') as f:
            ec = json.load(f)
    else:
        ec = {'list': []}
    print(f'Exclusion criteria loaded: {ec}')

    additive_metrics = mtc.loc[mtc['metric_type'].isin(['add','add_b'])]
    data_add = pd.DataFrame(columns=additive_metrics['metric_name'].tolist())
    data_append = {}
    skip_cnt = 0
    total_cnt = 0

    for run in os.listdir(work_dir):
        if not os.path.isdir(os.path.join(work_dir, run)):
            print(f'Skipping non-directory item: {run}')
            continue

        total_cnt += 1
        run_path = os.path.join(work_dir, run)

        metric_files = [os.path.join(run_path, f) for f
                        in os.listdir(run_path) if f.startswith('metrics_')
                        and (f.endswith('.json') or not strict)]

        if not metric_files:
            print(f'No metric files found in run: {run}')
            continue

        df_add, dict_comb, skip = combine_metric_files(metric_files, mtc, ec)

        if not skip:
            # Ensure columns are aligned before appending
            row = df_add.reindex(columns=data_add.columns, fill_value=None)
            data_add = pd.concat([data_add, row], ignore_index=True)
            data_append[run] = dict_comb
        else:
            print(f'Skipping run {run} due to missing required metrics.')
            skip_cnt += 1


    output_file_add = os.path.join(work_dir, 'additive_metrics.csv')
    data_add.to_csv(output_file_add, index=False)
    print(f'Additive metrics saved to {output_file_add}')

    if histogram:
        correlate_metrics(data_add, work_dir)
        histogram_metrics(data_add, work_dir)


    output_file_append = os.path.join(work_dir, 'combined_metrics.json')
    with open(output_file_append, 'w', encoding='utf-8') as f:
        json.dump({'additive': data_add.to_dict(orient='records'),
                   'append': data_append,
                   'general': {
                       'total_runs': total_cnt,
                       'skipped_runs': skip_cnt
                   }
                   },
                    f,
                    indent=4
                    )

    print(f'Combined metrics saved to {output_file_append}')



if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Collect metrics from AI agent evaluations.'
        )
    parser.add_argument(
        '-wd',
        '--work_dir',
        type=str,
        required=True,
        help='Directory where the evaluation results are stored.',
    )
    parser.add_argument(
        '-mtcf',
        '--metrics_to_collect_file',
        type=str,
        required=True,
        help='CSV file containing columns: ' \
        'metric_name, metric_type, default_value, required',
    )
    parser.add_argument(
        '-s',
        '--strict',
        action='store_true',
        help='If set, only JSON files will be processed.'
    )
    parser.add_argument(
        '-ecf',
        '--exclusion_criteria_file',
        type=str,
        help='Path to a .json with exclusion criteria'
    )
    parser.add_argument(
        '-his',
        '--histogram',
        action='store_true',
        help='If set, generate histograms for the metrics.'
    )

    args = parser.parse_args()
    main(args.work_dir, args.metrics_to_collect_file, args.strict, args.exclusion_criteria_file, args.histogram)
