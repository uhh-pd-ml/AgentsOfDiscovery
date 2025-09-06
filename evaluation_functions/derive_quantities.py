import argparse

import pandas as pd
import numpy as np

VALID_OPERATIONS = ['+', '-', '*', '/', 'root', 'log_base', 'ln', 'exp', '**']

def parse_args():
    parser = argparse.ArgumentParser(description="Derive quantities from metrics.")
    parser.add_argument(
        "--metrics_file",
        "-mf",
        type=str,
        required=True,
        help="Path to the metrics file to derive quantities from.",
    )
    parser.add_argument(
        "--output_dir",
        "-od",
        type=str,
        required=True,
        help="Path to the output directory for derived quantities.",
    )
    parser.add_argument(
        "--quantities_file",
        "-qf",
        type=str,
        required=True,
        help="CSV file describing the quantities to derive.",
    )


    return parser.parse_args()

def derive_quantities(metrics_df, quantities_df):
    out_df = pd.DataFrame()

    for _, row in quantities_df.iterrows():
        name = row['name']

        # Helper to parse numeric or string values
        def parse_value(val, is_min=False):
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, str):
                val_strip = val.strip()
                if val_strip.lower() == 'inf':
                    return -np.inf if is_min else np.inf
                try:
                    return float(val_strip)
                except ValueError:
                    return val_strip  # Return as string if not numeric
            return val

        v1 = parse_value(row['name1'])
        v1_min = parse_value(row['min1'], is_min=True)
        v1_max = parse_value(row['max1'])
        if not isinstance(v1_min, (int, float)):
            raise ValueError(f"Invalid min1 value: {v1_min}")
        if not isinstance(v1_max, (int, float)):
            raise ValueError(f"Invalid max1 value: {v1_max}")
        if not (v1_min <= v1_max):
            raise ValueError(f"min1 ({v1_min}) must be less than or equal to max1 ({v1_max}) for {name}.")

        v2 = parse_value(row['name2'])
        v2_min = parse_value(row['min2'], is_min=True)
        v2_max = parse_value(row['max2'])
        if not isinstance(v2_min, (int, float)):
            raise ValueError(f"Invalid min2 value: {v2_min}")
        if not isinstance(v2_max, (int, float)):
            raise ValueError(f"Invalid max2 value: {v2_max}")
        if not (v2_min <= v2_max):
            raise ValueError(f"min2 ({v2_min}) must be less than or equal to max2 ({v2_max}) for {name}.")

        operation = row['operation']
        default = row['default']    

        if name in metrics_df.columns:
            raise ValueError(f"Column '{name}' already exists in metrics_df. Please choose a different name.")
        
        if operation not in VALID_OPERATIONS:
            raise ValueError(f"Invalid operation '{operation}'. Valid operations are: {', '.join(VALID_OPERATIONS)}")
        
        # Prepare v1 and v2 as Series or None
        v1_series = None
        v2_series = None

        if isinstance(v1, str) and v1 in metrics_df.columns:
            v1_series = metrics_df[v1]
        elif isinstance(v1, (int, float)):
            v1_series = pd.Series(v1, index=metrics_df.index)
        elif isinstance(v1,str) and v1 in out_df.columns:
            v1_series = out_df[v1]
        else:
            v1_series = pd.Series(np.nan, index=metrics_df.index)

        if isinstance(v2, str) and v2 in metrics_df.columns:
            v2_series = metrics_df[v2]
        elif isinstance(v2, (int, float)):
            v2_series = pd.Series(v2, index=metrics_df.index)
        elif isinstance(v2, str) and v2 in out_df.columns:
            v2_series = out_df[v2]
        else:
            v2_series = pd.Series(np.nan, index=metrics_df.index)

        # Determine valid mask based on operation
        if operation in ['ln', 'exp']:
            # Only v1 is used
            valid = (v1_series >= v1_min) & (v1_series <= v1_max)
        elif operation in ['root', 'log_base', '/', '**', '+', '-', '*']:
            # Both v1 and v2 are used
            valid = (
                (v1_series >= v1_min) & (v1_series <= v1_max) &
                (v2_series >= v2_min) & (v2_series <= v2_max)
            )
        else:
            # Fallback: require both to be valid if present
            valid = (
                (v1_series >= v1_min) & (v1_series <= v1_max) &
                (v2_series >= v2_min) & (v2_series <= v2_max)
            )

        v1 = v1_series
        v2 = v2_series

        if operation == '+':
            out_df[name] = np.where(valid, v1 + v2, default)
        elif operation == '-':
            out_df[name] = np.where(valid, v1 - v2, default)
        elif operation == '*':
            out_df[name] = np.where(valid, v1 * v2, default)
        elif operation == '/':
            out_df[name] = np.where(valid, v1 / v2, default)
        elif operation == 'root':
            out_df[name] = np.where(valid, np.power(v1, 1 / v2), default)
        elif operation == 'log_base':
            out_df[name] = np.where(valid, np.log(v1) / np.log(v2), default)
        elif operation == 'ln':
            out_df[name] = np.where(valid, np.log(v1), default)
        elif operation == 'exp':
            out_df[name] = np.where(valid, np.exp(v1), default)
        elif operation == '**':
            out_df[name] = np.where(valid, np.power(v1, v2), default)
    return out_df


def main():
    args = parse_args()

    # Load metrics and quantities data
    metrics_df = pd.read_csv(args.metrics_file)
    quantities_df = pd.read_csv(args.quantities_file)

    # Derive quantities
    derived_quantities_df = derive_quantities(metrics_df, quantities_df)

    # Save the derived quantities to the output directory
    output_path = f"{args.output_dir}/derived_quantities.csv"
    derived_quantities_df.to_csv(output_path, index=False)
    print(f"Derived quantities saved to {output_path}")

if __name__ == "__main__":
    main()