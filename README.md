# WORK IN PROGRESS


# Agents of Discovery

This repository provides a framework for running AI agents with tools and execution scripts. For safely running AI-generated code it uses [this](https://github.com/olgarius/ai_agent) Singularity container.

---

## Requirements

- **OpenAI API access**: You must have an API key. Export it as described in the [official OpenAI documentation](https://platform.openai.com/docs/libraries?language=python).
- **Singularity**: Required for full functionality. This repo assumes that you are able to run singularity containers from [docker hub](https://hub.docker.com/)
- **OpenAI Python SDK**: Only needed if you're running the code outside the container environment.

> **Note**: While running outside the container is possible, it limits agent capabilities. You’ll be prompted to execute code manually, and only file-level outputs are passed back to the agent—logs and program output are ignored.

---

## Usage

### Setup

1. Clone this repository.
2. Ensure you have access to the external Singularity container (see separate container repo).
3. Create a file named `params.txt` inside the [scripts](scripts/) directory. It should contain the following three lines:

```plaintext
/path/to/data/directory/
/path/to/output/directory/
/path/to/the/ai_agent/directory/
```

4. Prepare:
   - A **prompt file** describing the task (e.g., `projects/example_prompt.txt`)
   - Optionally, a **question file** for final report questions (one per line, e.g., `projects/example_questions.txt`)

---

### Execution

To launch an agent with the default project:

```bash
source run_default.sh --prompt_file projects/example_prompt.txt --question_file projects/example_questions.txt --work_dir /out/tests --model gpt-4.1
```

- `--prompt_file`: (Required) Path to the task description.
- `--question_file`: (Optional) Path to a list of report questions.
- `--work_dir`: (Optional) Path inside the container to store output. Defaults to `/out/`.
- `--model`: (Optional) OpenAI model (with vision support). Defaults to `gpt-4o-mini`.

Available models are listed in the [OpenAI documentation](https://platform.openai.com/docs/models).

### Automatic evaluation for scoring tasks 
The `--evaluation_param_file` allows for automated evaluation of projects where the agent is tasked with score something.
The file needs to have the following structure:
```json
{
    "label_file": "/path/to/truth/labels/",
    "plot_label": "Title to appear with plots"
}
```
The `label_file` must contain a column named `label` with the truth information.

If an evaluation file is provided, ROC and SIC Curves will be saved under `background_rejection_curve.png` and `sic_curve.png` respectively. 
The area under the ROC curve (AUC) is reported in the primary metrics file together with the maximum SIC value and corresponding TPR (tpr max SIC). 

The JSON file can also contain a field `allow_feedback`, if this is set to `true`, it enables the `get_feedback` tool.
This tool allows the agent to submit a score files and get feedback on its performance (including AUC, max SIC, tpr max SIC and both plots).
This allows for iterative behavior.

### Collection of numeric answers from the agent

The agent can be tasked with questions that only accept numbers as answers. Those numbers can then be submitted with a tool and get logged to the primary metric file. 
For this `--numeric_questions_file` accepts a path to file with the following structure:
```json
 {
  "questions":[
    {
      "question_identifier": "Parameter name in the tool and the metric file",
      "question": "The question the agent should answer"
    }
  ]
 }
```

---

### Custom Projects

To run a custom agent-based project inside the container:

```bash
./scripts/run_custom.sh
```

This launches the container and drops you into a shell inside the `/code/` directory. You can then execute:

```bash
python -m projects.your_custom_project <args>
```

---

## Output Structure

Each run creates a subdirectory under the specified working directory (e.g., `run_0`, `run_1`, ..., `run_#>`).
If a job number is provided with `--job_number` the directories are called `job_<job_number>_#`,
this is for preventing errors when simultaneously creating working directories during job arrays. 

Key outputs include:

- **Agent Conversations**:
  - `conversation.md`: Main agent (_Researcher_)
  - `conversation_coder_#.md`: Coding sub-agents
  - `logic_review_#.md`: Logic reviewer agents

- **Metrics**:
  - `metrics_conversation.json`
  - `metrics_conversation_coder_#.json`
  - `metrics_logic_review_#.json`

  These provide detailed tool usage stats, success/failure rates, prompt context, model info, execution time and more.

- **Additional Files**:
  - `task_#.md`: Agent-generated subtasks
  - `final_report.md`: Summary output (if produced by the agent)
  - `feedback/r_#/*`: SIC plot, background rejection plot and submitted score file (only when feedback is enabled)

---

## Notes

- Including report questions directly in the prompt may help guide the agent toward writing a better final report.
- The agent **does not always** write a final report on its own. If this is required, you should emphasize it in the prompt or provide a questions file.
- Make sure the container is correctly mounted and paths in `params.txt` align with your local environment.

---

## Related Projects

- [Singularity Container Repo (external)](https://github.com/olgarius/ai_agent)— Provides the secure execution environment used by the run scripts.
 
