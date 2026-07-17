#!/bin/bash

################################################################################
# GitHub Actions Project Directory Setup Script (Bash)
#
# Purpose: Creates all necessary directories for GitHub Actions automation
# Usage: ./setup_directories.sh
# Cross-platform: Yes (Linux, macOS, Windows with WSL/Git Bash)
#
# Directories created:
#   - .github/workflows/   (for YAML workflow files)
#   - screenshots/         (for debug captures and screenshots)
#   - logs/                (for logs and debugging output)
#
# Each directory will contain a .gitkeep placeholder file to ensure
# the folder structure is tracked in Git.
################################################################################

set -e  # Exit on error

# Color codes for output (optional, can be disabled)
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

# Define the directories to create
DIRECTORIES=(
    ".github/workflows"
    "screenshots"
    "logs"
)

# Function to create directory with .gitkeep
create_directory() {
    local dir="$1"
    
    if [ -d "$dir" ]; then
        echo -e "${YELLOW}[SKIP]${NC} Directory already exists: ${BLUE}$dir${NC}"
    else
        mkdir -p "$dir"
        echo -e "${GREEN}[CREATE]${NC} Successfully created directory: ${BLUE}$dir${NC}"
    fi
    
    # Create .gitkeep file to track the directory in Git
    local gitkeep_file="$dir/.gitkeep"
    if [ ! -f "$gitkeep_file" ]; then
        touch "$gitkeep_file"
        echo -e "${GREEN}[KEEP]${NC} Created placeholder file: ${BLUE}$gitkeep_file${NC}"
    fi
}

# Main execution
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}GitHub Actions Project Directory Setup${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Create all directories
for directory in "${DIRECTORIES[@]}"; do
    create_directory "$directory"
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Setup complete!${NC} All directories have been created."
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Directory structure:"
echo ""
for directory in "${DIRECTORIES[@]}"; do
    echo "  📁 $directory/"
    echo "     └── .gitkeep"
done
echo ""
