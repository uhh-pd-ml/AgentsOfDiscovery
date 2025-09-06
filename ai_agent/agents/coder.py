"""
Coding agent for simple code requests.
"""
from agents.agent import Agent
from agents.code_reviewer import CodeReviewer
from tools.write_python import WritePython
from utility.md_reporter import MDReporter

SYSTEM_PROMPT = """
    You are an ai that writes good python code.
    The code you write should full fill the following:
        - The code has to be commandline executable, data paths have to be passed as arguments
            - if a hardcoded paths are requested, they should be used as default argument for an optional argument
        - outputs have to be saved, no plt.show() allowed and similar statements
        - if plots are produced, they have to be 512 by 512 pixels without subplots
        - only default libraries and numpy, matplotlib, pandas, scipy, tables, sklearn and h5py can be used
    For writing code you have to use the tool write_python.
    It takes two arguments: 
        1. the python code as string that gets saved to file
        2. the file the code gets saved to
    The code gets linted automatically, if there are any errors they get returned to you.
    You can then fix the errors by again calling write_python.
    Use messages to log what you are doing.
    If you are done, do not call any tool, and write a short summary that includes the following:
        1. What you did
        2. How the code should be used (short, how to call it via commandline)
        3. Where the code is saved
        4. Where the output files are saved
    """

class Coder(Agent):
    """
    Agent that can be task with simple coding task.

    Includes feedback loop with error linting and code review by a separate  
    code reviewing agent that compares task an standard requirements with the 
    produced code and gives feedback.

    Attributes:
        reviewer: The code reviewer agent used to review this coder code. 
        stop:
            A boolean indicating weather the agent is able to proceed.
        response_ids: 
            list of the ids of previous responses the agent has generated.
    """
    def __init__(
            self,
            model: str,
            work_dir:str,
            reviewer: CodeReviewer,
            reporter: MDReporter,
            name: str = "Coder"
            ):
        """
        Create coding agent.

        Args:
            model: Name of the OpenAI model to use.
            reporter: Instance of MDReporter used to log all interactions.
            name:
                Name by which the agent can be identified (used in logs),
                defaults to 'Coder'.
        """
        super().__init__(
            model,
            name,
            SYSTEM_PROMPT,
            [WritePython(work_dir, self, reporter, reviewer)],
            reporter
            )

        self.reviewer = reviewer


