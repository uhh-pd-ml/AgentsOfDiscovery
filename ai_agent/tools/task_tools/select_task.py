from tools.tool import Tool
from utility.task_manager import TaskManager
from utility.md_reporter import MDReporter

class SelectTask(Tool):
    def __init__(self, task_manager: TaskManager, reporter: MDReporter):
        name = "select_task"
        parameter_new_id = Tool.build_parameter_schema(
            "new_id",
            "The ID of the next task you want to work on.",
            "integer", 
        )
        parameter_comment = Tool.build_parameter_schema(
            "comment",
            "Comment why you are abandoning your current task. Add whats its current status. Also Add info you might need when you pick it up again. If you have no task active leave this empty.",
            "string",
        )

        schema = Tool.build_function_schema(
            name,
            "Select a new task to work on.",
            [
                parameter_new_id,
                parameter_comment,
            ]
            )
        
        super().__init__(name, schema, self.select_task, reporter)
        self.task_manager = task_manager

    def select_task(self, new_id: str, comment: str):
        """
        Select a new task to work on.
        """

        out = ''
        try:
            new_id = int(new_id)
        except ValueError:
            return "The task ID must be an integer."

        if self.task_manager.active_task != -1:
            out += '\n' + self.task_manager.deactivate_task(self.task_manager.active_task, comment)

        for task in self.task_manager.tasks:
            if task.task_id == new_id:
                return out + '\n' + self.task_manager.activate_task(new_id)
        return out + '\n' + "Task not found."



