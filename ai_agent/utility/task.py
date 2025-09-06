class Task:
    def __init__(self, task_id: int, task_name: str, task_description: str, work_dir: str):
        """
        Initializes a Task object with the given task ID, name, and description.

        Args:
            task_id (int): The unique identifier for the task.
            task_name (str): The name of the task.
            task_description (str): A detailed description of the task.
        """
        self.task_id = task_id
        self.task_name = task_name
        self.task_description = task_description
        self.work_dir = work_dir

        self.task_status = -1
        self.comment = []
        self.report = None

    def activate_task(self):
        """
        Activates the task by setting its status to 0.
        """
        self.task_status = 0

    def deactivate_task(self, comment):
        """
        Deactivates the task by setting its status to -1 and appending a comment.
        Args:
            comment (str): A comment explaining why the task was deactivated.
        """
        self.task_status = -1
        self.comment.append(comment)

    def complete_task(self, report):
        """
        Completes the task by setting its status to 1 and storing a report.
        Args:
            report (str): A report detailing the completion of the task.
        """
        self.task_status = 1
        self.report = report

    def get_task_status(self)->str:
        """
        Returns the current status of the task as a string.
        Returns:
            str: The status of the task, which can be "active", "inactive", or "completed".
        """
        if self.task_status == 0:
            return "active"
        elif self.task_status == -1:
            return "inactive"
        elif self.task_status == 1:
            return "completed"
        else:
            return "unknown"

    def get_task_info(self)-> str:
        """
        Returns a string representation of the task's information, including its ID, name, description, status, comments, and report.
        Returns:
            str: A formatted string containing the task's information.
        """
        return f"""Task ID: {self.task_id},
                Task Name: {self.task_name},
                Task Description: {self.task_description},
                Task Status: {self.get_task_status()},
                Comments: {self.comment},
                Report: {self.report}
                """
    
    def get_task_overview(self)-> str:
        """
        Returns a string representation of the task's overview, including its ID, name, and status.
        Returns:
            str: A formatted string containing the task's overview.
        """
        return f"""Task ID: {self.task_id},
                Task Name: {self.task_name},
                Task Status: {self.get_task_status()}
                """

    def save_task(self):
        """
        Saves the task's information to a file in the work directory.
        """
        task_name = self.task_name.replace(" ", "_").replace("/", "_or_")
        with open(f"{self.work_dir}/task_{self.task_id}_{task_name}.md", "w") as f:
            f.write("# Task Information\n")
            f.write(f"| Task ID | Task Name | Task Status |\n")
            f.write(f"|---------|-----------|-------------|\n")
            f.write(f"| {self.task_id} | {self.task_name} | {self.get_task_status()} |\n")
            f.write(f"# Task Description\n")
            f.write(f"{self.task_description}\n")
            f.write(f"# Task Comments\n")
            for comment in self.comment:
                f.write(f"- {comment}\n")
            f.write(f"# Task Report\n")
            if self.report:
                f.write(f"{self.report}\n")
            else:
                f.write("No report available.\n")

            

