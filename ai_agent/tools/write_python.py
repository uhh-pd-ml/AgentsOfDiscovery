from pylint.lint import Run
from pylint.reporters.json_reporter import JSONReporter
from astroid import MANAGER
import json
import os
import io

from tools.tool import Tool
from agents.code_reviewer import CodeReviewer
from utility.md_reporter import MDReporter

class WritePython(Tool):
    def __init__(self, work_dir, coder, reporter: MDReporter, reviewer: CodeReviewer):
        name = "write_python"
        param_python_code =  Tool.build_parameter_schema(
                            "python_code",
                            "The Python code to be written to the file.",
                            "string"
                        )
        
        param_filename =  Tool.build_parameter_schema(
                            "filename",
                            "The name of the file where the code will be saved.",
                            "string"
                        )
        schema = Tool.build_function_schema(
            name,
            "Writes the provided Python code to a file, lints the file for errors, and returns feedback.",
            [param_python_code, param_filename]
        )
        super().__init__(name , schema, self.write_python, reporter)

        self.coder = coder
        self.reviewer = reviewer
        self.work_dir = work_dir

    def write_python(self, python_code: str, filename: str) -> str:
        """
        Writes the provided Python code to a file, lints the file for errors, and passes it to code review if no errors are found.
        Args:
            python_code (str): The Python code to be written to the file.
            filename (str): The name of the file  where the code will be saved.
        Returns:
            str: A message indicating whether the code was saved successfully, passed the review, and the feedback provided.
        Notes:
            - The file is saved with a ".py" extension in the directory specified by the `WORK_DIR` variable.
            - If linting errors are found, the file is not removed (commented-out code suggests it might have been intended).
        """
        path = self.work_dir + filename 

        directory = '/'.join(path.split('/')[:-1])
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w')as f:
            f.write(python_code)
        
        errors = ""
        errors = self.lint_file(path)

        if len(errors) > 10:
            self.reporter.report_metrics("lint_errors", 1, mode="add")
            # os.remove(path)
            return filename + ': ' + errors
        else:
            self.reviewer.reset()
            pass_, feedback = self.reviewer.review(path)
            if pass_:
                # self.coder.stop = True
                return filename + ' saved successfully. Code passed the review. Feedback: ' + feedback
            else:
                # os.remove(path)
                return filename + ' saved successfully. Code did not pass the review. Feedback: ' + feedback
            




    def lint_file(self, file_path):
        """Runs pylint on the given Python file and returns results as a JSON string."""
        output_stream = io.StringIO()
        reporter = JSONReporter(output_stream)
        
        MANAGER.astroid_cache.clear() # Clear the cache to avoid pylint using old data
        Run(['--errors-only', file_path], reporter=reporter, exit=False)
        
        return output_stream.getvalue()  # Returns JSON output