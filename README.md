# COMP3014 Network Simulation Project Part C: Light Reproducibility Analysis

## 1. Project Overview
This project focuses on **verifying the reproducibility of network simulations** using NS2. It involves:
- Running 5 independent simulations for 4 TCP algorithms (Cubic, Reno, Yeah, Vegas) with different random seeds.
- Calculating key metrics (Goodput, Packet Loss Rate) and their 95% confidence intervals.
- Automating the entire workflow (simulation → analysis → visualization) via a Shell script.


## 2. Directory Structure
```
comp3014j/
├── cubicCode.tcl      # NS2 script for TCP Cubic scenario
├── renoCode.tcl       # NS2 script for TCP Reno scenario
├── yeahCode.tcl       # NS2 script for TCP Yeah scenario
├── vegasCode.tcl      # NS2 script for TCP Vegas scenario
├── run_partC.sh       # Automated workflow script (runs simulations + analysis)
├── analyser_partC.py  # Python script for statistical analysis + visualization
├── partC_results/     # Output directory (CSV files, trace/NAM files)
└── partC_plots/       # Output directory (visualization plots)
```


## 3. Dependencies
To run this project, you need:
- **NS2** (Network Simulator 2) – Install on Ubuntu/Debian with:
  ```bash
  sudo apt-get install ns2
  ```
- **Python 3** – Install via:
  ```bash
  sudo apt-get install python3
  ```
- **Python Libraries**:
  ```bash
  pip3 install matplotlib numpy pandas scipy
  ```


## 4. Quick Start
1. **Run the automated workflow**:
   ```bash
   chmod +x run_partC.sh  # Make script executable
   ./run_partC.sh         # Start simulations + analysis
   ```

2. **View results**:
   - Statistical summary: `partC_results/partC_statistical_summary.csv`
   - Raw seed-level data: `partC_results/partC_individual_seed_runs.csv`
   - Visualizations: `partC_plots/partC_mean_ci_results.png` (mean + 95% CI) and `partC_plots/partC_seed_variability.png` (seed-level variability)


## 5. Component Details

### 5.1 NS2 Scenario Scripts (`*.tcl`)
- Define the network topology (bottleneck link: 1000Mb/s, 50ms delay) and TCP configurations.
- Accept command-line arguments for **random seed**, **trace file path**, and **NAM file path** (for visualization).


### 5.2 Automated Workflow (`run_partC.sh`)
- Runs 5 simulations for each TCP algorithm (4 algorithms × 5 seeds = 20 total runs).
- Automatically invokes `analyser_partC.py` after simulations.
- Archives trace/NAM files in `partC_results/`.


### 5.3 Analysis & Visualization (`analyser_partC.py`)
- **Parses trace files** to extract Goodput (throughput) and Packet Loss Rate (PLR).
- **Calculates statistics**: Mean, standard deviation, and 95% confidence intervals (using t-distribution for small samples).
- **Generates visualizations**:
  - `partC_mean_ci_results.png`: Compares mean Goodput/PLR across algorithms with error bars.
  - `partC_seed_variability.png`: Shows metric variability across different random seeds.


## 6. Results Interpretation

### 6.1 CSV Files
- `partC_statistical_summary.csv`:
  - Columns: `TCP_Algorithm`, `Valid_Runs_Count`, `Goodput_Mean_Mbps`, `Goodput_Std_Mbps`, `Goodput_95CI_Lower_Mbps`, `Goodput_95CI_Upper_Mbps`, `PLR_Mean_Percent`, `PLR_Std_Percent`, `PLR_95CI_Lower_Percent`, `PLR_95CI_Upper_Percent`.
  - Example:
    | TCP_Algorithm | Goodput_Mean_Mbps | Goodput_95CI_Lower_Mbps | Goodput_95CI_Upper_Mbps | PLR_Mean_Percent |
    |---------------|-------------------|-------------------------|-------------------------|------------------|
    | CUBIC         | 0.2541            | 0.2470                  | 0.2612                  | 0.6225           |

- `partC_individual_seed_runs.csv`:
  - Raw data for each seed run (e.g., `CUBIC Seed 12345: Goodput = 0.2556 Mbps, PLR = 0.6001%`).


### 6.2 Visualizations
- `partC_mean_ci_results.png`:
  - Left subplot: Goodput (Mbps) with 95% confidence intervals.
  - Right subplot: Packet Loss Rate (%) with 95% confidence intervals.
- `partC_seed_variability.png`:
  - Left subplot: Goodput variability across different random seeds.
  - Right subplot: PLR variability across different random seeds.


## 7. Notes & Troubleshooting
- **NS2 Compatibility**: Ensure your NS2 version supports `Agent/TCP/Linux` and `Agent/TCPSink/Sack1`.
- **Path Mismatches**: If trace files are not found, check `analyser_partC.py`’s `self.trace_dir` (should point to `./partC_results`).
- **Seed Consistency**: The same random seeds (`12345, 23456, 34567, 45678, 56789`) are used across all simulations for reproducibility.
- **Dependency Issues**: If Python libraries are missing, run `pip3 install matplotlib numpy pandas scipy`.


## 8. Conclusion
This project demonstrates how to validate the reproducibility of network simulations using statistical metrics and automated workflows. The generated results (CSVs, plots) can be used to compare TCP algorithm performance and ensure consistent behavior across independent runs.
