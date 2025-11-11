#!/bin/bash
#SBATCH --job-name=docling_chunking
#SBATCH --output=logs/chunking_%j.log
#SBATCH --error=logs/chunking_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1

# ============================================================================
# Docling Hybrid Chunking - Basic SLURM Job Script
# ============================================================================
#
# This script runs the full-featured Docling processor with:
# - Table extraction (TableFormer)
# - OCR for scanned documents
# - High-resolution image processing
# - Context-aware semantic chunking
#
# Requirements:
# - hybrid_chunking.sif container built from singularity.def
# - documents/knowledge/ folder with PDFs to process
# - 16GB RAM allocation (adjust --mem if needed)
#
# Usage:
#   sbatch run_chunking.slurm
#
# ============================================================================

echo "=============================================="
echo "Docling Hybrid Chunking Job Started"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "=============================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Load Singularity/Apptainer module (adjust for your HPC environment)
# Common module names: singularity, apptainer, singularityce
module load singularity || module load apptainer || echo "Warning: Could not load container module"

# Verify module loaded
if command -v singularity &> /dev/null; then
    echo "Using Singularity: $(singularity --version)"
elif command -v apptainer &> /dev/null; then
    echo "Using Apptainer: $(apptainer --version)"
else
    echo "ERROR: Neither singularity nor apptainer found!"
    exit 1
fi

# Set working directory to job submission directory
cd $SLURM_SUBMIT_DIR

# Verify container exists
if [ ! -f "hybrid_chunking.sif" ]; then
    echo "ERROR: hybrid_chunking.sif not found in $(pwd)"
    echo "Please build the container first with:"
    echo "  singularity build hybrid_chunking.sif singularity.def"
    exit 1
fi

# Verify documents directory exists
if [ ! -d "documents/knowledge" ]; then
    echo "ERROR: documents/knowledge/ directory not found"
    echo "Please create it and add your PDF files"
    exit 1
fi

# Create outputs directory if it doesn't exist
mkdir -p outputs

# Count input files
NUM_FILES=$(find documents/knowledge -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" \) | wc -l)
echo "Found $NUM_FILES document(s) to process"
echo "=============================================="

# Run the container
echo "Starting Docling processing..."
echo ""

singularity run \
  -B $PWD/documents:/app/documents \
  -B $PWD/outputs:/app/outputs \
  hybrid_chunking.sif

EXIT_CODE=$?

# Job completion summary
echo ""
echo "=============================================="
echo "Job Completion Summary"
echo "=============================================="
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Status: SUCCESS"
    echo ""
    echo "Output files generated:"
    ls -lh outputs/
else
    echo "Status: FAILED"
    echo "Check error log: logs/chunking_${SLURM_JOB_ID}.err"
fi

echo "=============================================="

exit $EXIT_CODE
