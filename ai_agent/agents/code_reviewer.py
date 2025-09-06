"""
Code reviewing agent that compares a task and standard requirements with code.
"""
from agents.agent import Agent
from tools.write_code_review import WriteCodeReview
from utility.md_reporter import MDReporter

SYSTEM_PROMPT = """"
You are an AI that reviews python code.
You will be prompted with the code to review and the task that the code should do.
The coder already has passed a linter, so you do not have to check for syntax errors.
Your task is to:
    1. Check that the code does not throw errors that the linter cannot catch
    2. Check that the code fulfills the task
    3. Check also for the following additional requirements:
        - The code has to be commandline executable, data paths have to be passed as arguments
            - if a hardcoded paths are requested, they should be used as default argument for an optional argument
        - outputs have to be saved, no plt.show() allowed and similar statements
        - if plots are produced, they have to be 512 by 512 pixels without subplots
    4. Write short but detailed feedback on what to improve using the write_code_review tool
    5. do not write improved code yourself!
    6. Do no use messages to communicate, everything expected from you can be handled with the write_code_review tool


Give  the feedback using the write_code_review tool.
    - Fail the review if the code does not fulfill the above requirements.
    - Pass the review if the code fulfills the above requirements.
The code does not have to be perfect to pass the review. 
Unlikely edge cases and causes of errors do not have to be considered.  
Let the code pass on good enough!
"""

class CodeReviewer(Agent):
    """
    Code reviewing agent.

    Writes a code review based on standard requirements and the task that the
    code should fullfil. 

    Attributes:
        task: The current task the code is compared to.
        pass_: If the last code passed the review.
        feedback: Feedback for the last code.
        stop:
            A boolean indicating weather the agent is able to proceed.
        response_ids: 
            list of the ids of previous responses the agent has generated.
    """
    def __init__(
            self,
            model: str,
            task: str,
            reporter: MDReporter,
            name: str = "CodeReviewer"
            ):
        """
        Initialize Code reviewing agent.

        Args:
            model: name of the OpenAI model to use
            task:
                Description of the task the code to be reviewed should fullfil.
            reporter:
                Instance of MDReporter used to log all interactions.
            name:
                Name by which the agent can be identified (used in logs),
                defaults to 'CodeReviewer'.
        """
        write_code_review = WriteCodeReview(self, reporter)
        super().__init__(model, name, SYSTEM_PROMPT,
                        [write_code_review], reporter)
        self.task = task
        self.pass_ = False
        self.feedback = ""

    def review(self, path_to_code: str)-> tuple[bool, str]:
        """
        Request code review from the agent.

        Args:
            path_to_code:
                Path specifying where the code to be reviewed can be found.

        Returns:
            Tuple consisting out of if the code passed the review and feedback.

        Raises:
            MaxCallsExceededError: Agent has no calls left.
            ValueError: The message list is empty.

        """
        with open(path_to_code, "r", encoding="utf-8") as file:
            code = file.read()
            print(code)
        messages = [{
            "role": "user",
            "content": f"Code to be reviewed:\n ```python\n{code}\n```"
        },
        {
            "role": "user",
            "content": f'The task the code should align with:\n {self.task}'
        }]
        _ = self.call(messages)

        if self.pass_:
            self._reporter.report_metrics("passed_reviews", 1, mode="add")
        else:
            self._reporter.report_metrics("failed_reviews", 1, mode="add")
        return self.pass_, self.feedback

    def reset(self):
        """
        Reset the Agent to its initial state.
        """
        self.pass_ = False
        self.feedback = ""
        self.stop = False
        self.response_ids = []
