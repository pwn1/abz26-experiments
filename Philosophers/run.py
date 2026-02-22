#!/bin/env python3

import json
import subprocess
import os
import time
import itertools
import re
import logging
import sys

from rich.logging import RichHandler
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TimeElapsedColumn, 
    MofNCompleteColumn,
    TaskProgressColumn
)

# --- Configuration ---
path_to_refines = "refines"
template_file = "phil.csp"  # The source file with placeholders
log_file_name = "phil.log"

# Define the permissible values
parameters = {
    'phil': [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]
}

# Map the parameter keys to the string constants of the .csp file
const_map = {
    'phil': 'PHILOSOPHERS'
}

# --- Logging Setup ---
# Create a logger
log = logging.getLogger("fdr_sweep")
log.setLevel(logging.INFO)

# 1. Rich Handler for Terminal Output (with colors)
shell_handler = RichHandler(rich_tracebacks=True, show_path=False)
shell_handler.setLevel(logging.INFO)

# 2. File Handler for Disk Output (clean text)
file_handler = logging.FileHandler(log_file_name, mode='w')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)

# Add both handlers to the logger
log.addHandler(shell_handler)
log.addHandler(file_handler)

def run_fdr(file_path, current_params, progress):
    # Add an indeterminate spinner subtask
    sub_task = progress.add_task(
        f"  [grey50]Checking {os.path.basename(file_path)}...", 
        total=None
    )
    
    start_time = time.perf_counter()
    
    fdr_process = subprocess.Popen(
        [path_to_refines, "--format=json", file_path],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )

    try:
        stdout, stderr = fdr_process.communicate()
    except KeyboardInterrupt:
        fdr_process.terminate()
        raise
    finally:
        progress.remove_task(sub_task)

    duration = time.perf_counter() - start_time

    try:
        parsed_data = json.loads(stdout)
        
        if parsed_data.get("errors"):
            log.error(f"[bold red]Errors in {file_path}[/]")
            for err in parsed_data["errors"]:
                msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
                log.error(f"  → {msg}")
            return None, duration

        results = parsed_data.get("results", [])
        if results:
            for res in results:
                status = "[green]PASS[/]" if res.get("result") == 1 else "[red]FAIL[/]"
                log.info(f"{os.path.basename(file_path)}: {status} ({duration:.2f}s)")
        else:
            log.warning(f"No assertions in {file_path}")

        parsed_data['time'] = duration
        parsed_data['parameters'] = current_params
        
        output_filename = os.path.splitext(file_path)[0] + ".json"
        with open(output_filename, 'w') as f:
            json.dump(parsed_data, f, indent=4)
            
        return parsed_data, duration

    except json.JSONDecodeError:
        log.critical(f"Malformed JSON from FDR for {file_path}")
        return None, duration

def generate_and_run():

    if not os.path.exists(template_file):
        log.error(f"Template file '{template_file}' not found.")
        return

    start_index = 0
    if len(sys.argv) > 1:
        try:
            # We assume 0-based indexing for the command line
            start_index = int(sys.argv[1])
        except ValueError:
            log.error("Invalid index provided. Starting from 0.")

    with open(template_file, 'r') as f:
        template_content = f.read()

    keys = list(parameters.keys())
    values = list(parameters.values())
    combinations = list(itertools.product(*values))
    total_count = len(combinations)

    if start_index >= total_count:
        log.error(f"Start index {start_index} is out of range (Total combinations: {total_count})")
        return

    log.info(f"=== Starting Sweep at Index {start_index} of {total_count} ===")

    # We use standard columns only to ensure maximum compatibility
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
    ) as progress:
        
        main_task = progress.add_task(
            "[cyan]Total Progress (Starting...)", 
            total=len(combinations)
        )

        main_task = progress.add_task("[cyan]Total Progress", total=total_count, completed=start_index)

        for i in range(start_index, total_count):
            combo = combinations[i]
            current_params = dict(zip(keys, combo))
            new_content = template_content

            for key, val in current_params.items():
                const_name = const_map[key]
                pattern = rf"({const_name}\s*=\s*)[0-9a-zA-Z\._]+"
                replacement = rf"\g<1>{val}"
                new_content = re.sub(pattern, replacement, new_content)

            param_str = "_".join([f"{k}{v}" for k, v in current_params.items()])
            new_filename = f"run_{param_str}.csp"
            
            with open(new_filename, 'w') as f:
                f.write(new_content)

            # Execution
            _, duration = run_fdr(new_filename, current_params, progress)
            
            # Update the description directly to show the timing of the last run
            progress.update(
                main_task, 
                advance=1, 
                description=f"[cyan]Total Progress [blue]({duration:.2f}s)"
            )

            progress.update(main_task, advance=1, description=f"[cyan]Total Sweep [blue]({duration:.2f}s last)")
            log.info(f"PROGRESS: {i+1}/{total_count} ({(i+1)/total_count*100:.1f}%) complete.")

        log.info("=== Sweep Complete ===")

if __name__ == "__main__":
    generate_and_run()