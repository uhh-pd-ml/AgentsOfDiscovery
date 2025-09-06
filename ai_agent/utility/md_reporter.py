import json

class MDReporter:
    def __init__(self, out_dir, filename="conversation"):
        self.out_dir = out_dir
        self.filename = filename + ".md"
        self.metrics = {}
        self.metric_file = "metrics_" + filename + ".json"

    def report_messages(self, messages, assistant_id=None):
        for m in messages:
            self.report_message(m, assistant_id)

    def report_message(self, message, assistant_id=None):
        with open(self.out_dir + self.filename, "a") as f:
            assistant_id = "to " + assistant_id if assistant_id else ""
            try:
                if message["role"] == "system":
                    f.write("# System Message " + assistant_id + "\n")
                elif message["role"] == "user":
                    f.write("# User Message " + assistant_id + "\n")
                else:
                    f.write("# Unknown Role " + assistant_id + "\n")
            except KeyError:
                try:
                    if message["type"] == "function_call_output": 
                        f.write("# Function Call Output " + assistant_id + "\n")
                        f.write(message["output"] + "\n\n")
                        return
                    else:
                        f.write("# Unknown Type " + assistant_id + "\n")
                except KeyError:
                    f.write("# Unknown Message" + assistant_id + "\n")

            if isinstance(message["content"], list):
                for i, m in enumerate(message["content"]):
                    try:
                        if m["type"] == "input_image":
                            f.write(f"Image {i}\n")
                        else:
                            f.write(str(m) + "\n")
                    except KeyError:
                        f.write(str(m) + "\n")
            else:
                try:
                    if message["type"] == "image_url":
                        f.write("Some Image\n")
                    else:
                        f.write(str(message["content"]) + "\n")
                except KeyError:
                    f.write(message["content"] + "\n\n")
    
    def report_assistant_response(self, response, assistant_id=None):
        assistant_id = "from " + assistant_id if assistant_id else ""

        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            if hasattr(usage, "input_tokens"):
                self.report_metrics("input_tokens", usage.input_tokens, "add")
            if hasattr(usage, "input_tokens_details"):
                if hasattr(usage.input_tokens_details, "cached_tokens"):
                    self.report_metrics(
                        "cached_tokens",
                        usage.input_tokens_details.cached_tokens,
                        "add"
                        )
            if hasattr(usage, "output_tokens"):
                self.report_metrics("output_tokens", usage.output_tokens, "add")
            if hasattr(usage, "output_tokens_details"):
                if hasattr(usage.output_tokens_details, "reasoning_tokens"):
                    self.report_metrics(
                        "reasoning_tokens",
                        usage.output_tokens_details.reasoning_tokens,
                        "add"
                        )
            if hasattr(usage, "total_tokens"):
                self.report_metrics("total_tokens", usage.total_tokens, "add")
        else:
            self.report_metrics("no_usage_provided", 1, "add")

        with open(self.out_dir + self.filename, "a") as f:
            f.write("# Response " + assistant_id + "\n")
            
            for output in response.output:
                if output.type == "message":
                    for content in output.content:
                        f.write("## Message\n")
                        f.write(content.text + "\n\n")
                elif output.type == "function_call":
                    f.write("## Function Call\n")
                    f.write(f"{output.name}({output.arguments})\n\n")
                elif output.type == 'reasoning':
                    f.write("## Reasoning\n")
                    for summary in output.summary:
                        f.write(f"{summary.text}\n\n")
                else:
                    f.write("## Unknown Output\n")
                    f.write(f"{output.type}\n\n")
    
    def report_image(self, path):
        with open(self.out_dir + self.filename, "a") as f:
            f.write("# Image\n")
            f.write(f"![Image]({path})\n\n")

    def report_text(self, text, file_name):
        with open(self.out_dir + self.filename, "a") as f:
            f.write(f"# Text File ({file_name})\n")
            f.write(f"{text}\n\n")

    def report_max_calls(self, agent_id=None):
        with open(self.out_dir + self.filename, "a") as f:
            f.write("# Max Calls Reached\n")
            if agent_id:
                f.write(f"Max calls reached for {agent_id}\n")
            else:
                f.write("Max calls reached\n")

    def report_completion_time(self, time):
        with open(self.out_dir + self.filename, "a") as f:
            f.write("# Completion Time\n")
            f.write(f"Completion time: {time}\n")

    def report_metrics(self, metric, value , mode="append"):
        if mode == "append":
            if metric not in self.metrics:
                self.metrics[metric] = []
            self.metrics[metric].append(value)
        elif mode == "overwrite":
            self.metrics[metric] = value
        elif mode == "add":
            if metric not in self.metrics:
                self.metrics[metric] = 0
            self.metrics[metric] += value
        else:
            raise ValueError("Invalid mode. Use 'append', 'overwrite', or 'add'.")

        file_path = f"{self.out_dir}{self.metric_file}"

        with open(file_path, "w") as f:
            f.write(json.dumps(self.metrics, indent=4))
            

    