#!/bin/bash

# Create required directories
mkdir -p scraper_output
mkdir -p translator_output
mkdir -p curated_output
mkdir -p .cache

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install required packages
pip install -U pip
pip install pandas requests beautifulsoup4 newspaper3k langdetect
pip install transformers torch tqdm
