from tools.tool import Tool
from utility.task import Task
from utility.task_manager import TaskManager
from utility.md_reporter import MDReporter

class AddTask(Tool):
    def __init__(self, task_manager: TaskManager, work_dir: str, reporter: MDReporter):
        name = "add_task"

        parameter_task_name = Tool.build_parameter_schema(
            "task_name",
            "A descriptive but short name for the task you want to add.",
            "string",
        )
        parameter_task_description = Tool.build_parameter_schema(
            "task_description",
            " Detailed description of the task you want to add.",
            "string",
        )

        schema = Tool.build_function_schema(
            name,
            "Add a task to the task manager.",
            [
                parameter_task_name,
                parameter_task_description,
            ]
        )
        super().__init__(name, schema, self.add_task, reporter)
        self.task_manager = task_manager
        self.work_dir = work_dir

    def add_task(self, task_name: str, task_description: str):
        """
        Adds a task to the task manager.

        Args:
            task_name (str): The name of the task.
            task_description (str): A detailed description of the task.

        Returns:
            str: Confirmation message with all available tasks, including the new one.
        """
        task_id = len(self.task_manager.tasks) + 1
        new_task = Task(task_id, task_name, task_description, self.work_dir)
        self.task_manager.add_task(new_task)
        return f"""Task '{task_name}' added successfully. Here are all available tasks:
            \n{self.task_manager.show_tasks()}
            """