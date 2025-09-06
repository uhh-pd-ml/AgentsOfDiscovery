""" 
A tool that allows the Agent to get feedback on the scores it has generated.
"""
import os

from tools.tool import Tool
from utility.md_reporter import MDReporter
from utility.evaluation_functions import evaluate_scores

import pandas as pd

SCORE_FILE_NAME = 'scores.csv'

class GetFeedback(Tool):
    """
    A tool that allows the Agent to get feedback on the scores it has generated.

    Attributes:
        work_dir:
            The working directory where the tool will create its output
            directory.
        eval_file:
            The path to the file containing evaluation information for the
            scores.
        name:
            The name of the tool.
        schema:
            The schema defining the tool's parameters and return type.
        function:
            The function that implements the tool's functionality has to 
            return a string containing the result readable for a LLM.
        reporter:
            An instance of MDReporter for reporting metrics.
    """


    def __init__(self,
                 work_dir: str,
                 reporter: MDReporter,
                 eval_file: str,
                 ):
        """
        Initializes the GetFeedback tool.
        
        Args:
            work_dir:
                The working directory where the tool will create its output
                directory.
            reporter:
                An instance of MDReporter for reporting metrics.
            eval_file:
                The path to the file containing evaluation information for the
                scores. The eval file has to be a JSON file with the following 
                structure:
                {
                    "label_file": "/path/to/truth/labels.csv",
                    "plot_label": "Label in the plot",
                    "allow_feedback": true 
                }
                The last field is optional, default is false. This tool can only
                be used if allow_feedback is true.
                The score file needs to be a CSV file with the first column
                being the index column and the second column being the scores.
        """
        name = 'get_feedback'
        parameter_score_file = Tool.build_parameter_schema(
            'score_file',
            """
            The file containing evaluation scores to be checked,
            first column needs to be index column.
            File needs to be sorted by index
            """,
            'string'
        )
        parameter_score_col = Tool.build_parameter_schema(
            'score_col',
            'The column name in the evaluation file with the scores',
            'string',
        )
        params = [parameter_score_file, parameter_score_col]

        schema = Tool.build_function_schema(
            name,
            """
            Get feedback on scores. Feedback includes AUC, max SIC
            and TPR at max SIC (Significance improvement characteristic),
            as well as corresponding plots.
            """,
            params
        )

        super().__init__(name, schema, self.get_feedback, reporter)
        self.eval_file = eval_file

        self.work_dir = work_dir if work_dir.endswith('/') else work_dir + '/'
        self.counter = 0

    def get_feedback(self, score_file: str, score_col: str) -> str:
        """
        Get feedback on the scores provided in the score file.
        Args:
            score_file:
                The file containing evaluation scores to be checked,
                first column needs to be index column.
                File needs to be sorted by index.
            score_col:
                The column name in the evaluation file with the scores.
        Returns:
            A string containing the feedback on the scores, including AUC,
            max SIC, TPR at max SIC, and paths to the generated plots.
        """
        sub_dir = f"feedback/r_{self.counter}/"
        directory = f"{self.work_dir}{sub_dir}"
        self.counter += 1

        if not os.path.exists(directory):
            os.makedirs(directory)

        try:
            score_df = pd.read_csv(self.work_dir + score_file)
            if score_col not in score_df.columns:
                return f"""
                Column '{score_col}' not found in the score file '{score_file}'.
                """
        except Exception as e:
            self.reporter.report_metrics('feedback_error', 1, mode='add')
            return f'The score file "{score_file}" could not be read: {e}'

        score_df.to_csv(directory + SCORE_FILE_NAME)

        auc = None
        m_sic = None
        tpr_ms = None
        try:
            auc, m_sic, tpr_ms = evaluate_scores(directory, SCORE_FILE_NAME,
                                             score_col, self.eval_file)
        except TypeError:
            self.reporter.report_metrics('feedback_error', 1, mode='add')

        if auc is None:
            self.reporter.report_metrics('feedback_error', 1, mode='add')
            return """
            Error evaluating scores. Please check the score file and labels.
            Ensure the score file is a CSV file containing a score for every
            index in the label file, sorted by index.
            """

        self.reporter.report_metrics('auc_feedback', auc, mode='append')
        self.reporter.report_metrics('max_sic_feedback', m_sic, mode='append')
        self.reporter.report_metrics('tpr_max_sic_feedback',
                                                tpr_ms, mode='append')

        feedback = f"""
            Feedback for scores in {score_file}:
            AUC: {auc:.4f}
            Max SIC: {m_sic:.4f}
            TPR at Max SIC: {tpr_ms:.4f}
            Plots:\n
            {sub_dir}background_rejection_curve.png
            {sub_dir}sic_curve.png
            """
        self.reporter.report_metrics('feedback_success', 1, mode='add')

        return feedback
