#!/bin/bash
#SBATCH --partition=maxgpu                # partition
#SBATCH --array=1-16%4
#SBATCH --time=0-02:00:00                 # maximum runtime in days-hours:minutes:seconds
#SBATCH --export=None
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=8G                          # minimum memory required
#SBATCH --cpus-per-task=1                 # minimum number of CPUs
#SBATCH --job-name=gpt-41         # job name
#SBATCH --output=log/only_ml_split/m_res/b1_gpt-41-%A_%a.out      # log file for command line output
#SBATCH --error=log/only_ml_split/m_res/b1_gpt-41-%A_%a.err       # log file for errors and warnings
#SBATCH --mail-type=End                   # when to get email notifications
#SBATCH --mail-user=tim.lukas-1@studium.uni-hamburg.de         # email address for notifications
#SBATCH --constraint=GPUx1                # GPU constraint
#SBATCH --chdir=/data/dust/user/lukastim/  # where to run the job



PROJECTPATH=project_descriptions/anomaly_c_w_bkg_only_ml_split/m_res/
MODEL=gpt-4.1
WORKDIR=/out/batched/only_ml_split/m_res/b1_gpt-41

# print node information
num_cpus=$(nproc --all)
num_gpus=$(nvidia-smi -L | wc -l)

echo "node: $(uname -n)"
echo "number of CPUs: $num_cpus"
echo "number of GPUs: $num_gpus"
grep MemTotal /proc/meminfo

echo "Starting job..."
echo ""

cd code/mt/masterthesis/scripts/ \
    && source run_default.sh  \
    --prompt_file $PROJECTPATH/prompt.txt \
    --question_file $PROJECTPATH/questions.txt \
    --work_dir $WORKDIR \
    --model $MODEL \
    --numeric_questions_file $PROJECTPATH/numeric_questions.json \
    --job_number $SLURM_ARRAY_TASK_ID