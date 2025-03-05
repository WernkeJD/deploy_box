#!/bin/bash

# Define the stack name
STACK_NAME="MERN"

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the stack directory
STACK_DIR="$SCRIPT_DIR/$STACK_NAME"

# Define the output tar file name
OUTPUT_FILE="$SCRIPT_DIR/$STACK_NAME.tar"

# Check if the stack directory exists
if [ ! -d "$STACK_DIR" ]; then
    echo "Error: Directory $STACK_DIR does not exist."
    exit 1
fi

# Compress the directory, excluding node_modules
tar --exclude='node_modules' --exclude='.env' -czvf "$OUTPUT_FILE" -C "$STACK_DIR" .

# Check if the compression was successful
if [ $? -eq 0 ]; then
    echo "Compression completed: $OUTPUT_FILE"
else
    echo "Error: Compression failed."
    exit 1
fi
