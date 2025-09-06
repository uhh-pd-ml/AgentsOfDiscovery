from tools.tool import Tool
from utility.task_manager import TaskManager
from utility.md_reporter import MDReporter

class GetTaskInfo(Tool):
    def __init__(self, task_manager: TaskManager, reporter: MDReporter):
        name = "get_task_info"
        parameter_id = Tool.build_parameter_schema(
            'task_id',
            'The ID of the task to retrieve information for.',
            'integer'
        )
        schema = Tool.build_function_schema(
            name,
            "Get information about a specific task.",
            [parameter_id]
        )
        super().__init__(name, schema, self.get_task_info, reporter)
        self.task_manager = task_manager

    def get_task_info(self, task_id):
        return self.task_manager.show_task_info(task_id)
