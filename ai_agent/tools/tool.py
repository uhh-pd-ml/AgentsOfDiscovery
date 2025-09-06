"""
Base class for tools used by the AI agent.
"""
from typing import Callable

from utility.md_reporter import MDReporter

class Tool:
    """
    Base class for tools used by the AI agent.

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
    def __init__(
            self,
            name: str,
            schema: dict,
            function_: Callable[..., str],
            reporter: MDReporter
            ):
        """
        Initializes the Tool instance.

        Args:
            name:
                The name of the tool.
            schema:
                The schema defining the tool's parameters and return type.
            function_:
                The function that implements the tool's functionality.
            reporter:
                An instance of MDReporter for reporting metrics.
        """
        self.name = name
        self.schema = schema
        self.function = function_
        self.reporter = reporter

    def run(self, parameters: dict)-> str:
        """
        Executes the tool's function with the provided parameters.

        Args:
            parameters:
                A dictionary of parameters to be passed to the tool's function.
        Returns:
            The result of the tool's function execution.
        """
        self.reporter.report_metrics(f"tool_calls_{self.name}", 1, mode="add")
        return self.function(**parameters)

    @staticmethod
    def build_parameter_schema(
        name: str,
        description: str,
        type_: str,
        array: bool = False,
        required: bool = True,
        enum: list[str] = None
        ):
        """
        Builds a parameter schema for the tool.

        Args:
            name:
                The name of the parameter.
            description:
                A description of the parameter.
            type\\_:
                The type of the parameter (e.g., "string", "integer").
            array:
                Whether the parameter is an array (default: False).
            required:
                Whether the parameter is required (default: True).
            enum:
                An optional list of allowed values for the parameter 
                (default: None).
        Returns:
            A dictionary representing the parameter schema.
        """
        if array:
            items = type_
            type_ = "array"

        if not required:
            type_ = [type_, "null"]

        schema = {
            name: {
                "type": type_,
                "description": description
                }
            }

        if enum:
            schema[name]["enum"] = enum

        if array:
            schema[name]["items"] = {
                "type": items
            }

        return schema

    @staticmethod
    def build_function_schema(
        name: str,
        description: str,
        parameters: list[dict]
        ):
        """ Builds a function schema for the tool.

        Args:
            name:
                The name of the function.
            description:
                A description of the function.
            parameters:
                A list of dictionaries representing the parameters of
                the function.
        Returns:
            A dictionary representing the function schema.
        """
        parameter_dict = {}
        for p in parameters:
            parameter_dict.update(p)
        parameter_names = [list(p.keys())[0] for p in parameters]
        schema = {
                "type": "function",
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameter_dict,
                    "required": parameter_names,
                    "additionalProperties": False
                },
                "strict": True
            }
        return schema
