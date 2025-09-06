"""
Tool that allows the agent to execute a python file in the specified directory.
"""
import os
import glob
import subprocess
import time

from tools.tool import Tool
from utility.md_reporter import MDReporter

class ExecutePython(Tool):
    """
    Tool for executing a python file in a specified directory.

    The execution only is done automatically if the environment variable
    SAVE_EXECUTION_ENV is set to True. Otherwise, the user  will be prompted
    to check the file and execute it manually.

    Attributes:
        work_dir:
            The directory where the agent can find the executable python files.
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
        execute_python(filename: str, cli_args: str) -> str:
            Executes the specified python file with the given command line
            arguments.
            Returns a message indicating the result of the execution.
    """
    def __init__(self, work_dir: str, reporter: MDReporter):
        """
        Initializes the ExecutePython tool.

        Args:
            work_dir: 
                The directory where executable python files are located.
            reporter:
                The reporter to log the execution results.
        """
        name = 'execute_python'
        schema = Tool.build_function_schema(
            name,
            'Execute a python file in the specified directory',
            [
                Tool.build_parameter_schema(
                    'filename',
                    'The name of the python file to execute', 
                    'string'
                ),
                Tool.build_parameter_schema(
                    'cli_args',
                    'The command line arguments to pass to the python file',
                    'string'
                )
            ]
        )

        super().__init__(name, schema, self.execute_python, reporter)
        self.work_dir = work_dir
        self._save_env  = False
        if os.environ.get('SAVE_EXECUTION_ENV') == 'True':
            self._save_env = True

    def execute_python(self, filename: str, cli_args: str) -> str:
        """
        Executes the specified python file with the given cli arguments.
        Args:
            filename:
                The name of the python file to execute 
                (without the .py extension).
            cli_args:
                The command line arguments to pass to the python file.
        Returns:
            A message indicating the result of the execution,
            including any new files created, program output, error output
            and exit status.
        """
        path = self.work_dir + filename + '.py'

        current_files = glob.glob('**', root_dir=self.work_dir, recursive=True)

        if self._save_env:
            start_clock = time.time()
            result = subprocess.run(
                ['python', filename] + cli_args.split(' '),
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=False
            )
            end_clock = time.time()
            self.reporter.report_metrics(
                'execution_time',
                (end_clock - start_clock),
                mode='add'
            )

            output = result.stdout
            error_output = result.stderr
            exit_status = result.returncode

            if exit_status != 0:
                self.reporter.report_metrics(
                    'execute_python_error',
                    1,
                    mode='add'
                    )


        else:
            print('Execute ' + path +
                  ' as follows: python ' + path + str(cli_args))
            print('enter on execution . . . ')
            input()

        new_files = []

        for f in glob.glob('**', root_dir=self.work_dir, recursive=True):
            if f not in current_files:
                new_files.append(f)

        message = 'The following files were created: ' + str(new_files)

        if new_files:
            self.reporter.report_metrics(
                'new_files_created',
                len(new_files),
                mode='add'
                )

        if self._save_env:
            message += '\n Program output: \n' + output \
                + '\n Error output: \n' +  error_output \
                + '\n Exit status: ' + str(exit_status)

        return message


