# HPC Quick Start Guide - Docling Hybrid Chunking

This guide provides step-by-step instructions for running the Docling document processing pipeline on HPC systems with SLURM.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Building the Container](#building-the-container)
- [Transferring to HPC](#transferring-to-hpc)
- [Running Jobs](#running-jobs)
- [Monitoring Jobs](#monitoring-jobs)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Your Local Machine (with internet)
- Singularity or Apptainer installed
- This repository cloned
- Internet access for downloading models

### On HPC
- Access to HPC cluster with SLURM
- Singularity/Apptainer module available
- Sufficient storage quota (plan for ~5GB per container + outputs)

---

## Building the Container

### Step 1: Build on a Machine with Internet Access

```bash
# Navigate to project directory
cd vector_database

# Build the container (requires ~10-15 minutes, downloads ~2GB)
singularity build hybrid_chunking.sif singularity.def
```

**Alternative using Apptainer:**
```bash
apptainer build hybrid_chunking.sif singularity.def
```

**What happens during build:**
- Installs Python 3.11 and system dependencies
- Installs Docling, PyTorch, Transformers
- **Pre-caches all models** (no internet needed at runtime)
- Configures full-featured pipeline (TableFormer, OCR)

### Step 2: Verify Container Build

```bash
# Check container info
singularity inspect hybrid_chunking.sif

# Test container (should show help text)
singularity run-help hybrid_chunking.sif

# Verify models are cached
singularity exec hybrid_chunking.sif ls -lh /opt/models
```

---

## Transferring to HPC

### Upload Container and Documents

```bash
# Set your HPC details
HPC_USER="your_username"
HPC_HOST="hpc.university.edu"
HPC_PATH="/scratch/your_project/docling"

# Create remote directory
ssh ${HPC_USER}@${HPC_HOST} "mkdir -p ${HPC_PATH}"

# Upload container (~3GB, may take 5-10 minutes)
scp hybrid_chunking.sif ${HPC_USER}@${HPC_HOST}:${HPC_PATH}/

# Upload SLURM scripts
scp run_chunking*.slurm ${HPC_USER}@${HPC_HOST}:${HPC_PATH}/

# Upload documents
scp -r documents/ ${HPC_USER}@${HPC_HOST}:${HPC_PATH}/
```

### SSH to HPC and Set Up

```bash
# Connect to HPC
ssh ${HPC_USER}@${HPC_HOST}

# Navigate to project directory
cd ${HPC_PATH}

# Create necessary directories
mkdir -p logs outputs

# Verify everything is present
ls -lh
# Should see:
#   hybrid_chunking.sif
#   run_chunking.slurm
#   run_chunking_parallel.slurm
#   run_chunking_highmem.slurm
#   documents/
#   logs/
#   outputs/
```

---

## Running Jobs

### Option 1: Basic Single Job (Recommended for First Run)

**When to use:**
- First-time testing
- Processing small batches (< 10 files)
- Standard-sized documents

**Resources:**
- 16GB RAM
- 4 CPU cores
- 2 hour time limit

```bash
# Submit job
sbatch run_chunking.slurm

# Monitor job
squeue -u $USER

# Check output when done
cat logs/chunking_*.log
ls -lh outputs/
```

### Option 2: Parallel Processing (Best for Large Batches)

**When to use:**
- Processing many documents (10+)
- Want faster total completion time
- Have many compute nodes available

**Resources per task:**
- 16GB RAM per task
- 4 CPU cores per task
- 1 hour per task
- Max 4 concurrent tasks

```bash
# Count your files first
NUM_FILES=$(find documents/knowledge -name "*.pdf" | wc -l)
echo "Number of files: $NUM_FILES"

# Edit the script to match file count
# Change line: #SBATCH --array=0-9%4
# To:          #SBATCH --array=0-14%4  (if you have 15 files)

nano run_chunking_parallel.slurm

# Submit parallel job array
sbatch run_chunking_parallel.slurm

# Monitor all array tasks
squeue -u $USER

# Check specific task log
cat logs/chunking_<JOBID>_0.log  # First task
cat logs/chunking_<JOBID>_1.log  # Second task
```

### Option 3: High-Memory Processing (For Large/Complex Documents)

**When to use:**
- Standard job fails with "Out of Memory"
- Processing scanned PDFs with OCR
- Large technical documents (100+ pages)
- Documents with many complex tables

**Resources:**
- 24GB RAM (50% more than standard)
- 8 CPU cores (faster processing)
- 4 hour time limit

```bash
# Submit high-memory job
sbatch run_chunking_highmem.slurm

# Monitor
squeue -u $USER

# Check output
cat logs/chunking_hm_*.log
```

---

## Monitoring Jobs

### Check Job Queue Status

```bash
# View your jobs
squeue -u $USER

# View detailed job info
scontrol show job <JOBID>

# View specific job array task
scontrol show job <JOBID>_<TASKID>
```

### Monitor Running Job

```bash
# Watch logs in real-time
tail -f logs/chunking_*.log

# For job arrays, pick specific task
tail -f logs/chunking_<JOBID>_0.log
```

### Check Job History

```bash
# View completed jobs (last 24 hours)
sacct -u $USER --starttime=now-1day

# Detailed info for specific job
sacct -j <JOBID> --format=JobID,JobName,State,ExitCode,MaxRSS,Elapsed

# Check why job failed
sacct -j <JOBID> --format=JobID,State,ExitCode,DerivedExitCode
```

### Cancel Jobs

```bash
# Cancel specific job
scancel <JOBID>

# Cancel all your jobs
scancel -u $USER

# Cancel specific task in job array
scancel <JOBID>_<TASKID>

# Cancel range of array tasks
scancel <JOBID>_[0-5]
```

---

## Troubleshooting

### Issue: Job Fails with "Out of Memory"

**Symptoms:**
```
SLURM: error: Exceeded job memory limit
Exit code: 137 or 247
```

**Solutions:**
```bash
# Option A: Use high-memory script
sbatch run_chunking_highmem.slurm

# Option B: Request even more memory
# Edit SLURM script:
#SBATCH --mem=32G

# Option C: Process fewer files at once
# Split documents into smaller batches
mkdir documents/knowledge/batch1
mkdir documents/knowledge/batch2
# Move half the files to batch2
```

### Issue: Job Sits in Queue (PENDING state)

**Check why:**
```bash
squeue -u $USER -t PENDING -o "%.18i %.9P %.8j %.8u %.2t %.10M %.6D %R"
```

**Common reasons:**
- `(Resources)`: Waiting for available nodes
- `(Priority)`: Other jobs have higher priority
- `(QOSMaxMemoryPerUser)`: Exceeded memory quota
- `(PartitionTimeLimit)`: Requested time too long

**Solutions:**
- Reduce memory requirement if possible
- Reduce time limit if possible
- Use different partition: `#SBATCH --partition=short`
- Cancel other running jobs if you have many

### Issue: "Module 'singularity' not found"

**Symptoms:**
```
ModuleCmd_Load.c(208):ERROR:105: Unable to locate a modulefile for 'singularity'
```

**Solutions:**
```bash
# List available modules
module avail

# Try common alternatives
module load apptainer
module load singularityce
module load containers/singularity

# If nothing works, ask your HPC support for the correct module name
```

### Issue: Models Not Found at Runtime

**Symptoms:**
```
HuggingFace Hub connection error
Model not found: sentence-transformers/all-MiniLM-L6-v2
```

**Cause:** Models weren't pre-cached during build (internet was unavailable)

**Solutions:**
```bash
# Option A: Rebuild container with internet access

# Option B: Use custom cache directory on HPC scratch space
export HF_HOME=/scratch/$USER/.cache/huggingface
singularity run \
  -B $HF_HOME:/opt/models \
  -B $PWD/documents:/app/documents \
  -B $PWD/outputs:/app/outputs \
  hybrid_chunking.sif
```

### Issue: Permission Denied Errors

**Symptoms:**
```
Permission denied: '/opt/models'
Permission denied: '/app/outputs'
```

**Solutions:**
```bash
# Ensure bind mounts point to writable locations
singularity run \
  -B $PWD/documents:/app/documents:ro \
  -B $PWD/outputs:/app/outputs:rw \
  -B $PWD/.cache:/opt/models:rw \
  hybrid_chunking.sif

# Create directories with correct permissions
mkdir -p outputs logs .cache
chmod 755 outputs logs .cache
```

### Issue: Job Output Files Empty or Missing

**Check:**
```bash
# Verify job completed successfully
sacct -j <JOBID> --format=JobID,State,ExitCode

# Check error log for issues
cat logs/chunking_*.err

# Verify input files are accessible
singularity exec hybrid_chunking.sif ls /app/documents/knowledge/

# Manually test container
singularity run \
  -B $PWD/documents:/app/documents \
  -B $PWD/outputs:/app/outputs \
  hybrid_chunking.sif
```

---

## Performance Tips

### Optimize Resource Requests

```bash
# Check actual memory usage from completed job
sacct -j <JOBID> --format=JobID,MaxRSS,ReqMem

# If MaxRSS is much lower than ReqMem, reduce memory request
# Example: If MaxRSS=12GB but ReqMem=24GB, use --mem=16G next time
```

### Parallel Processing Best Practices

```bash
# Good: Process 20 files with 4 concurrent jobs
#SBATCH --array=0-19%4

# Better: Process in smaller time windows
#SBATCH --array=0-19%8
#SBATCH --time=00:30:00

# Best: Balance concurrency with cluster load
# Check current load first:
sinfo
```

### Adjust CPU Threads

```bash
# If CPU usage is low, reduce cores
#SBATCH --cpus-per-task=2

# If processing is CPU-bound, increase
#SBATCH --cpus-per-task=8
export OMP_NUM_THREADS=8
```

---

## Example Workflows

### Workflow 1: Process All SONiC Documentation

```bash
# 1. Upload documents
scp -r documents/knowledge/ ${HPC_USER}@${HPC_HOST}:${HPC_PATH}/documents/

# 2. SSH to HPC
ssh ${HPC_USER}@${HPC_HOST}
cd ${HPC_PATH}

# 3. Check file count
find documents/knowledge -name "*.pdf" | wc -l
# Output: 6 files

# 4. Submit basic job (sufficient for 6 files)
sbatch run_chunking.slurm

# 5. Monitor
watch squeue -u $USER

# 6. When complete, download results
exit
scp -r ${HPC_USER}@${HPC_HOST}:${HPC_PATH}/outputs/ ./
```

### Workflow 2: Process 50 Large Technical Manuals

```bash
# 1. Use parallel processing for speed
cd ${HPC_PATH}

# 2. Edit parallel script for 50 files
nano run_chunking_parallel.slurm
# Change: #SBATCH --array=0-49%8

# 3. Use high-memory config for large files
nano run_chunking_parallel.slurm
# Change: #SBATCH --mem=20G

# 4. Submit
sbatch run_chunking_parallel.slurm

# 5. Monitor progress
watch 'squeue -u $USER; echo ""; ls -1 outputs/ | wc -l'

# 6. Check for failures
sacct -u $USER --starttime=now-1hour --format=JobID,State,ExitCode | grep FAIL
```

### Workflow 3: Iterative Processing with Adjustments

```bash
# 1. Test with one file first
mkdir documents/knowledge/test
cp documents/knowledge/large_manual.pdf documents/knowledge/test/

# 2. Run basic job
sbatch run_chunking.slurm

# 3. Check memory usage
sacct -j <JOBID> --format=MaxRSS
# Output: MaxRSS=18GB (exceeds 16GB!)

# 4. Rerun with high-memory config
sbatch run_chunking_highmem.slurm

# 5. Success! Now process all files
rm -rf documents/knowledge/test
sbatch run_chunking_highmem.slurm
```

---

## Getting Help

### HPC System Information

```bash
# Check SLURM configuration
scontrol show config | grep -i memory
scontrol show config | grep -i time

# View available partitions
sinfo -o "%20P %5a %.10l %.6D %.6c %.10m %N"

# Check your account limits
sacctmgr show assoc user=$USER format=user,account,partition,maxjobs,maxsubmit
```

### Contact Your HPC Support Team

Include this information when reporting issues:
1. Job ID: `<JOBID>`
2. Script used: `run_chunking.slurm`
3. Error log: `logs/chunking_<JOBID>.err`
4. Memory usage: `sacct -j <JOBID> --format=MaxRSS`
5. Node where it ran: From `scontrol show job <JOBID>`

---

## Summary of Scripts

| Script | Use Case | Resources | Max Files |
|--------|----------|-----------|-----------|
| `run_chunking.slurm` | Standard processing | 16GB, 4 CPUs, 2h | 10-20 |
| `run_chunking_parallel.slurm` | Large batches | 16GB each, 4 CPUs, 1h | Unlimited |
| `run_chunking_highmem.slurm` | Complex documents | 24GB, 8 CPUs, 4h | 20-30 |

---

**For detailed configuration options, see:**
- Container build: `singularity.def`
- Project documentation: `CLAUDE.md`
- Docling configuration: `hybrid_chunking.py`
