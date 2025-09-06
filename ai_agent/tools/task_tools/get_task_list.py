from tools.tool import Tool
from utility.task_manager import TaskManager
from utility.md_reporter import MDReporter

class GetTaskList(Tool):
    def __init__(self, task_manager: TaskManager, reporter: MDReporter):
        name = 'get_task_list'
        schema = Tool.build_function_schema(
            name,
            "Returns a list of all open tasks in the task manger, their status and their IDs.",
            []
            )
        super().__init__(name, schema, self.get_task_list, reporter)
        self.task_manager = task_manager

    def get_task_list(self):
        return self.task_manager.show_tasks()