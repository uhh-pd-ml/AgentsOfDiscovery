"""
Agent class for managing interactions with OpenAI's API.
"""
import json
from typing import Any
import time

from openai import OpenAI
from openai.types.responses import Response


from tools.tool import Tool
from utility.md_reporter import MDReporter
from utility.prepared_msg_buff import preparedMsgBuff


class MaxCallsExceededError(Exception):
    """Custom exception raised when the maximum number of calls is exceeded."""
    pass


class Agent:
    """
    Base class for all agents, handles all API and Tool interactions.

    Attributes:
        stop:
            A boolean indicating weather the agent is able to proceed.
        response_ids: 
            list of the ids of previous responses the agent has generated.        
    """

    def __init__(
        self,
        model: str,
        agent_name: str,
        system_prompt: str,
        tools: list[Tool],
        reporter: MDReporter,
        prepared_message_buffer: preparedMsgBuff = preparedMsgBuff(),
        max_calls: int = 10,
        client: OpenAI = OpenAI()
        ):
        """
        Initializes new agent based on parameters.

        Args:
            model: name of the OpenAI model to use
            name: name by which the agent can be identified (used in logs)
            system_prompt: developer message to initialize the model
            tools: a list of tools the model can use
            reporter: instance of MDReporter used to log all interactions
            prepared_message_buffer: buffer saving messages for later
            max_calls:  how often the model can be called before emergency stop
            client: used to connect to LLM API and submit calls        

        """

        self._client = client
        self._model = model
        self._agent_name = agent_name
        self._system_prompt = system_prompt
        self._tools = tools
        self._reporter = reporter
        self._prepared_message_buffer = prepared_message_buffer

        self._max_calls = max_calls
        self._call_count = 0
        self.stop = False

        self.response_ids = []

    def iterate(self):
        """
        Checks for max calls and increments the call counter.
        """
        if self._call_count >= self._max_calls:
            self.stop = True
            self._reporter.report_max_calls(self._agent_name)
            self._reporter.report_metrics("max_calls_reached", 1, mode="add")
            print(f"Max calls reached for {self._agent_name}")
        self._call_count += 1

    def _create_response(
            self,
            messages: list[Any],
            last_response_id: int = None
            ) -> Response:
        """
        Makes OpenAI API call and logs interaction.

        Args:
            messages:
                A list of messages in the format:
                {"role": "user", "content": "<content>"}
            last_response_id:
                Id of the last message in a existing conversation the agent 
                should see. Defaults to the id of the last response created by
                this agent or none if its the first call.
        
        Returns:
            OpenAi response object containing the information on the call.

        Raises:
            MaxCallsExceededError: Agent has no calls left     
        """
        if self.stop:
            raise MaxCallsExceededError("Max calls reached")
        self.iterate()
        self._reporter.report_metrics("num_calls", 1, mode = "add")


        self._reporter.report_messages(messages, self._agent_name)

        if last_response_id is None:
            if self.response_ids:
                last_response_id = self.response_ids[-1]
            else:
                response = self._client.responses.create(
                    model=self._model,
                    instructions=self._system_prompt,
                    input=messages,
                    tools=[tool.schema for tool in self._tools],
                    )
                self.response_ids.append(response.id)
                self._reporter.report_assistant_response(
                    response, self._agent_name)
                return response

        response = self._client.responses.create(
            model=self._model,
            instructions=self._system_prompt,
            input=messages,
            tools=[tool.schema for tool in self._tools],
            previous_response_id=last_response_id
            )

        self.response_ids.append(response.id)
        self._reporter.report_assistant_response(response, self._agent_name)
        return response

    def call(self, messages: list[Any], last_response_id=None):
        """
        Calls the Agent with a list of messages, handles in between tool calls
        and logs interaction.

        Args:
            messages:
                A list of messages in the format:
                {"role": "user", "content": "<content>"}
            last_response_id:
                Id of the last message in a existing conversation the agent 
                should see. Defaults to the id of the last response created by
                the agent.
        Returns:
            Either the output text or No_response if there is no response

        Raises:
            MaxCallsExceededError: Agent has no calls left.
            ValueError: The message list is empty.
        
        """
        if messages == []:
            raise ValueError("Message list is empty")
        response = None

        #  create response and check if there are tool calls. Results of tool
        #  calls get stored in messages and initiate next call until there are
        #  no more tool calls.

        while not messages == [] and not self.stop:
            start_time = time.time()
            response = self._create_response(messages, last_response_id)
            mid_time = time.time()
            messages = self.execute_tool_calls(response)
            end_time = time.time()
            self._reporter.report_metrics("response_time",
                                            mid_time - start_time, mode="add")
            self._reporter.report_metrics("tool_call_time",
                                            end_time - mid_time, mode="add")
        if self.stop and messages:
            self._reporter.report_messages(messages, self._agent_name)
        if response is None:
            return "No response"
        return response.output_text

    def call_function(self, name: str, args) -> str:
        """
        Searches function in available tools by name and executes it.

        Args:
            name: name of the tool to execute
            args: arguments for the tool to be executed

        Returns:
            Text result of the tool call  
        """
        result = "function not found"
        for tool in self._tools:
            if tool.name == name:
                result = tool.run(args)
                break
        self._reporter.report_metrics("tool_calls", 1, mode="add")
        print("\n Result:")
        print(result)
        print("\n\n")

        return result

    def execute_tool_calls(self, response: Response) -> list[Any]:
        """
        Executes tool calls in a response and returns resulting tool messages.

        Args:
            response: OpenAi response object

        Returns:
            List of tool messages with the results of the tool calls. 
        """
        tool_messages = []
        for tool_call in response.output:
            if tool_call.type != "function_call":
                continue

            name = tool_call.name
            args = json.loads(tool_call.arguments)

            print(f"\n Executing: {name}(args={args})")

            result = self.call_function(name, args)
            tool_messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(result)
            })

            for pm in self._prepared_message_buffer.get_msg():
                tool_messages.append(pm)
            self._prepared_message_buffer.clear_msg()
        return tool_messages

    def reset_call_count(self):
        """
        Resets the call count of the agent.
        """
        self._call_count = 0
        self.stop = False
        self._reporter.report_metrics("num_resets", 1, mode="add")
