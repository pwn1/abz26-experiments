#!/usr/bin/env python3
import json
import os
import sys
import csv
from rich.console import Console
from rich.table import Table

def summarise():
    # Help message
    if len(sys.argv) < 2:
        print("Usage: ./summarise.py <param> [--hide-context] [--format csv|latex|table|markdown]")
        return

    target_param = sys.argv[1]
    
    # Robust check for the hide-context flag
    show_context = True
    if "--hide-context" in sys.argv:
        show_context = False
    
    # Detect format choice
    out_format = "table"
    if "--format" in sys.argv:
        try:
            out_format = sys.argv[sys.argv.index("--format") + 1].lower()
        except (IndexError, ValueError):
            out_format = "table"

    console = Console()
    json_files = [f for f in os.listdir('.') if f.endswith('.json') and f.startswith('run_')]
    data_rows = []

    for file_name in json_files:
        try:
            with open(file_name, 'r') as f:
                data = json.load(f)
            params = data.get('parameters', {})
            if target_param in params:
                results_list = data.get('results', [])
                results = results_list[0] if results_list else {}
                data_rows.append({
                    'val': params[target_param],
                    'states': results.get('visited_states', 0),
                    'transitions': results.get('visited_transitions', 0),
                    'time': data.get('time', 0),
                    'others': ", ".join([f"{k}:{v}" for k, v in params.items() if k != target_param])
                })
        except: continue

    # Sort logic
    try:
        data_rows.sort(key=lambda x: float(x['val']))
    except:
        data_rows.sort(key=lambda x: str(x['val']))

    # --- Output Logic ---

    if out_format == "csv":
        writer = csv.writer(sys.stdout)
        header = [target_param, "States", "Transitions", "Time"]
        if show_context: header.append("Context")
        writer.writerow(header)
        for r in data_rows:
            row = [r['val'], r['states'], r['transitions'], f"{r['time']:.2f}"]
            if show_context: row.append(r['others'])
            writer.writerow(row)

    elif out_format == "latex":
        cols = "lrrr" + ("l" if show_context else "")
        print(f"\\begin{{tabular}}{{{cols}}}")
        print(f"{target_param} & States & Transitions & Time " + ("& Context " if show_context else "") + "\\\\ \\hline")
        for r in data_rows:
            line = f"{r['val']} & {r['states']:,} & {r['transitions']:,} & {r['time']:.2f}s"
            if show_context: line += f" & \\small{{{r['others']}}}"
            print(line + " \\\\")
        print("\\end{tabular}")

    elif out_format == "markdown":
        header = f"| {target_param} | States | Transitions | Time |"
        sep = "|---:|---:|---:|---:|"
        if show_context:
            header += " Context |"
            sep += "---|"
        print(header)
        print(sep)
        for r in data_rows:
            line = f"| {r['val']} | {r['states']:,} | {r['transitions']:,} | {r['time']:.2f}s |"
            if show_context: line += f" {r['others']} |"
            print(line)

    else: # Default: Rich Table
        table = Table(title=f"FDR Metric Summary: {target_param}")
        table.add_column(target_param, justify="right", style="cyan")
        table.add_column("States", justify="right", style="magenta")
        table.add_column("Transitions", justify="right", style="magenta")
        table.add_column("Time", justify="right", style="green")
        
        if show_context:
            table.add_column("Other Parameters (Context)", style="dim")
        
        for r in data_rows:
            row = [str(r['val']), f"{r['states']:,}", f"{r['transitions']:,}", f"{r['time']:.2f}s"]
            if show_context:
                row.append(r['others'])
            table.add_row(*row)
        console.print(table)

if __name__ == "__main__":
    summarise()