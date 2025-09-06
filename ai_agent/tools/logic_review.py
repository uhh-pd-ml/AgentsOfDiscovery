"""
Tool that allows to review statements based on provide program outputs. 
"""
import os

from tools.tool import Tool
from utility.md_reporter import MDReporter
from agents.logic_reviewer import LogicReviewer


class LogicReview(Tool):
    """
    Tool that allows to review statements based on provided program outputs.

    Attributes:
        model:
            The LLM model used for the logic reviewer.
        work_dir:
            The directory where the logic reviewer can find necessary files.
        name:
            The name of the tool.
        schema:
            The schema defining the tool's parameters and return type.
        function:
            The function that implements the tool's functionality has to 
            return a string containing the result readable for a LLM.
        reporter:
            An instance of MDReporter for reporting metrics.
    Methods:
        logic_review(statement: str) -> str:
            Requests the review of a statement based on program outputs.
    """
    def __init__(self, model, work_dir: str, reporter: MDReporter):
        """
        Initializes the LogicReview tool.

        Args:
            model:
                The LLM model used for the logic reviewer.
            work_dir:
                The directory where the logic reviewer can find necessary files.
            reporter:
                An instance of MDReporter for reporting metrics.
        """
        name = "logic_review"
        parameter_statement = Tool.build_parameter_schema(
            "statement",
            """
            The statement to be reviewed, include relevant filenames that helped
            to derive the statement.
            """,
            "string"
        )
        schema = Tool.build_function_schema(
            name,
            """
            Requests the review of statements based on program outputs
            (text files, images).
            """,
            [
                parameter_statement,
            ]
        )
        super().__init__(name, schema, self.logic_review, reporter)
        self.model = model
        self.work_dir = work_dir

    def logic_review(self, statement: str) -> str:
        """
        Requests the review of a statement based on program outputs.
        
        Args:
            statement:
                The statement to be reviewed, include relevant filenames that
                helped to derive the statement.
        Returns:
            A string containing the result of the review, readable for a LLM.
        """
        i = 0
        while os.path.exists(
            os.path.join(self.work_dir, f'logic_review_{i}.md')
            ):
            i += 1

        filename = f'logic_review_{i}.md'
        reviewer = LogicReviewer(
            self.model,
            MDReporter(self.work_dir, filename=filename),
            self.work_dir)

        message = {
            "role": "user",
            "content": statement,
        }

        feedback = reviewer.call([message])

        return feedback
