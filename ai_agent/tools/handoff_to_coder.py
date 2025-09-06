"""
Tool that allows to handoff a coding task to a python code writing AI.
"""
from tools.tool import Tool
from agents.coder import Coder
from agents.code_reviewer import CodeReviewer
from utility.md_reporter import MDReporter


class HandoffToCoder(Tool):
    """
    Tool that allows to handoff a coding task to a python code writing AI.

    Attributes:
        work_dir:
            The directory in which the code is saved and executed.
        model:
            The LLM model used for the coder.
        sub_reporter:
            If True, a new MDReporter instance is created for each coder.
        coders:
            A list of coders that have been created, each with an ID and a Coder
            instance.
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
        handoff_to_coder(task: str, coder_id: int) -> str:
            Hands off a coding task to a coder instance identified by coder_id.
            If the coder instance does not exist, a new one is created.
            Returns the response from the coder.
    """
    def __init__(
            self,
            work_dir: str,
            reporter: MDReporter,
            model: str,
            sub_reporter: bool = False
            ):
        """
        Initializes the HandoffToCoder tool.

        Args:
            work_dir: 
                The directory in which the code is saved and executed.
            reporter:
                The reporter to log interactions.
            model:
                The LLM model used for the coder.
            sub_reporter:
                If True, a new MDReporter instance is created for each coder.
        """
        name = 'handoff_to_coder'

        parameter_task = Tool.build_parameter_schema(
            'task',
            """
            Detailed description for the coder on what the python code 
            should do. 
            Specify how you want the program inputs and outputs to work.
            """,
            'string'
        )
        parameter_coder_id = Tool.build_parameter_schema(
            'coder_id',
            """
            Integer that refers to the coder instance you want to use. 
            The instance remembers what happened before 
            and can build on that knowledge.
            If the integer does not exist yet,
            a new coder with this number is created
            """,
            'integer'
        )

        schema = Tool.build_function_schema(
            name,
            """
            Tool that allows to handoff a coding task to a python code 
            writing AI.
            Call if you need python code.
            Code that you request needs to be commandline executable and outputs
            have to be saved, images need to be 512x512px.
            The coder can use the following packages:
            numpy, pandas, matplotlib, seaborn, sklearn and tables
            + default packages.
            """,
            [parameter_task, parameter_coder_id]
        )

        super().__init__(name, schema, self.handoff_to_coder, reporter)
        self.work_dir = work_dir
        self.reporter = reporter
        self.model = model
        self.coders = []
        self.sub_reporter = sub_reporter

    def handoff_to_coder(self, task, coder_id):
        """
        Hands off a coding task to a coder instance identified by coder_id.
        If the coder instance does not exist, a new one is created.
        
        Args:
            task:
                Detailed description for the coder on what the python code
                should do.
            coder_id:
                Integer that refers to the coder instance that should be used.
                Creates a new coder instance if the ID does not exist yet.
        Returns:
            The response from the coder, including a introduction how the
            program can be used.
        """
        coder: Coder = None
        for c in self.coders:
            if c['id'] == coder_id:
                coder = c['coder']
                coder.reviewer.task = task
                coder.reset_call_count()
                coder.reviewer.reset_call_count()

        if coder is None:
            if self.sub_reporter:
                reporter = MDReporter(
                    self.work_dir,
                    filename=f'conversation_coder_{str(coder_id)}'
                    )
            else:
                reporter = self.reporter
            reviewer = CodeReviewer(self.model, task, reporter)
            coder =  Coder(
                self.model,
                self.work_dir,
                reviewer,
                reporter,
                name=f"Coder {str(coder_id)}"
                )
            self.coders.append({'id': coder_id, 'coder': coder})

            self.reporter.report_metrics('different_coders', 1, mode='add')

        message = {
            'role': 'user',
            'content': task
        }

        response = coder.call([message])
        return response
