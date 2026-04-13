#!/usr/bin/env python
"""
Run Memory-Optimized Scene Flow Evaluation

This script uses the memory-optimized evaluation function to process
sceneflow methods with minimal memory usage.
"""

import os
import sys
import django
import traceback
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'springwebsite.settings')
django.setup()

from springeval.models import ResultEntry
from memory_optimized_evaluation import evaluate_submission_sceneflow_optimized

def run_optimized_evaluation(entry_id):
    """Run memory-optimized evaluation for a sceneflow method"""
    
    print(f"Starting memory-optimized evaluation for entry ID: {entry_id}")
    print(f"Timestamp: {datetime.now()}")
    print("-" * 60)
    
    try:
        # Get the result entry
        entry = ResultEntry.objects.get(id=entry_id)
        print(f"Found entry: {entry.name} (Type: {entry.method_type})")
        
        if entry.method_type != "SF":
            print(f"ERROR: Entry {entry_id} is not a sceneflow method (type: {entry.method_type})")
            return False
        
        # Check files exist
        imghash = entry.imghash.hex
        UPLOAD_DIRECTORY = os.environ["SPRING_UPLOADDIR"]
        IMG_DIR = os.path.join(os.environ["SPRING_IMGDIR"], "media")
        
        file_d1 = os.path.join(UPLOAD_DIRECTORY, f"upload__{entry_id}__{imghash}__disp1.hdf5")
        file_d2 = os.path.join(UPLOAD_DIRECTORY, f"upload__{entry_id}__{imghash}__disp2.hdf5")
        file_fl = os.path.join(UPLOAD_DIRECTORY, f"upload__{entry_id}__{imghash}__flow.hdf5")
        
        # Check files exist
        missing_files = []
        for file_path, name in zip([file_d1, file_d2, file_fl], ["disp1", "disp2", "flow"]):
            if not os.path.exists(file_path):
                missing_files.append(name)
            else:
                size_mb = os.path.getsize(file_path) / (1024*1024)
                print(f"{name} file: {size_mb:.1f}MB")
        
        if missing_files:
            print(f"ERROR: Missing required files: {', '.join(missing_files)}")
            return False
        
        # Set up output directory
        outputimgdir = os.path.join(IMG_DIR, imghash)
        print(f"Output directory: {outputimgdir}")
        
        # Update status
        entry.process_status = "WAIT_PROC"
        entry.save()
        
        print("\nStarting memory-optimized evaluation...")
        print("This version processes data in chunks to minimize memory usage.")
        print("It may take longer but should be more memory-efficient.")
        
        start_time = datetime.now()
        
        try:
            # Run the memory-optimized evaluation
            results = evaluate_submission_sceneflow_optimized(file_d1, file_d2, file_fl, outputimgdir)
            
            end_time = datetime.now()
            
            print(f"\nEvaluation completed successfully!")
            print(f"Start time: {start_time}")
            print(f"End time: {end_time}")
            print(f"Duration: {end_time - start_time}")
            
            # Update database with results
            print("Updating database with results...")
            for k, v in results.items():
                setattr(entry, k, v)
            entry.process_status = "SUCCESS"
            entry.save()
            
            print(f"Results saved to database for entry {entry_id}")
            print(f"Output images saved to: {outputimgdir}")
            
            return True
            
        except MemoryError as e:
            print(f"MEMORY ERROR: {str(e)}")
            print("The evaluation ran out of memory despite optimizations.")
            print("This sceneflow method may be too large for this system.")
            entry.process_status = "FAIL"
            entry.save()
            return False
            
        except Exception as e:
            print(f"ERROR during evaluation: {str(e)}")
            print("\nFull traceback:")
            print(traceback.format_exc())
            entry.process_status = "FAIL"
            entry.save()
            return False
        
    except ResultEntry.DoesNotExist:
        print(f"ERROR: Entry with ID {entry_id} not found in database")
        return False
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_optimized_eval.py <entry_id>")
        print("Example: python run_optimized_eval.py 252")
        sys.exit(1)
    
    try:
        entry_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: Entry ID must be an integer")
        sys.exit(1)
    
    success = run_optimized_evaluation(entry_id)
    
    if success:
        print("\n" + "="*60)
        print("MEMORY-OPTIMIZED EVALUATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("MEMORY-OPTIMIZED EVALUATION FAILED!")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
