import argparse
import os

import pandas as pd



def parse_args():
    parser = argparse.ArgumentParser(
        description='Collect data from different files to create a table')
    parser.add_argument('--work_dir','-wd', type=str, help='Working directory')
    parser.add_argument('--table_name', '-tn', type=str, help='Output file name')
    parser.add_argument('--columns', '-c', type=str, nargs='+', help='List of columns to include in the format <metric_name>.<sub_metric>')
    parser.add_argument('--key_col', '-kc', type=str, default='category', help='Key column to align the table, has to be existent in every data file')
    return parser.parse_args()

def extract_metric_name_name(filename: str) -> str:
    name = filename.split('.')[0]
    name = name.split('_')[1:]
    name = '_'.join(name)
    return name

def get_data_files(work_dir):
    data_files = []
    metrics = set()
    for root, _, files in os.walk(work_dir):
        for file in files:
            if file.startswith('data') and file.endswith('.csv'):
                name = extract_metric_name_name(file)
                data_files.append({
                    'metric': name,
                    'path': os.path.join(root, file)
                })
                metrics.add(name)
    return data_files, metrics

def extract_columns(raw_columns: list[str])-> list[dict[str, str]]:
    columns = []
    metrics = set()
    for rc in raw_columns:
        parts = rc.split('.')
        if len(parts) == 2:
            columns.append({'metric': parts[0], 'sub_metric': parts[1]})
            metrics.add(parts[0])
        else:
            raise ValueError(f"Invalid column format: {rc}. Expected format is <metric_name>.<sub_metric>")
    return columns, metrics

def main():
    args = parse_args()
    data_files, metrics = get_data_files(args.work_dir)
    columns, col_metrics = extract_columns(args.columns)

    table = pd.DataFrame()

    for d in data_files:
        if d['metric'] not in col_metrics:
            continue
        print(f"Processing {d['metric']} from {d['path']}")
        for c in columns:
            if c['metric'] == d['metric']:
                print(f"Adding column {c['metric']}.{c['sub_metric']} from {d['path']}")
                df = pd.read_csv(d['path'])
                if c['sub_metric'] not in df.columns:
                    if f'{c['sub_metric']}.' in df.columns:
                        df[f'{c['sub_metric']}'] = df[f'{c['sub_metric']}.']
                    else:
                        raise ValueError(f"Sub-metric {c['sub_metric']} not found in {d['path']}.")
                if args.key_col not in df.columns:
                    raise ValueError(f"Key column {args.key_col} not found in {d['path']}.")
                # temp_df = pd.DataFrame()
                # temp_df['key'] = df[args.key_col]
                # temp_df.set_index('key', inplace=True)
                # temp_df[f'{c['metric']}_{c['sub_metric']}'] = df[c['sub_metric']]
                print(df.head())
                # print(temp_df.head())


                # table = pd.concat([table, temp_df], axis=1, join='outer')
                if not table.empty:
                    table = table.merge(df[[args.key_col, c['sub_metric']]], on=args.key_col, how='outer' ).rename(columns={c['sub_metric']: f'{c["metric"]}_{c["sub_metric"]}'})      
                else:
                    table = df[[args.key_col, c['sub_metric']]].rename(columns={c['sub_metric']: f'{c["metric"]}_{c["sub_metric"]}'})
                    table.set_index(args.key_col, inplace=True)

    table.to_csv(f'{args.work_dir}/{args.table_name}.csv', index=False)

if __name__ == "__main__":
    main()