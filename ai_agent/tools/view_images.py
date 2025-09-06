"""
Tool that allows the Agent to request image files.
"""
import os
import base64
from typing import Dict, Any

from tools.tool import Tool
from utility.prepared_msg_buff import preparedMsgBuff
from utility.md_reporter import MDReporter


class ViewImages(Tool):
    """
    A tool that allows the Agent request image files.

    Attributes:
        work_dir:
            The directory where the images are stored.
        prepared_message_buffer:
            An instance of preparedMsgBuff for storing messages to be sent to
            the agent.
        name:
            The name of the tool.
        schema:
            The schema defining the tool's parameters and return type.
        function:
            The function that implements the tool's functionality has to 
            return a string containing the result readable for a LLM.
        reporter:
            An instance of MDReporter for reporting metrics.
    """
    def __init__(
            self,
            work_dir: str,
            prepared_message_buffer: preparedMsgBuff,
            reporter: MDReporter
        ):
        """
        Initializes the ViewImages tool.

        Args:
            work_dir: 
                The directory where the images are stored.
            prepared_message_buffer: 
                An instance of preparedMsgBuff for storing messages to be sent
                to the agent.
            reporter: 
                An instance of MDReporter for reporting metrics.
        """
        name = 'view_images'
        parameter_filenames = Tool.build_parameter_schema(
            'filenames',
            'List of image filenames you want to view.',
            'string',
            array=True
            )
    
        schema = Tool.build_function_schema(
            name,
            """
            Processes a list of image filenames,
            appending existing images to to the next user message buffer.
            The tool response includes which images were appended and which
            images do not exist.
            """,
            [parameter_filenames]
        )

        super().__init__(name, schema, self.view_images, reporter)
        self.work_dir = work_dir
        self.prepared_message_buffer = prepared_message_buffer
        self.reporter = reporter

    @staticmethod
    def encode_image(image_path:str) -> str:
        """
        Encodes an image file into a Base64 string.

        Args:
            image_path (str): The file path to the image to be encoded.

        Returns:
            str: The Base64-encoded string representation of the image.

        Raises:
            FileNotFoundError: If the specified image file does not exist.
            IOError: If there is an error reading the image file.
        """
        with open(image_path, 'rb') as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


    def view_image(
        self,
        filename: str,
        img_msg_list: list[str]
    ) -> tuple[list[Dict[str, Any]], bool]:
        """
        Processes an image file and appends its encoded data to a list of image
        messages.

        Args:
            filename (str): The name of the image file to be processed.
            img_msg_list (list[str]): A list of dictionaries containing image
            message data.
        Returns:
            tuple[list[Dict[str, Any]], bool]: A tuple containing:
                - The updated list of image message dictionaries.
                - A boolean indicating whether the file was successfully
                processed.
        """
        path = self.work_dir + filename
        if not os.path.isfile(path):
            return img_msg_list, False, 

        ext = filename.split('.')[-1]
    
        img = self.encode_image(path)

        img_msg_list.append({
            'type': 'input_image',
            'image_url': f'data:image/{ext};base64,{img}',
        })

        self.reporter.report_image(filename)

        return img_msg_list, True


    def view_images(self, filenames: list[str]) -> str:
        """
        Processes a list of image filenames, appending valid image messages to a 
        prepared message buffer and categorizing filenames into success and
        failure lists.

        Args:
            filenames (list[str]): A list of image filenames to process.

        Returns:
            str: A summary message indicating which images were successfully
            appended and which images do not exist.

        The function calls `view_image` for each filename in the input list.
        If the image is successfully processed, it is added to the `success`
        list; otherwise, it is added to the `failure` list. The processed image
        messages are stored in the `prepared_message_buffer` as a dictionary
        with "role" and "content" keys.
        """
        img_msg_list = []
        success = []
        failure = []
        for fn in filenames:
            img_msg_list, appended = self.view_image(fn, img_msg_list)
            if appended:
                success.append(fn)
            else:
                failure.append(fn)
        img_msg = {
            'role': 'user',
            'content': img_msg_list 
        }

        self.reporter.report_metrics('view_images_success',
                                     len(success), mode='add')
        self.reporter.report_metrics('view_images_failure',
                                     len(failure), mode='add')

        self.prepared_message_buffer.add_msg(img_msg)

        return f"""
        The following images were appended in this order: {str(success)},
        the following images do not exist: {str(failure)}
        """
