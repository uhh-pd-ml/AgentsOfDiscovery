"""
Tool that allows the agent to end the project with a reason.
"""
from tools.tool import Tool
from utility.md_reporter import MDReporter

class EndProject(Tool):
    """
    Tool that allows the agent to end the project with a reason.
    Extends the Tool class.
    
    Attributes:
        stop:
            A boolean indicating whether the project has been marked as 
            finished.
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
    def __init__(self, reporter: MDReporter):
        """
        Initializes the EndProject tool.

        Args:
            reporter (MDReporter):
                An instance of MDReporter for reporting metrics.
        """
        self.name = 'end_project'
        parameter_reason = Tool.build_parameter_schema(
            'reason',
            'The reason for ending the project.',
            'string'
        )
        schema = Tool.build_function_schema(
            self.name,
            """
            Marks the project as finished and provides a reason for its
            termination.
            """,
            [parameter_reason]
        )
        super().__init__(self.name, schema, self.end_project, reporter)
        self.stop = False


    def end_project(self, reason: str) -> str:
        """
        Marks the project as finished and provides a reason for its termination.

        Args:
            reason (str): The reason for ending the project.

        Returns:
            str: A message indicating the project has been finished along with
            the provided reason.
        """

        self.stop = True
        return 'The project was finished with the following reason: ' + reason
