from tools.tool import Tool
from utility.md_reporter import MDReporter
from utility.evaluation_functions import evaluate_scores

class WriteFinalReport(Tool):
    def __init__(self, questions_to_be_answered: list[str], work_dir: str, reporter: MDReporter, eval_file: str | None = None):
        name = "write_final_report"

        expanded_questions = ""
        for q in questions_to_be_answered:
            expanded_questions += f"Question: {q}\n"
        parameter_report = Tool.build_parameter_schema(
            "report",
            f"""The final report to be written in markdown.
            When referring to images, include the image filename in the format
            ![image_name](image_name).
            The report should document what you have done (in detail!),
            why you did it, and what you have learned.
            The final report has to be written in a way such that an external
            reader can understand what you have done and why.
            Also include sources and references!
            Please answer also the following questions:
            {expanded_questions}""",
            "string"
        )
        params = [parameter_report]
        self.eval_file = None
        fn = self.write_final_report

        if eval_file:
            self.eval_file = eval_file
            fn = self.write_final_report2
            parameter_score_file = Tool.build_parameter_schema(
                "score_file",
                """The file containing evaluation scores to be included in the
                report, first column needs to be index column.
                File needs to be sorted by index""",
                "string"
            )
            params.append(parameter_score_file)
            parameter_score_col = Tool.build_parameter_schema(
                "score_col",
                """The column name in the evaluation file with the scores""",
                "string",
            )
            params.append(parameter_score_col)


        schema = Tool.build_function_schema(
            name,
            "Writes a final report in markdown format. If asked for scores please provide them",
            params
        )


        super().__init__(name, schema, fn, reporter)
        self.work_dir = work_dir


    def write_final_report(self, report: str) -> str:
        """
        Writes the final report to a markdown file in the specified work directory.

        Args:
            report (str): The content of the final report to be written.

        Returns:
            str: A message indicating the success of the operation.
        """
        report_path = self.work_dir + "final_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        return f"Final report written to {report_path}"
    
    def write_final_report2(self, report: str, score_file: str, score_col: str) -> str:
        """
        Writes the final report to a markdown file in the specified work directory
        and evaluates scores.

        Args:
            report (str): The content of the final report to be written.
            eval_file (str): The file containing evaluation scores.
            score_col (str): The column name in the evaluation file with the scores.

        Returns:
            str: A message indicating the success of the operation.
        """
        report_path = self.work_dir + "final_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        try:
            auc, m_sic, tpr_ms = evaluate_scores(self.work_dir, score_file, score_col, self.eval_file)
        except Exception as e:
            self.reporter.report_metrics("auc_err", f"Error evaluating scores: {e}", mode="overwrite")
            auc = None
            m_sic = None
            tpr_ms = None
        if auc is not None:
            self.reporter.report_metrics("auc", auc, mode="overwrite")
            self.reporter.report_metrics("max_sic", m_sic, mode="overwrite")
            self.reporter.report_metrics("score_file", score_file, mode="overwrite")
            self.reporter.report_metrics("score_col", score_col, mode="overwrite")
            self.reporter.report_metrics("tpr_max_sic", tpr_ms, mode="overwrite")

        return f"Final report written to {report_path}"

