"""
logic reviewing agent for improved logical coherence.
"""
from agents.agent import Agent
from tools.view_text_files import ViewTextFiles
from tools.view_images import ViewImages
from utility.prepared_msg_buff import preparedMsgBuff
from utility.md_reporter import MDReporter

SYSTEM_PROMPT = """
You are an AI that is specialized in reviewing logic and reasoning.
You aid in particle physics research by reviewing statements that where based on program outputs (text files, images)
For this you have to compare the statements with the outputs and:
    - if files are referenced in the statement, look at them!
        - for this use your tools:
            - view images for images
            - view text files for text files
    - check if the content of the files was interpreted correctly
    - check if the statements can be derived from the outputs
    - check if the statements are logical consistent
Write detailed feedback, be critical, try to find inconsistencies and errors.

The outcome of mission critical projects depends ont the quality of you work, so give you very best!  
"""

class LogicReviewer(Agent):
    """
    Logic reviewing agent for checking the coherence of statements and data.

    Attributes:
        stop:
            A boolean indicating weather the agent is able to proceed.
        response_ids: 
            list of the ids of previous responses the agent has generated.
    """
    def __init__(
            self,
            model: str,
            reporter: MDReporter,
            work_dir: str,
            name: str = "LogicReviewer"
            ):
        """
        Creates logic reviewing agent.

        Args:
            model: Name of the OpenAi model to use.
            reporter: Reporter for logging the interactions of this Agent
            work_dir: path to directory this agent should work in
            name: Name by which the agent can be identified (used in logs),
                  defaults to 'LogicReviewer'.
        """
        buf = preparedMsgBuff()
        tools = [
            ViewTextFiles(work_dir, buf, reporter),
            ViewImages(work_dir, buf, reporter),
        ]

        super().__init__(model, name, SYSTEM_PROMPT, tools, reporter, buf)

