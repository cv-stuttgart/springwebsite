# Memory-Optimized Scene Flow Evaluation Scripts

This directory contains scripts to manually run sceneflow evaluations using memory-optimized processing when the automatic system is not working as expected.

## Scripts Overview

### 1. `eval_manager.py` - Main Management Script
This is the main script that provides various commands to manage evaluations.

**Usage:**
```bash
python eval_manager.py [command]
```

**Available Commands:**
- `status` - Check current evaluation status and running processes
- `kill` - Kill all running evaluation processes
- `run <entry_id>` - Run memory-optimized evaluation for a specific entry

### 2. `run_optimized_eval.py` - Direct Memory-Optimized Evaluation Script
This script directly evaluates a sceneflow method by entry ID using memory-optimized processing.

**Usage:**
```bash
python run_optimized_eval.py <entry_id>
```

### 3. `memory_optimized_evaluation.py` - Core Memory-Optimized Functions
This module contains the memory-optimized evaluation functions that process data in chunks to minimize memory usage.

## How to Use

### Check Current Status
```bash
# Using the bash wrapper (recommended)
./run_manual_eval.sh status

# Or directly with Python
cd /code/springwebsite
source venv/bin/activate
source /code/springwebsite/springwebsite/load_spring_env.sh
python eval_manager.py status
```

### Kill Running Evaluations
If you need to stop the automatic evaluation process:
```bash
./run_manual_eval.sh kill
```

### Run Memory-Optimized Evaluation
To manually evaluate a sceneflow method using memory-optimized processing:
```bash
# For entry ID 252 (the current stuck one)
./run_manual_eval.sh run 252

# Or directly using the memory-optimized script
python run_optimized_eval.py 252

# Or through the eval manager
python eval_manager.py run 252
```

## Important Notes

1. **Memory Requirements**: The memory-optimized evaluation significantly reduces memory usage by processing data in chunks. While still requiring substantial memory (8-12GB RAM), it's more efficient than the standard approach.

2. **Time Requirements**: Memory-optimized evaluation may take longer (45-90 minutes) due to chunked processing, but it's more reliable on systems with limited memory.

3. **File Requirements**: The script will check that all required files exist:
   - `upload__<entry_id>__<hash>__disp1.hdf5`
   - `upload__<entry_id>__<hash>__disp2.hdf5`
   - `upload__<entry_id>__<hash>__flow.hdf5`

4. **Database Updates**: The script will update the database entry status from WAIT_PROC to SUCCESS upon completion, or to FAIL if an error occurs.

5. **Output**: Results are saved to the database and output images are saved to `/code/spring_imgfiles/media/<hash>/`

6. **Memory Optimization**: The evaluation processes data in chunks and includes garbage collection to minimize memory usage throughout the process.

## Troubleshooting

### If the automatic system is running
The automatic evaluation system (`run_evaluation.sh`) runs continuously. If you see a process running, you can:
1. Wait for it to complete (it may take a long time)
2. Kill it with `./run_manual_eval.sh kill` and run manually
3. Let it continue running (it should complete eventually)

### If files are missing
The script will check for required files and report any missing ones. Make sure all three files (disp1, disp2, flow) are present in the upload directory.

### If evaluation fails
Check the error output for specific issues. Common problems:
- Insufficient memory (even with optimization)
- Corrupted input files
- Missing ground truth files
- Database connection issues
- Memory allocation errors during chunked processing

## Example Workflow

1. Check current status:
   ```bash
   ./run_manual_eval.sh status
   ```

2. If there's a stuck evaluation, kill it:
   ```bash
   ./run_manual_eval.sh kill
   ```

3. Run memory-optimized evaluation:
   ```bash
   ./run_manual_eval.sh run 252
   ```

4. Monitor progress (the script will show detailed output including memory usage and chunk processing)

5. Check status again to confirm completion:
   ```bash
   ./run_manual_eval.sh status
   ```

## Current Status

As of the last check, entry ID 252 (MS-M-FUSE) is in WAIT_PROC status and there may be an automatic evaluation process running. You can use these scripts to either monitor the automatic process or run a memory-optimized evaluation if needed.

## Memory Optimization Features

The memory-optimized evaluation includes several features to reduce memory usage:

1. **Chunked Data Reading**: Large datasets are read in configurable chunks (default 10M elements)
2. **Garbage Collection**: Explicit garbage collection after each major operation
3. **Memory Monitoring**: Real-time memory usage reporting throughout the process
4. **Efficient Data Types**: Uses float16 where possible to reduce memory footprint
5. **Progressive Processing**: Data is processed and released in stages to minimize peak memory usage
