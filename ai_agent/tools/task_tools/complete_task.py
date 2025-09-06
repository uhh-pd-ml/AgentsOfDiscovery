from tools.tool import Tool
from utility.task_manager import TaskManager
from utility.md_reporter import MDReporter

class CompleteTask(Tool):
    def __init__(self, task_manager: TaskManager, reporter: MDReporter):
        name = "complete_task"
        parameter_report = Tool.build_parameter_schema(
            "report",
            "Completion report for the task. What has been done what are the results. Preferably in markdown, you can refer to images.",
            "string"
        )
        schema = Tool.build_function_schema(
            name,
            "Complete the currently active task and write a report about it.",
            [
                parameter_report
            ]
        )
        super().__init__(name, schema, self.complete_task, reporter)
        self.task_manager = task_manager

    def complete_task(self, report: str):
        """
        Complete the currently active task and write a report about it.
        """
        if self.task_manager.active_task == -1:
            return "No active task to complete."
        
        task_id = self.task_manager.active_task
        result = self.task_manager.complete_task(task_id, report)
        return result