#!/bin/bash

# Part C: Light Reproducibility - Automated Simulation and Analysis Script

echo "=== Starting Part C: Light Reproducibility Analysis ==="

# Create directories for results
mkdir -p partC_results
mkdir -p partC_plots

# Define different seeds for 5 runs
SEEDS=(12345 23456 34567 45678 56789)
SCENARIOS=("cubic" "reno" "yeah" "vegas")

echo "Running 5 simulations with different seeds..."

# Run simulations for each seed
for i in {0..4}; do
    echo "--- Simulation $((i+1)) with seed ${SEEDS[i]} ---"
    
    # Run all TCP variants with the current seed
    for scenario in "${SCENARIOS[@]}"; do
        echo "Running $scenario with seed ${SEEDS[i]}..."
        ns ${scenario}Code.tcl ${SEEDS[i]}
        # Rename trace files to avoid overwriting
        mv ${scenario}Trace.tr partC_results/${scenario}_run$((i+1)).tr
    done
done

echo "All simulations completed!"

# Run the Part C analyser
echo "Running Part C analysis..."
python3 analyser_partC.py

echo "=== Part C Complete ==="
echo "Results saved in partC_results/ directory"
echo "Plots saved in partC_plots/ directory"
