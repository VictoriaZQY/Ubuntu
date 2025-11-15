#!/bin/bash

# Prevents silent failures (e.g., missing TCL files, failed ns runs)
set -euo pipefail

# Part C: Light Reproducibility - Automated Simulation and Analysis Script

echo "=== Starting Part C: Light Reproducibility Analysis ==="

# Create directories for results
mkdir -p partC_results
mkdir -p partC_plots
echo "Created output directories: partC_results/ | partC_plots/"

# Define different seeds for 5 runs
SEEDS=(12345 23456 34567 45678 56789)
SCENARIOS=("cubic" "reno" "yeah" "vegas")
WORK_DIR="./"  # Root directory for TCL scripts/trace file generation

echo -e "\n Running 5 simulations (1 per seed: ${SEEDS[*]})"

# Run simulations for each seed
for seed_idx in "${!SEEDS[@]}"; do
    current_seed=${SEEDS[seed_idx]}
    simulation_num=$((seed_idx + 1))  # run number (1-5)
    echo -e "\n--- Simulation $simulation_num / 5 | Seed: $current_seed ---"
    
    # Run all TCP variants with the current seed
    for scenario in "${SCENARIOS[@]}"; do
        # Define TCL script path and output file names
        tcl_script="${scenario}Code.tcl"
        trace_file="${scenario}_seed${current_seed}.tr"  # TCL generates this file
        nam_file="${scenario}_seed${current_seed}.nam"    # TCL generates this file
        trace_path="${WORK_DIR}/${trace_file}"
        nam_path="${WORK_DIR}/${nam_file}"

        # Validate TCL script exists before running
        if [ ! -f "$tcl_script" ]; then
            echo "ERROR: TCL script not found -> $tcl_script"
            exit 1  # Exit script if critical file is missing
        fi

        echo "Running: ns $tcl_script $current_seed $trace_path $nam_path"
        ns "$tcl_script" "$current_seed" "$trace_path" "$nam_path"

        if [ ! -f "$trace_path" ]; then
            echo "ERROR: Trace file not generated -> $trace_path"
            echo "Check $tcl_script for CLI argument handling or simulation errors"
            exit 1
        fi
        echo "Successfully generated: $trace_file | $nam_file"
    done
done

echo -e "\n All 5 simulations (20 total runs: 5 seeds × 4 TCP algos) completed!"

# Run the Part C analyser
echo "Running Part C analysis..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Install Python 3 to continue."
    exit 1
fi
if [ ! -f "analyser_partC.py" ]; then
    echo "ERROR: Analyser script not found -> analyser_partC.py"
    exit 1
fi

python3 analyser_partC.py

echo -e "\n Backing up trace/NAM files to partC_results/"
for scenario in "${SCENARIOS[@]}"; do
    for seed in "${SEEDS[@]}"; do
        # Backup trace file if it exists
        trace_file="${scenario}_seed${seed}.tr"
        if [ -f "$trace_file" ]; then
            mv "$trace_file" "partC_results/"
        fi

        # Backup NAM file if it exists (for optional visualization later)
        nam_file="${scenario}_seed${seed}.nam"
        if [ -f "$nam_file" ]; then
            mv "$nam_file" "partC_results/"
        fi
    done
done
echo "All trace/NAM files backed up to partC_results/"


# Final completion message
echo -e "=== Part C Analysis Complete ==="
echo "Results stored in: partC_results/"
echo "   - partC_statistical_summary.csv (mean/CI stats)"
echo "   - partC_individual_seed_runs.csv (per-seed raw data)"
echo "   - Backup trace/NAM files ({scenario}_seed{seed}.tr/.nam)"
echo -e "Plots stored in: partC_plots/"
echo "   - partC_mean_ci_results.png (mean + 95% CI)"
echo "   - partC_seed_variability.png (per-seed variability)"
echo "==================================================="
