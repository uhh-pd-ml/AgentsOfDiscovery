"""
Script to compare batches of metrics and generate histograms or
vertical scatter plots. It reads multiple CSV files containing
metrics, processes them, and saves the visualizations in a specified
directory. 
The CSV files can be generated  with the metric_collector script/
"""
import argparse
import json

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import vertical_scatter
from vertical_scatter_advanced import vertical_scatter as vs

plt.style.use(['./colors.mplstyle', './plots.mplstyle'])

def compare_batches(
        batches: list[pd.DataFrame],
        out_dir: str,
        labels: list[str] | None = None
        ):
    """
    Generates histograms for each metric in the provided batches.

    Args:
        batches:
            List of Pandas DataFrames, each representing a batch of metrics.
        out_dir:
            Directory where the output histograms will be saved.
        labels:
            Optional list of labels for each batch. If not provided, defaults to
            'Batch 0', 'Batch 1', etc.
    """
    if out_dir[-1] != '/':
        out_dir += '/'

    metrics = set()
    for batch in batches:
        metrics.update(batch.keys())

    for metric in metrics:
        plt.figure(figsize=(10, 6))
        # Concatenate all values for this metric to compute common bin edges
        all_values = []
        for batch in batches:
            if metric not in batch:
                print(
                    f"""
                    Warning: Metric '{metric}' not found in one of the batches.
                    Skipping.
                    """
                    )
                continue
            all_values.extend(batch[metric].dropna().tolist())

        range_ = np.ptp(all_values)  # Range of all values
        if range_ == 0:
            bins = [all_values[0] - 0.5, all_values[0] + 0.5]
            xtics = [all_values[0]]
            xlim = (all_values[0] - 1, all_values[0] + 1)
        else:
            # Set dist to next highest power of 10 <= range / 2
            dist = 10 ** int(np.floor(np.log10(range_/2)))
            epsilon = 1e-2
            bins = np.arange(min(all_values) - dist / 2,
                             max(all_values) + dist, dist)
            xtics = np.arange(min(all_values),
                              max(all_values) + dist + epsilon, dist)
            xlim = (min(all_values) - dist , max(all_values) + dist )

        for i, batch in enumerate(batches):
            if metric not in batch:
                print(
                    f"""
                    Warning: Metric '{metric}' not found in batch {i}. Skipping.
                    """
                    )
                continue
            label = labels[i] if labels and i < len(labels) else f'Batch {i}'
            plt.hist(batch[metric], bins=bins, alpha=0.5, label=label)

        plt.xticks(xtics)
        plt.xlim(xlim)
        plt.title(f'Histogram of {metric}')
        plt.xlabel('Value')
        plt.ylabel('Frequency')
        plt.legend()
        plt.grid(True)
        plt.savefig(f'{out_dir}histogram_{metric}.png')
        plt.close()

    print('Histograms generated for all metrics.')

def compare_batches_2(
        batches: list[pd.DataFrame],
        out_dir: str,
        labels: list[str] | None = None
        ):
    """
    Generates vertical scatter plots for each metric in the provided batches.

    Args:
        batches:
            List of Pandas DataFrames, each representing a batch of metrics.
        out_dir:
            Directory where the output scatter plots will be saved.
        labels:
            Optional list of labels for each batch. If not provided, defaults to
            'Batch 0', 'Batch 1', etc.
    """
    if not labels:
        labels = [f'Batch {i+1}' for i in range(len(batches))]

    metrics = set()
    for label, batch in zip (labels,batches):
        metrics.update(batch.keys())

        batch['category'] = label  # Add a category column for vertical scatter

    all_data = pd.concat(batches, ignore_index=True)

    for metric in metrics:
        fig, _ = vertical_scatter.vertical_scatter(all_data, metric)

        fig.savefig(f'{out_dir}vertical_scatter_{metric}.png')
        plt.close(fig)

def compare_batches_3(
        batches: list[pd.DataFrame],
        out_dir: str,
        labels: list[str] | None = None,
        advanced_parameter_list: list[dict] = None,
        general_settings: dict = None,
        skip_missing_ap: bool = False
        ):
    """
    Generates advanced vertical scatter plots for each metric in the provided batches.

    Args:
        batches:
            List of Pandas DataFrames, each representing a batch of metrics.
        out_dir:
            Directory where the output scatter plots will be saved.
        labels:
            Optional list of labels for each batch. If not provided, defaults to
            'Batch 0', 'Batch 1', etc.
        advanced_parameters:
            Optional dictionary with advanced parameters for the vertical scatter plot.
    """
    if not labels:
        labels = [f'Batch {i+1}' for i in range(len(batches))]

    metrics = set()

    def sorting_fun(category):
        try:
            key = labels.index(category)
        except ValueError:
            print(f"Warning: Category '{category}' not found in labels."
                  f" Using default index.")
            key = 0
        return key

    for label, batch in zip (labels,batches):
        metrics.update(batch.keys())

        batch['category'] = label  # Add a category column for vertical scatter

    all_data = pd.concat(batches, ignore_index=True)

    for metric in metrics:
        advanced_parameters = None
        if advanced_parameter_list:
            for apd in advanced_parameter_list:
                if metric in apd['metrics']:
                    advanced_parameters = apd['parameters']
                    break
            if skip_missing_ap and advanced_parameters is None:
                continue
        else:
            advanced_parameters = None

        fig, _, meta = vs(all_data,
                    metric,
                    advanced_parameters=advanced_parameters,
                    sorting_function=sorting_fun,
                    general_settings=general_settings
                    )

        fig.savefig(f'{out_dir}vertical_scatter_{metric}.png', dpi=600)
        plt.close(fig)

        meta.to_csv(f'{out_dir}data_{metric}.csv')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Compare batches and generate histograms for each metric.')
    parser.add_argument(
        '-bs',
        '--batches',
        type=str,
        nargs='+',
        help='List of batches as CSV files'
        )
    parser.add_argument(
        '-ls',
        '--labels',
        type=str,
        nargs='+',
        help='Labels for the batches (optional)',
        default=None
        )
    parser.add_argument(
        '-od',
        '--out_dir',
        type=str,
        help='Where the outputs should be saved'
        )
    parser.add_argument(
        '-ap',
        '--advanced_parameters_file',
        type=str,
        help='Advanced parameters for vertical scatter plots as JSON File'
        )

    args = parser.parse_args()
    bs = []

    if args.labels and len(args.batches) != len(args.labels):
        raise ValueError('Number of batches must match number of labels.')

    for batch_file in args.batches:
        try:
            print(f'Reading batch file: {batch_file}')
            b = pd.read_csv(batch_file)
            bs.append(b)
        except (FileNotFoundError, pd.errors.ParserError) as e:
            print(f'Error reading {batch_file}: {e}')

    od = args.out_dir
    if not od:
        od = './'

    if od[-1] != '/':
        od += '/'
    if args.advanced_parameters_file:
        try:
            with open(args.advanced_parameters_file, 'r') as f:
                advanced_parameters = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f'Error reading advanced parameters file: {e}')
            advanced_parameters = None
    else:
        advanced_parameters = None
    if advanced_parameters:
        if 'general_settings' in advanced_parameters:
            general_settings = advanced_parameters['general_settings']
        else:
            general_settings = None
        if 'list' in advanced_parameters:
            advanced_parameters = advanced_parameters['list']
        
    
    compare_batches_3(bs, od, labels=args.labels,
                      advanced_parameter_list=advanced_parameters,
                      general_settings=general_settings)

    # compare_batches_2(bs, od, labels=args.labels)
