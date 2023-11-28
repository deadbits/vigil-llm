#!/bin/bash

# Check if a configuration file is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <config-file>"
    exit 1
fi

# Assign the first argument to a variable
config_file="$1"

# Verify that the configuration file exists
if [ ! -f "$config_file" ]; then
    echo "Configuration file not found: $config_file"
    exit 1
fi

# Define an array of datasets
datasets=("deadbits/vigil-instruction-bypass-ada-002" "deadbits/vigil-jailbreak-ada-002")

# Loop through each dataset
for dataset in "${datasets[@]}"; do
    echo "Loading dataset: $dataset with config $config_file"

    # Run the loader script with the current dataset and configuration file
    python loader.py --conf "$config_file" --dataset "$dataset"

    # Check the exit status of the last command
    if [ $? -eq 0 ]; then
        echo "Successfully loaded dataset: $dataset"
    else
        echo "Failed to load dataset: $dataset" >&2
        # Exit the script with a non-zero status
        exit 1
    fi
done

echo "All datasets loaded successfully."
