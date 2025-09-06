import json
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, roc_auc_score

SIC_UNCERTAINTY = 0.1

def calc_sic_roc_auc(y_true, y_scores):

    required_bkg_events = 1/(2* SIC_UNCERTAINTY)
    fpr_cutoff = required_bkg_events / len(y_true)

    fpr, tpr, _ = roc_curve(y_true, y_scores)
    fpr_nonzero = np.delete(fpr, np.argwhere(fpr == 0))
    tpr_nonzero = np.delete(tpr, np.argwhere(fpr == 0))

    # Filter out FPR values that are below the cutoff
    valid_indices = fpr_nonzero >= fpr_cutoff
    fpr_nonzero = fpr_nonzero[valid_indices]
    tpr_nonzero = tpr_nonzero[valid_indices]

    auc = roc_auc_score(y_true, y_scores)

    sic = tpr_nonzero / fpr_nonzero**0.5  # SIC = TPR / FPR^0.5
    max_sic = np.max(sic)
    max_sic_tpr= tpr_nonzero[np.where(sic==max_sic)[0][0]]
    
    return sic, fpr_nonzero, tpr_nonzero, auc, max_sic, max_sic_tpr

def plot_background_rejection(fpr, tpr, auc,  label, work_dir):
    random_rejection = [1 / (x + 1e-100) for x in np.linspace(0, 1, len(fpr))] 

    plt.figure(figsize=(5, 5))
    plt.plot(np.linspace(0, 1, len(fpr)), random_rejection, 'k--', label='Random')
    plt.plot(tpr, 1 / fpr, label=f'{label} (AUC: {auc:.2f})')
    plt.xlim([-0.1, 1.1])
    plt.ylim([0.5, 10**5])
    plt.yscale('log')
    plt.ylabel('1 / False Positive Rate')
    plt.xlabel('True Positive Rate')
    plt.title(f'Background Rejection Curve - {label}')
    plt.legend(loc='upper right')
    plt.savefig(f'{work_dir}/background_rejection_curve.png', dpi=512/5)
    plt.close()

def plot_sic(tpr, sic, label, work_dir):
    random =  np.sqrt(np.linspace(0, 1, len(tpr)) )
    plt.figure(figsize=(5, 5))
    plt.plot(np.linspace(0, 1, len(tpr)), random, 'k--', label='Random')
    plt.plot(tpr, sic, label=label)
    plt.xlim([-0.1, 1.1])
    plt.ylim([0, np.max(sic) * 1.1])
    plt.xlabel('TPR')
    plt.ylabel('SIC')
    plt.title(f'SIC Curve - {label}')
    plt.legend(loc='upper right')
    plt.savefig(f'{work_dir}/sic_curve.png', dpi=512/5)
    plt.close()


def evaluate_scores(work_dir, score_file, col_name,  label_file, plot_label=None):
    if plot_label is None:
        eval_params = load_eval_parameters(label_file)
        label_file = eval_params['label_file']
        plot_label = eval_params['plot_label']

    print(f"Evaluating scores from {work_dir + score_file} with column {col_name} against labels in {label_file}")

    scores = pd.read_csv(work_dir + score_file)
    labels = pd.read_csv(label_file)

    # Ensure the scores and labels are aligned
    if not scores.iloc[:, 0].equals(labels.iloc[:, 0]):
        return

    y_true = labels.iloc[:, 1].values
    y_scores = scores[col_name]
    sic, fpr, tpr, auc, m_sic, tpr_ms = calc_sic_roc_auc(y_true, y_scores)
    plot_background_rejection(fpr, tpr, auc, plot_label, work_dir)
    plot_sic(tpr, sic, plot_label, work_dir)

    return auc, m_sic, tpr_ms

def load_eval_parameters(eval_params_file):
    with open(eval_params_file, 'r', encoding='utf-8') as f:
        eval_params = json.load(f)
    return eval_params


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Evaluate scores and plot results.')
    parser.add_argument('--work_dir', type=str, required=True, help='Working directory containing score files')
    parser.add_argument('--score_file', type=str, required=True, help='CSV file with scores')
    parser.add_argument('--col_name', type=str, required=True, help='Column name in the score file to evaluate')
    parser.add_argument('--label_file', type=str, required=True, help='CSV file with labels')
    parser.add_argument('--plot_label', type=str, default=True, help='Label for the plots')

    args = parser.parse_args()
    
    auc, m_sic, tpr_ms = evaluate_scores(args.work_dir, args.score_file, args.col_name, args.label_file, args.plot_label)

    print(f"AUC: {auc:.4f}, Max SIC: {m_sic:.4f} at TPR: {tpr_ms:.4f}")

    

    