"""
Tool that allows the Agent to submit numeric values for questions.
"""
import json

from tools.tool import Tool
from utility.md_reporter import MDReporter


class SubmitNumericValues(Tool):
    """
    A tool that allows the Agent to submit numeric values for questions.

    Attributes:
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
    def __init__(self, expected_values_file: str, reporter: MDReporter):
        """
        Initializes the SubmitNumericValues tool.
        
        Args:
            expected_values_file:
                The path to the file containing information about which values
                are expected to be submitted. 
                The file has to be a JSON file with the following structure:
                {
                    "questions": [
                        {
                            "question_identifier": "q1",
                            "question": "What is the value of question 1?"
                        },
                        ...
                    ]
                }
            reporter:
                An instance of MDReporter for reporting metrics.
        """

        name = 'submit_numeric_values'

        with open(expected_values_file, 'r', encoding='utf-8') as f:
            d = json.load(f)

        parameters = []

        for q in d['questions']:
            parameters.append(Tool.build_parameter_schema(
                q['question_identifier'],
                q['question'],
                'number'
            ))

        schema = Tool.build_function_schema(
            name,
            ' This function is used to submit numeric parameters to questions',
            parameters
        )


        super().__init__(name, schema, self.submit_numeric_value, reporter)

    def submit_numeric_value(self, **kwargs: float):
        for k, val in kwargs.items():
            self.reporter.report_metrics(k,val, mode='overwrite')
        return 'Values successfully submitted'
