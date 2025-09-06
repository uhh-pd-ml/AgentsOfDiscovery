from tools.tool import Tool
from utility.md_reporter import MDReporter

class WriteCodeReview(Tool):
    def __init__(self, reviewer, reporter: MDReporter):
        name = "write_code_review"
        schema = Tool.build_function_schema(
            name,
            "Writes a code review for the provided code and task.",
            [
                Tool.build_parameter_schema(
                    "pass_",
                    "If the code passes the review.",
                    "boolean"
                ),
                Tool.build_parameter_schema(
                    "feedback",
                    "The feedback for the code.",
                    "string"
                )
            ]
        )
        super().__init__(name, schema, self.write_code_review, reporter)

        self.reviewer = reviewer

    def write_code_review(self, pass_: bool, feedback: str) -> str:
        """
        Writes a code review for the provided code and task.
        Args:
            pass_ (bool): If the code passes the review.
            feedback (str): The feedback for the code.
        Returns:
            str: A message indicating whether the code passed the review and the feedback provided.
        """
        self.reviewer.stop = True
        if pass_:
            self.reviewer.pass_ = True
            self.reviewer.feedback = feedback
            return "Code passed the review. Feedback: " + feedback
        else:
            self.reviewer.pass_ = False
            self.reviewer.feedback = feedback
            return "Code did not pass the review. Feedback: " + feedback

