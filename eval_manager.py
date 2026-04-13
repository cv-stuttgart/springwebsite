#!/usr/bin/env python
"""
Evaluation Manager Script

This script helps manage the evaluation processes using memory-optimized evaluation.
Usage: python eval_manager.py [status|kill|run <entry_id>]
"""

import os
import sys
import django
import subprocess
import signal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'springwebsite.settings')
django.setup()

from springeval.models import ResultEntry

def check_evaluation_status():
    """Check the status of evaluation processes"""
    print("=== Evaluation Process Status ===")
    
    # Check for running evaluation processes
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        eval_processes = []
        for line in lines:
            if 'python manage.py update_evaluation' in line or 'run_optimized_eval.py' in line:
                eval_processes.append(line)
        
        if eval_processes:
            print("Running evaluation processes:")
            for proc in eval_processes:
                print(f"  {proc}")
        else:
            print("No evaluation processes currently running.")
            
    except Exception as e:
        print(f"Error checking processes: {e}")
    
    print("\n=== Database Status ===")
    
    # Check WAIT_PROC entries
    wait_proc_entries = ResultEntry.objects.filter(process_status='WAIT_PROC')
    print(f"Entries in WAIT_PROC status: {wait_proc_entries.count()}")
    
    for entry in wait_proc_entries:
        print(f"  ID: {entry.id}, Type: {entry.method_type}, Name: {entry.name}, Created: {entry.pub_date}")
    
    # Check recent entries
    print(f"\nRecent entries (last 5):")
    recent_entries = ResultEntry.objects.all().order_by('-pub_date')[:5]
    for entry in recent_entries:
        print(f"  ID: {entry.id}, Type: {entry.method_type}, Status: {entry.process_status}, Name: {entry.name}")

def kill_evaluation_processes():
    """Kill all running evaluation processes"""
    print("=== Killing Evaluation Processes ===")
    
    try:
        # Find evaluation processes
        result = subprocess.run(['pgrep', '-f', 'update_evaluation'], capture_output=True, text=True)
        pids = result.stdout.strip().split('\n')
        
        killed_count = 0
        for pid in pids:
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"Killed process {pid}")
                    killed_count += 1
                except ProcessLookupError:
                    print(f"Process {pid} already terminated")
                except Exception as e:
                    print(f"Error killing process {pid}: {e}")
        
        if killed_count == 0:
            print("No evaluation processes found to kill.")
        else:
            print(f"Killed {killed_count} evaluation processes.")
            
    except Exception as e:
        print(f"Error killing processes: {e}")

def run_manual_evaluation(entry_id):
    """Run memory-optimized evaluation for a specific entry"""
    print(f"=== Running Memory-Optimized Evaluation for Entry {entry_id} ===")
    
    # Check if entry exists
    try:
        entry = ResultEntry.objects.get(id=entry_id)
        print(f"Found entry: {entry.name} (Type: {entry.method_type})")
        
        if entry.method_type != "SF":
            print(f"ERROR: Entry {entry_id} is not a sceneflow method")
            return False
            
    except ResultEntry.DoesNotExist:
        print(f"ERROR: Entry {entry_id} not found")
        return False
    
    # Run the memory-optimized evaluation script
    script_path = os.path.join(os.path.dirname(__file__), 'run_optimized_eval.py')
    cmd = [sys.executable, script_path, str(entry_id)]
    
    print(f"Running command: {' '.join(cmd)}")
    print("This will use the memory-optimized evaluation approach.")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Memory-optimized evaluation completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Memory-optimized evaluation failed with exit code: {e.returncode}")
        return False
    except Exception as e:
        print(f"Error running memory-optimized evaluation: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python eval_manager.py [status|kill|run <entry_id>]")
        print("  status - Check current evaluation status")
        print("  kill   - Kill all running evaluation processes")
        print("  run <entry_id> - Run memory-optimized evaluation for specific entry")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        check_evaluation_status()
    elif command == "kill":
        kill_evaluation_processes()
    elif command == "run":
        if len(sys.argv) != 3:
            print("Usage: python eval_manager.py run <entry_id>")
            sys.exit(1)
        try:
            entry_id = int(sys.argv[2])
            run_manual_evaluation(entry_id)
        except ValueError:
            print("ERROR: Entry ID must be an integer")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: status, kill, run")
        sys.exit(1)

if __name__ == "__main__":
    main()
