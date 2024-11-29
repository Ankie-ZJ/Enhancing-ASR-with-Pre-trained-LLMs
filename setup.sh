#!/bin/bash

# Script to set up a conda environment for running this project

# Step 1: Create the conda environment
echo "Creating a conda environment..."
conda create -n asr_llm_rescoring python=3.10 -y

# Step 2: Activate the conda environment
echo "Activating the conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate asr_llm_rescoring

# Check if activation was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to activate conda environment 'asr_llm_rescoring'. Exiting."
    exit 1  # Exit the script with an error code
fi

# Step 3: Install PyTorch and CUDA dependencies
echo "Installing PyTorch, Torchaudio, and CUDA..."
conda install pytorch==2.0.1 torchaudio==2.0.2 pytorch-cuda=11.8 -c pytorch -c nvidia -y

# Step 4: Clone the ESPnet repository
echo "Checking if ESPnet repository already exists..."
if [ -d "espnet" ]; then
    echo "ESPnet repository already exists. Skipping cloning."
else
    echo "Cloning ESPnet repository..."
    git clone https://github.com/espnet/espnet.git
fi

# Step 5: Install ESPnet and its dependencies
echo "Installing ESPnet and dependencies..."
cd espnet
pip install -e .
cd ..

# Step 6: Install additional Python packages required for the project
echo "Installing additional Python packages from requirements.txt..."
pip install -r requirements.txt
pip install -U espnet

echo "Conda environment setup is complete. Activate the environment with 'conda activate asr_llm_rescoring'."
