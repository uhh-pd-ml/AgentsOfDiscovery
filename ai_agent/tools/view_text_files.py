import os
from typing import Dict, Any

from tools.tool import Tool
from utility.prepared_msg_buff import preparedMsgBuff
from utility.md_reporter import MDReporter


class ViewTextFiles(Tool):
    def __init__(self, work_dir: str, prepared_message_buffer: preparedMsgBuff, reporter: MDReporter):
        name = "view_text_files"
        parameter_filenames = Tool.build_parameter_schema(
            "filenames",
            "List of filenames you want to view.",
            "string",
            array=True
            )
    
        schema = Tool.build_function_schema(
            name,
            """
            Processes a list of text filenames,
            appending existing text files to to the next user message buffer.
            The tool response includes which images were appended and which images do not exist.
            """,
            [parameter_filenames]
        )

        super().__init__(name, schema, self.view_text_files, reporter)
        self.work_dir = work_dir
        self.prepared_message_buffer = prepared_message_buffer
        self.reporter = reporter

    def view_txt(self, filename: str, txt_msg_list:str) -> tuple[str, bool]:
        path = self.work_dir + filename
        if not os.path.isfile(path):
            return txt_msg_list, False, 
        
        ext = filename.split('.')[-1]
        
        txt = ''
        with open(path, "r") as file:
            app = False
            try:
                txt = file.read()
                app = True
            except UnicodeDecodeError:
                txt = "File could not be read as text, possibly binary or unsupported encoding."
                self.reporter.report_metrics("view_text_files_error", 1, mode="add")
                app = False

            if len(txt) > 2000:
                txt = txt[:2000] + '...\n \n FILE TO LARGE TO DISPLAY IN FULL'
                self.reporter.report_metrics("view_text_files_truncated", 1, mode="add")

        txt_msg_list += f"## {filename}\n \n {txt}\n\n\n" 

        self.reporter.report_text(txt, filename)

        return txt_msg_list, app

    def view_text_files(self, filenames: list[str]) -> str:
        txt_msg_list = ''
        success = []
        failure = []
        for fn in filenames:
            txt_msg_list, appended = self.view_txt(fn, txt_msg_list)
            if appended:
                success.append(fn)
            else:
                failure.append(fn)
        txt_msg = {
            "role": "user",
            "content": txt_msg_list 
        }

        self.reporter.report_metrics("view_text_files_success", len(success), mode="add")
        self.reporter.report_metrics("view_text_files_failure", len(failure), mode="add")

        self.prepared_message_buffer.add_msg(txt_msg)

        return f"The following text files were appended in this order: {str(success)}, the following text files do not exist: {str(failure)} "