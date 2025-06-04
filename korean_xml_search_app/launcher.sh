#!/bin/bash

echo "Activating virtual environment and starting the XML Search App..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Check if venv exists
if [ ! -f "${SCRIPT_DIR}/venv/bin/activate" ]; then
    echo "ERROR: Virtual environment (venv) not found in ${SCRIPT_DIR}."
    echo "Please run the setup instructions in README.md first."
    exit 1
fi

# Activate virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

# Check if src directory and gui.py exist
if [ ! -f "${SCRIPT_DIR}/src/gui.py" ]; then
    echo "ERROR: src/gui.py not found in ${SCRIPT_DIR}."
    echo "Ensure the project structure is correct."
    # Attempt to deactivate if venv was sourced, though exit will usually handle it
    type deactivate &>/dev/null && deactivate
    exit 1
fi

echo "Starting GUI..."
cd "${SCRIPT_DIR}/src"
python3 gui.py
cd "${SCRIPT_DIR}" # Return to original directory

# Deactivate virtual environment (optional, happens when script ends or shell closes)
# deactivate

echo "Application closed."
