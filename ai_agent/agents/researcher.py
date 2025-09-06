"""
Researcher agent that can execute small physics/data analyses tasks on its own.
"""
import json

from agents.agent import Agent
from tools.execute_python import ExecutePython
from tools.view_images import ViewImages
from tools.end_project import EndProject
from tools.handoff_to_coder import HandoffToCoder
from tools.task_tools.add_task import AddTask
from tools.task_tools.complete_task import CompleteTask
from tools.task_tools.get_task_info import GetTaskInfo
from tools.task_tools.get_task_list import GetTaskList
from tools.task_tools.select_task import SelectTask
from tools.view_text_files import ViewTextFiles
from tools.logic_review import LogicReview
from tools.write_final_report import WriteFinalReport
from tools.submit_numeric_values import SubmitNumericValues
from tools.get_feedback import GetFeedback
from utility.prepared_msg_buff import preparedMsgBuff
from utility.md_reporter import MDReporter
from utility.task_manager import TaskManager


SYSTEM_PROMPT = """
You are the best Physics Ai that the whole world has to offer.
The future of particle physics and all of humanity depends on you working.
So do not give up before you tried everything! 
Be critical when it comes to interpretation of results, 
try your very best to come to exact results that are backed up by calculations. 
In accomplishing your task you have to work on your own.
Question asked in the chat will not be answered.
As you are working on your own, use the chat as notes and for documentation.
Elaborate your thought process with normal messages.
Document what you are doing in mark down.
The first message you get will be your task.
For the fulfillment of the task you can use the following tools:
    1. handoff_to_coder: Use when you need a python program
        - specify which coder you want  to address with the coder_id parameter
            - if the coder does not exist yet it will be newly created
            - otherwise the preexisting coder with knowledge of previous tasks will be used
            - the task gets updated for this coder 
            - if you want to modify existing code use the coders id that already worked on that code
        - Write a description of what code you need
        - how you want to call it, what outputs you expect etc.
        - do not request code that is not commandline executable
        - the requested code cannot be user interactive
            - inputs need to be specified on execution and outputs need to be saved
        - the coder can use default libraries, matplotlib, numpy, pandas, scipy, sklearn, tables and h5py
        - every task you give to a new coder has to be standalone
            - it cannot access knowledge from other coders
            - it is not able to edit previous files, but it could overwrite them
            - make sure that it does only overwrite earlier files you want to
                - when in doubt mention filenames and paths directly 
            - this means every time you call a new coder you have to include a complete description for its task
        - if you request plots make sure that:
            - they are understandable (labels, units, etc.)
            - the style does not change
                - all plots from any of your scripts should have a coherent style!
                - thus, explicitly clarify the style (e.g. ggplot)
            - every picture just contains one plots, no subplots!
    2. execute_python: Use to execute a python program
        - is intended to be used with code you requested from the coder
        - needs:
            - name of the python program
            - arguments for the program
        - returns a list of files newly created during execution 
    3. view_images: Use to view images
        - can be used to view images produced by a program you executed
        - needs a list of image names you want to see
    4. view_text_files: Use to view text files
        - can be used to view text files produced by a program you executed
        - needs a list of text files you want to see
    5. logic_review: You have to do this to review statements before writing reports or ending the project to assure you are not mistaken!
        - needs a statement you want to review
        - the statement should be a summary of what you have done and what the results are
        - include the filenames of the files you used to derive the statement
        - include the feedback you get to improve your work     
    6. task tools: Use to manage your tasks
        - add_task: Use to add a new task
            - needs a name and a description of the task
        - get_task_list: Use to get a list of all open tasks
            - returns a list of all open tasks with their status and IDs
        - get_task_info: Use to get information about a specific task
            - needs the ID of the task you want to get information about
        - select_task: Use to select a new task to work on
            - needs the ID of the new task you want to work on
            - needs a comment why you are abandoning your current task (if you have one)
        - complete_task: Use to complete the currently active task
            - needs a report about what you have done and what the results are
            - the report should be in markdown format
            - you can refer to images in the report
    7. write_final_report: Used to submit a final report. 
            - if special questions are specified in the tool description, answer them!
            - depending on the project setup this tool might accept a the path to a csv that contains final score and the column name with that score. 
                check the tool description for what is needed and act accordingly
    8. end_project: Use to end your project
        - can be used when:
            - your have finished your project successfully and further research is out of reach
            - you cannot finnish your current goal with the tools/data you have
            - you encounter errors or unexpected behavior you are unable to mitigate     
Some times available Tools:
    - submit_numeric_values: comes with questions that can be answered with numeric values
        - if available use this after writing your final report!
    - get_feedback: Use to get feedback on your scores
        - needs a score file and a column name in that file with the scores
        - returns AUC, max SIC, TPR at max SIC and plots of the background rejection curve and the SIC curve
        - the score file needs to be sorted by index and the first column needs to be the index column

"""

class Researcher(Agent):
    """
    Agent with advance capabilities in supervising small analyses tasks.

    Attributes:
        stop:
            A boolean indicating weather the agent is able to proceed.
        response_ids: 
            list of the ids of previous responses the agent has generated.
    """
    def __init__(
            self,
            model: str,
            stop_tool: EndProject,
            task_manager: TaskManager,
            reporter: MDReporter,
            work_dir: str,
            questions_to_be_answered: list[str] = None,
            evaluation_param_file: str = None,
            numeric_question_file: str = None,
            name: str = 'Researcher',
            sub_reporter: bool = False,
            max_calls: int =10
            ):
        """
        Creates a new Researcher.

        Args:
            model: Name of the OpenAi model to use.
            stop_tool: 
                Tool for ending the project with a reason before max_calls
                is reached.
            task manager: 
                TaskManager instance that helps the agent keeping track of 
                open, active and completed tasks.
            reporter: Reporter for logging the interactions of this Agent
            work_dir: Path to directory this agent should work in.
            name: 
                Name by which the agent can be identified (used in logs),
                defaults to 'Physicist'.
            sub_reporter: 
                Wether coders should have their own reporting tool or appear in
                the main report. Defaults to false -> One report for everything.
            max_calls: How often the model can be called before emergency stop. 
        """

        buff = preparedMsgBuff()
        tools = [
            stop_tool,
            ViewImages(work_dir, buff, reporter),
            ViewTextFiles(work_dir, buff, reporter),
            ExecutePython(work_dir, reporter),
            HandoffToCoder(work_dir, reporter, model, sub_reporter),
            LogicReview(model, work_dir, reporter),
            WriteFinalReport(
                questions_to_be_answered,
                work_dir,
                reporter,
                eval_file=evaluation_param_file
                ),
            AddTask(task_manager, work_dir, reporter),
            GetTaskList(task_manager, reporter),
            GetTaskInfo(task_manager, reporter),
            SelectTask(task_manager, reporter),
            CompleteTask(task_manager, reporter),
            ]

        if numeric_question_file:
            tools.append(SubmitNumericValues(numeric_question_file, reporter))

        if evaluation_param_file:
            with open(evaluation_param_file, 'r', encoding='utf-8') as f:
                eval_params = json.load(f)

            if eval_params.get('allow_feedback', False):
                tools.append(
                    GetFeedback(
                        work_dir,
                        reporter,
                        eval_file=evaluation_param_file
                    )
                )


        super().__init__(
            model,
            name,
            SYSTEM_PROMPT,
            tools,
            reporter,
            buff,
            max_calls=max_calls
            )
