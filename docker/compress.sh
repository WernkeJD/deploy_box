#!/bin/bash

STACK_NAME="MERN"

# Define the output tar file name
OUTPUT_FILE="$STACK_NAME.tar"

tar --exclude='node_modules' -czvf "$OUTPUT_FILE" -C "$(pwd)" "$STACK_NAME"

echo "Compression completed: $OUTPUT_FILE"
