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

---

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

---

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

## Evaluation an Plotting

### Extracting data from runs

Given a least one run, `metric_collector.py` allows to summarize the metrics of all runs in a given directory (`--work_dir`) into two files:

1. **Additive metrics** are numeric metrics that can be summed up easily as a table, the same metrics of different agents during one run are added up. The output is saved in `additive_metrics.csv`, each run is represented by a row.

2. **Combined metrics** are metrics that cannot be easily summed up in a CSV, for example strings and arrays. Those are saved in `combined_metrics.json`. Additionally this file also contains all additive metrics and general information

Metrics gets extracted from all files starting with `metrics_` by default. Strict mode can be activated with `-s`, requiring that the files also have to end with `.json`.
Which metrics get collected from those files is steered by a CSV that has to be passed with `--metrics_to_collect_file`. It has to have the following columns:

- **metric_name** the identifier of the metric you want to collect
- **metric_type** `add` for collecting numeric values, `add_b` for collecting booleans as additive metric, and `append` for metrics that should be saved as combined metric
- **default_value** the value the metrics gets if it was not collected in a run
- **required**    boolean whether the metric has to be present or not, if set to true, do not provide a default value. If a value is required but not present the run is excluded from collection

Furthermore, `--exclusion_criteria file` allows to set criteria for excluding runs. The file has to be a `.json` file formatted as follows:

```json
{
  "list": [
    {
      "metric": "The metric this criterion is applicable to",
      "type": "Either '>', '==' or '<' ",
      "value": "The value the metric is compared to"
    }
  ]
} 
```

If some metric meets one of the exclusion criteria, the run is excluded completely from metric collection.
To keep track how many runs where excluded and how many runs in total where checked those values are stored in the combined metrics file as `total_runs` and `skipped_runs`.

If the `--histogram` flag is set, basic histograms and correlation plots of all metrics are generated.

All generated files are saved to the working directory.

---

### Deriving quantities from collected metrics

After extracting metrics from a run it is possible to calculate quantities based on the additive metrics with `derive_quantities.py`.
The program reads a with `--metrics_file` specified files and calculates new metrics accordingly to a CSV with the following columns:

- **name** the name of the new metric
- **name1** and **name2** names of one of the metrics needed for calculation of the new metric. Instead of a name a numerical value can be given that is used for the calculation in all runs. Either has to be a metric that appears in the specified metrics file or already has been calculated previously
- **operation** the operation that should be carried out with the specified values, has to be one of the following:
  - **+**, **-**, **\***, **\\**, **root** and **log_base**
  - **ln**, **exp** only the metric specified with `name1` is taken into account
- **min1**, **max1**, **min2** and **max2** limits for the operands, can be numeric values or `inf` 
- **default** if one of the metrics does not fall within the specified limits, this value is used


When all new metrics are calculated, they are saved in `--output_dir` as `derived_quantities.csv` 

---

### Comparing batches of different runs

The program `compare_batches.py` allows to compare different batches of runs. At first each batch needs to be summarized with the metric collector. Then outputs of this step than can be used as follows:
```bash
python compare_batches.py -bs /path/to/additive/metrics/of/batch/1/.csv \
                              /add/as/many/as/you/like \
                          -ls 'plot label for batch 1' \
                              'plot labels fot the other batches' \
                          -od path/to/output/directory \
                          -ap path/to/file/with/advance/parameters 
```


---

## Notes

- Including report questions directly in the prompt may help guide the agent toward writing a better final report.
- The agent **does not always** write a final report on its own. If this is required, you should emphasize it in the prompt or provide a questions file.
- Make sure the container is correctly mounted and paths in `params.txt` align with your local environment.

---

## Related Projects

- [Singularity Container Repo (external)](https://github.com/olgarius/ai_agent)— Provides the secure execution environment used by the run scripts.
 
