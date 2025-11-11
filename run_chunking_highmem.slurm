#!/bin/bash
#SBATCH --job-name=docling_highmem
#SBATCH --output=logs/chunking_hm_%j.log
#SBATCH --error=logs/chunking_hm_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --nodes=1

# ============================================================================
# Docling Hybrid Chunking - High-Memory Configuration
# ============================================================================
#
# This script is optimized for processing LARGE or COMPLEX documents:
# - Technical documentation with many tables
# - Scanned PDFs requiring intensive OCR
# - Documents with high-resolution images
# - Very large files (100+ pages)
#
# Configuration:
# - 24GB RAM   : Double the standard allocation
# - 8 CPU cores: Increased parallel processing
# - 4 hours    : Extended time limit for large batches
#
# When to use this script:
# - Standard script fails with "Out of Memory" errors
# - Processing scanned technical manuals
# - Documents with complex layouts and many tables
# - Batch processing 10+ large documents
#
# Usage:
#   sbatch run_chunking_highmem.slurm
#
# ============================================================================

echo "=============================================="
echo "Docling High-Memory Processing Job"
echo "=============================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Memory: 24GB"
echo "CPUs: 8 cores"
echo "Start time: $(date)"
echo "Working directory: $(pwd)"
echo "=============================================="

# Create logs directory
mkdir -p logs

# Load Singularity/Apptainer module
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

# Change to submission directory
cd $SLURM_SUBMIT_DIR

# Verify container exists
if [ ! -f "hybrid_chunking.sif" ]; then
    echo "ERROR: hybrid_chunking.sif not found in $(pwd)"
    echo "Please build the container first"
    exit 1
fi

# Verify documents directory
if [ ! -d "documents/knowledge" ]; then
    echo "ERROR: documents/knowledge/ directory not found"
    exit 1
fi

# Create outputs directory
mkdir -p outputs

# Set OpenMP threads for parallel processing
export OMP_NUM_THREADS=8

# Count input files
NUM_FILES=$(find documents/knowledge -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" \) | wc -l)
echo "Found $NUM_FILES document(s) to process"

# Display file sizes
echo ""
echo "Input file sizes:"
find documents/knowledge -type f \( -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" \) -exec du -h {} \; | sort -h

echo ""
echo "=============================================="
echo "Starting high-memory processing..."
echo "Configuration:"
echo "  - Table extraction: ENABLED"
echo "  - OCR: ENABLED"
echo "  - Image scale: 2.0x (high resolution)"
echo "  - Parallel threads: 8"
echo "=============================================="
echo ""

# Record start time
START_TIME=$(date +%s)

# Run the container
singularity run \
  -B $PWD/documents:/app/documents \
  -B $PWD/outputs:/app/outputs \
  hybrid_chunking.sif

EXIT_CODE=$?

# Calculate processing time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# Job completion summary
echo ""
echo "=============================================="
echo "Job Completion Summary"
echo "=============================================="
echo "Exit code: $EXIT_CODE"
echo "Processing time: ${MINUTES}m ${SECONDS}s"
echo "End time: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Status: SUCCESS"
    echo ""
    echo "Output files generated:"
    ls -lh outputs/ | tail -n +2

    # Calculate total output size
    TOTAL_SIZE=$(du -sh outputs/ | cut -f1)
    echo ""
    echo "Total output size: $TOTAL_SIZE"
else
    echo "Status: FAILED"
    echo "Check error log: logs/chunking_hm_${SLURM_JOB_ID}.err"
    echo ""
    echo "Troubleshooting tips:"
    echo "- If still out of memory, try processing fewer files at once"
    echo "- Consider splitting large PDFs into smaller sections"
    echo "- Check if OCR can be disabled for text-based PDFs"
fi

echo "=============================================="

exit $EXIT_CODE
