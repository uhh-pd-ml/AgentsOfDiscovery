#!/bin/bash

# Hardcoded parameter file
PARAM_FILE="./params.txt"

# Read parameters from the file
read -r DATA_DIR < <(sed -n '1p' "$PARAM_FILE")
read -r OUTPUT_DIR < <(sed -n '2p' "$PARAM_FILE")
read -r CODE_DIR < <(sed -n '3p' "$PARAM_FILE")

# Check directories
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: '$DATA_DIR' does not exist."
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: '$OUTPUT_DIR' does not exist."
    exit 1
fi

if [ ! -d "$CODE_DIR" ]; then
    echo "Error: '$CODE_DIR' does not exist."
    exit 1
fi

# Check API key
if [[ -z "${OPENAI_API_KEY}" ]]; then
    echo "Error: OPENAI_API_KEY not set"
    exit 1
fi

# Docker/Singularity image
SINGULARITY_IMAGE="docker://olgarius1/ai_agent:latest"

# Capture additional arguments
PYTHON_ARGS="$@"

# Run container and pass arguments to Python module
SINGULARITYENV_OPENAI_API_KEY="$OPENAI_API_KEY" singularity run --containall \
    --bind "$OUTPUT_DIR":/out \
    --bind "$DATA_DIR":/data:ro \
    --bind "$CODE_DIR":/code:ro \
    "$SINGULARITY_IMAGE" \
    -c "cd /code && exec /bin/bash"