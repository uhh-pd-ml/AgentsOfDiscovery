from utility.task import Task

class TaskManager:
    def __init__(self):
        self.tasks = []
        self.active_task = -1

    def add_task(self, task: Task):
        self.tasks.append(task)

    def show_tasks(self):
        tasks_overview = ""
        for task in self.tasks:
            if task.task_status != 1:
                tasks_overview += task.get_task_overview() + "\n"
        return tasks_overview
    
    def show_task_info(self, task_id: int):
        for task in self.tasks:
            if task.task_id == task_id:
                return task.get_task_info()
        return "Task not found."
    
    def activate_task(self, task_id: int):
        for task in self.tasks:
            if task.task_id == task_id:
                if self.active_task != -1:
                    self.deactivate_task(self.active_task, "Deactivated due to new activation.")
                task.activate_task()
                self.active_task = task_id
                return f"Task {task_id} activated."
        return "Task not found."
    
    def deactivate_task(self, task_id: int, comment: str):
        for task in self.tasks:
            if task.task_id == task_id:
                task.deactivate_task(comment)
                self.active_task = -1
                return f"Task {task_id} deactivated."
        return "Task not found."
    
    def complete_task(self, task_id: int, report: str):
        for task in self.tasks:
            if task.task_id == task_id:
                task.complete_task(report)
                self.active_task = -1
                return f"Task {task_id} completed."
        return "Task not found."
    
    def save_tasks(self):
        for task in self.tasks:
            task.save_task()