#!/bin/zsh -l
# Antigravity Linker Host Launcher
# Runs as a login shell to ensure pyenv, PATH, and user environments are correctly loaded.

# Navigate to the script's directory
DIR="$(cd "$(dirname "$0")" && pwd)"

# Execute the python script with the inherited environment
exec python3 "$DIR/save_skill.py"
