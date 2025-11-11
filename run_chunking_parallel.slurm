#!/bin/bash
#SBATCH --job-name=docling_parallel
#SBATCH --output=logs/chunking_%A_%a.log
#SBATCH --error=logs/chunking_%A_%a.err
#SBATCH --array=0-9%4
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1

# ============================================================================
# Docling Hybrid Chunking - Parallel Job Array Script
# ============================================================================
#
# This script processes multiple documents in parallel using SLURM job arrays.
# Each document is processed independently on a separate compute node.
#
# Configuration:
# - --array=0-9%4  : Process up to 10 files, max 4 jobs running simultaneously
#                    (adjust range based on number of files)
# - %4             : Limits concurrent jobs to 4 (prevents overloading cluster)
#
# Job Array Variables:
# - SLURM_ARRAY_TASK_ID : Index of current task (0, 1, 2, ...)
# - SLURM_ARRAY_JOB_ID  : Main job ID (shared across all array tasks)
#
# Usage:
#   1. Count your PDF files:
#      NUM_FILES=$(find documents/knowledge -name "*.pdf" | wc -l)
#
#   2. Adjust --array range (e.g., for 15 files use --array=0-14%4)
#
#   3. Submit:
#      sbatch run_chunking_parallel.slurm
#
#   4. Monitor:
#      squeue -u $USER
#
# ============================================================================

echo "=============================================="
echo "Docling Parallel Processing - Array Job"
echo "=============================================="
echo "Array Job ID: $SLURM_ARRAY_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "=============================================="

# Create logs directory if it doesn't exist
mkdir -p logs

# Load Singularity/Apptainer module
module load singularity || module load apptainer || echo "Warning: Could not load container module"

# Change to submission directory
cd $SLURM_SUBMIT_DIR

# Create outputs directory if it doesn't exist
mkdir -p outputs

# Build array of all PDF files to process
# Adjust extensions as needed: *.pdf, *.docx, *.pptx, *.md
mapfile -t FILES < <(find documents/knowledge -type f -name "*.pdf" | sort)

# Get total number of files
TOTAL_FILES=${#FILES[@]}

echo "Total files found: $TOTAL_FILES"

# Check if task ID is valid
if [ $SLURM_ARRAY_TASK_ID -ge $TOTAL_FILES ]; then
    echo "ERROR: Task ID $SLURM_ARRAY_TASK_ID exceeds number of files ($TOTAL_FILES)"
    echo "Adjust --array range to 0-$((TOTAL_FILES-1))"
    exit 1
fi

# Get the file for this task
INPUT_FILE="${FILES[$SLURM_ARRAY_TASK_ID]}"
FILENAME=$(basename "$INPUT_FILE")
BASENAME="${FILENAME%.*}"

echo "Processing file: $INPUT_FILE"
echo "Output will be: outputs/${BASENAME}_chunks.txt"
echo "=============================================="

# Create a temporary Python script to process single file
cat > /tmp/process_single_${SLURM_ARRAY_TASK_ID}.py << 'PYSCRIPT'
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, '/app')

# Import the chunking functions
from hybrid_chunking import chunk_document, analyze_chunks, save_chunks
from transformers import AutoTokenizer
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

def main():
    if len(sys.argv) < 2:
        print("Usage: python process_single.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    max_tokens = 512

    print(f"\n{'='*60}")
    print(f"Processing: {Path(file_path).name}")
    print(f"{'='*60}\n")

    # Initialize converter with full features
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.do_ocr = True
    pipeline_options.images_scale = 2.0
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Initialize tokenizer
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)

    # Process document
    chunks, chunker = chunk_document(file_path, max_tokens, converter, tokenizer)

    # Analyze chunks
    analyze_chunks(chunks, tokenizer)

    # Save chunks
    file_name = Path(file_path).stem
    output_path = f"/app/outputs/{file_name}_chunks.txt"
    save_chunks(chunks, chunker, output_path)

    print(f"\n{'='*60}")
    print("Processing complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
PYSCRIPT

# Run the container with single file processing
singularity exec \
  -B $PWD/documents:/app/documents \
  -B $PWD/outputs:/app/outputs \
  -B /tmp/process_single_${SLURM_ARRAY_TASK_ID}.py:/app/process_single.py \
  hybrid_chunking.sif \
  python /app/process_single.py "/app/$INPUT_FILE"

EXIT_CODE=$?

# Clean up temporary script
rm -f /tmp/process_single_${SLURM_ARRAY_TASK_ID}.py

# Task completion summary
echo ""
echo "=============================================="
echo "Task Completion Summary"
echo "=============================================="
echo "Task ID: $SLURM_ARRAY_TASK_ID"
echo "File: $FILENAME"
echo "Exit code: $EXIT_CODE"
echo "End time: $(date)"

if [ $EXIT_CODE -eq 0 ]; then
    echo "Status: SUCCESS"
    OUTPUT_FILE="outputs/${BASENAME}_chunks.txt"
    if [ -f "$OUTPUT_FILE" ]; then
        SIZE=$(du -h "$OUTPUT_FILE" | cut -f1)
        echo "Output size: $SIZE"
    fi
else
    echo "Status: FAILED"
    echo "Check error log: logs/chunking_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
fi

echo "=============================================="

exit $EXIT_CODE
