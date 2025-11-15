import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import os

class PartCAnalyser:
    def __init__(self):
        self.SEEDS = [12345, 23456, 34567, 45678, 56789]  # Matches run_partC.sh seed list
        self.scenarios = ["cubic", "reno", "yeah", "vegas"]
        self.results = {}
        # Configurable paths (match TCL/Shell output locations)
        self.trace_dir = "./partC_results"  # Trace files generated here by TCL scripts
        self.output_csv_dir = "./partC_results"
        self.output_plot_dir = "./partC_plots"
        # Ensure output directories exist
        os.makedirs(self.output_csv_dir, exist_ok=True)
        os.makedirs(self.output_plot_dir, exist_ok=True)
        self.simulation_time = 100.0  # Fixed simulation time (matches TCL: 100s)
        self.packet_size = 1000  # Fixed packet size (matches TCL: 1000 bytes)


    def parse_trace_file(self, filename):
        """Read and understand the simulation result files"""
        lines = []
        try:
            with open(filename, 'r') as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line:  # Skip empty lines
                        lines.append(stripped_line.split())
        except FileNotFoundError:
            print(f"WARNING: Trace file not found -> {filename}")
            return None
        except PermissionError:
            print(f"ERROR: Permission denied when reading -> {filename}")
            return None
        return lines

    def calculate_goodput(self, data):
        """Calculate how much data was successfully delivered"""
        if not data:
            return 0.0

        source_maxseq = {}  # Dictionary: {tcp_source_id: max_seq_value}
        # Extract max TCP sequence number (from "maxseq_" trace lines in TCL)
        for line in data:
            # Skip lines without enough fields for maxseq_ (needs at least 7 fields: 0-6)
            if len(line) < 7:
                continue
        
            # Skip lines that are not maxseq_ traces
            if line[5] != "maxseq_":
                continue

            try:
                tcp_source_id = line[1].strip()  # Get TCP source ID (distinguishes source1/source2)
                current_seq = int(line[6])       # Get current maxseq_ value (index 6)
            
                # Skip invalid negative maxseq_ values (-1 = uninitialized)
                if current_seq < 0:
                    continue

                # Update maxseq_ for this source: keep the largest value
                if tcp_source_id not in source_maxseq or current_seq > source_maxseq[tcp_source_id]:
                    source_maxseq[tcp_source_id] = current_seq

            except (ValueError, IndexError):
                # Skip lines with invalid seq numbers or missing fields
                continue

        # Calculate TOTAL maxseq_ (sum of maxseq_ from all valid TCP sources)
        total_maxseq = sum(source_maxseq.values()) if source_maxseq else 0

        # Calculate Goodput (valid only if total_maxseq > 0)
        if total_maxseq == 0:
            return 0.0
        # Goodput formula: (total_bytes * 8) / (simulation_time * 1e6)
        # total_bytes = total_maxseq * packet_size (1000 bytes = data size per packet, matches TCL)
        total_bytes = total_maxseq * self.packet_size
        goodput_mbps = (total_bytes * 8) / (self.simulation_time * 1e6)

        # Round to 4 decimal places (avoid 0.0000 due to rounding tiny values)
        return round(goodput_mbps, 4)


    def calculate_plr(self, data):
        """Calculate how many packets were lost"""
        if not data:
            return 0

        sent_packets = 0
        dropped_packets = 0
        
        for line in data:
            if len(line) < 5:
                continue
            event_type = line[0].strip()  # Event type: '+' (enqueue), '-' (dequeue), 'd' (drop), 'r' (receive)
            protocol = line[4].strip()    # Protocol: 'tcp' (we only care about TCP)

            # Count SENT packets: NS2 uses '+' (packet enqueued for sending) OR '-' (packet dequeued/sent)
            # Use '-' for stricter counting (only packets that actually left the queue)
            if (event_type == '-' or event_type == '+') and protocol == "tcp":
                sent_packets += 1
        
            # Count DROPPED packets: NS2 uses 'd' for dropped packets
            elif event_type == 'd' and protocol == "tcp":
                dropped_packets += 1

        # Avoid division by zero (no TCP traffic)
        if sent_packets == 0:
            print("Warning: No sent TCP packets detected (check event type/protocol indices)")
            return np.nan  # Use NaN to indicate invalid PLR (not 0, which is misleading)
    
        plr = (dropped_packets / sent_packets) * 100
        return round(plr, 4)

    def collect_all_results(self):
        print("=== Collecting Results from Seed-Based Runs ===")
        print(f"Trace file directory: {self.trace_dir}")
        print(f"Seeds used: {self.SEEDS}\n")

        for scenario in self.scenarios:
            self.results[scenario] = {
                'goodput': [],
                'plr': [],
                'seeds': self.SEEDS  # Track which seed corresponds to which result
            }

            for seed in self.SEEDS:
                # TCL-generated filename: {scenario}_seed{seed}.tr (e.g., cubic_seed12345.tr)
                trace_filename = f"{scenario}_seed{seed}.tr"
                trace_path = os.path.join(self.trace_dir, trace_filename)
                data = self.parse_trace_file(trace_path)


                if data:
                    goodput = self.calculate_goodput(data)
                    plr = self.calculate_plr(data)
                    self.results[scenario]['goodput'].append(goodput)
                    self.results[scenario]['plr'].append(plr)
                    print(f"  {scenario.upper()} (Seed {seed}): Goodput = {goodput} Mbps, PLR = {plr}%")
                else:
                    # Use NaN instead of 0 to indicate missing data (avoids misleading stats)
                    self.results[scenario]['goodput'].append(np.nan)
                    self.results[scenario]['plr'].append(np.nan)
                    print(f"  {scenario.upper()} (Seed {seed}): NO VALID DATA")

    def calculate_statistics(self):
        """Calculate average and confidence ranges"""
        stats_summary = {}
        
        for scenario in self.scenarios:
            # Extract results and remove NaN (missing data)
            goodputs = [gp for gp in self.results[scenario]['goodput'] if not np.isnan(gp)]
            plrs = [pl for pl in self.results[scenario]['plr'] if not np.isnan(pl)]

            # Calculate basic stats (skip if no valid data)
            if len(goodputs) == 0:
                stats_summary[scenario] = self._empty_stats()
                continue
            if len(plrs) == 0:
                stats_summary[scenario] = self._empty_stats()
                continue


            # Mean and standard deviation (ddof=1 = sample standard deviation)
            goodput_mean = np.mean(goodputs)
            goodput_std = np.std(goodputs, ddof=1)
            plr_mean = np.mean(plrs)
            plr_std = np.std(plrs, ddof=1)

            # 95% Confidence Interval (t-distribution for small sample size: n=5)
            goodput_ci = stats.t.interval(
                alpha=0.95,
                df=len(goodputs)-1,  # Degrees of freedom = sample size - 1
                loc=goodput_mean,
                scale=goodput_std / np.sqrt(len(goodputs))  # Standard error
            )
            plr_ci = stats.t.interval(
                alpha=0.95,
                df=len(plrs)-1,
                loc=plr_mean,
                scale=plr_std / np.sqrt(len(plrs))
            )


            # Store rounded stats (for readability)
            stats_summary[scenario] = {
                'goodput_mean': round(goodput_mean, 4),
                'goodput_std': round(goodput_std, 4),
                'goodput_ci_lower': round(goodput_ci[0], 4),
                'goodput_ci_upper': round(goodput_ci[1], 4),
                'plr_mean': round(plr_mean, 4),
                'plr_std': round(plr_std, 4),
                'plr_ci_lower': round(plr_ci[0], 4),
                'plr_ci_upper': round(plr_ci[1], 4),
                'valid_runs': len(goodputs)  # Track how many runs had valid data
            }

            # Print stats (user-friendly format)
            print(f"\n{scenario.upper()} Statistics (Valid Runs: {len(goodputs)}/5):")
            print(f"  Goodput: {goodput_mean:.4f} ± {(goodput_ci[1]-goodput_mean):.4f} Mbps")
            print(f"  PLR: {plr_mean:.4f} ± {(plr_ci[1]-plr_mean):.4f}%")
    
        return stats_summary

    def _empty_stats(self):
        """Helper: Return empty stats dict for scenarios with no valid data"""
        return {
            'goodput_mean': np.nan, 'goodput_std': np.nan,
            'goodput_ci_lower': np.nan, 'goodput_ci_upper': np.nan,
            'plr_mean': np.nan, 'plr_std': np.nan,
            'plr_ci_lower': np.nan, 'plr_ci_upper': np.nan,
            'valid_runs': 0
        }

    def create_visualizations(self, stats_summary):
        """Create charts showing the results with better layout"""
    
        # Prepare data for plotting
        scenarios = list(stats_summary.keys())
        scenario_labels = [s.upper() for s in scenarios]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Matplotlib default colors
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))  # Single figure creation (fixed duplicate)


        # Extract mean and CI data (skip NaN)
        goodput_means = [stats_summary[s]['goodput_mean'] for s in scenarios]
        goodput_ci_err = [
            [stats_summary[s]['goodput_mean'] - stats_summary[s]['goodput_ci_lower'] for s in scenarios],
            [stats_summary[s]['goodput_ci_upper'] - stats_summary[s]['goodput_mean'] for s in scenarios]
        ]

        plr_means = [stats_summary[s]['plr_mean'] for s in scenarios]
        plr_ci_err = [
            [stats_summary[s]['plr_mean'] - stats_summary[s]['plr_ci_lower'] for s in scenarios],
            [stats_summary[s]['plr_ci_upper'] - stats_summary[s]['plr_mean'] for s in scenarios]
        ]
        
        # Plot 1: Goodput with confidence intervals
        x_pos = np.arange(len(scenarios))
        bars1 = ax1.bar(
            x_pos, goodput_means, yerr=goodput_ci_err,
            capsize=8, alpha=0.7, color=colors, edgecolor='black'
        )
        ax1.set_xlabel('TCP Algorithms', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Goodput (Mbps)', fontsize=12, fontweight='bold')
        ax1.set_title('Goodput with 95% Confidence Intervals\n(5 Seed-Based Runs)', fontsize=14, fontweight='bold')
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(scenario_labels)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim(0, 0.3)

        # Add value labels on bars
        for bar, mean in zip(bars1, goodput_means):
            if not np.isnan(mean):
                ax1.text(
                    bar.get_x() + bar.get_width()/2, bar.get_height() + 0.002,
                    f'{mean:.4f}', ha='center', va='bottom', fontsize=10
                )

        # Plot 2: PLR with confidence intervals
        bars2 = ax2.bar(
            x_pos, plr_means, yerr=plr_ci_err,
            capsize=8, alpha=0.7, color=colors, edgecolor='black'
        )
        ax2.set_xlabel('TCP Algorithms', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Packet Loss Rate (%)', fontsize=12, fontweight='bold')
        ax2.set_title('Packet Loss Rate with 95% Confidence Intervals\n(5 Seed-Based Runs)', fontsize=14, fontweight='bold')
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(scenario_labels)
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim(0, 1)
        # Add value labels on bars
        for bar, mean in zip(bars2, plr_means):
            if not np.isnan(mean):
                ax2.text(
                    bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f'{mean:.4f}%', ha='center', va='bottom', fontsize=10
                )
        
        plt.tight_layout()
        mean_plot_path = os.path.join(self.output_plot_dir, "partC_mean_ci_results.png")
        plt.savefig(mean_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"\nMean + CI plot saved to: {mean_plot_path}")

        # Plot 2: Individual Seed Run Results (for variability check)
        self.plot_individual_seed_runs()


    def plot_individual_seed_runs(self):
        """Plot goodput/PLR for each seed (replaces run numbers with actual seeds)"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        markers = ['o', 's', '^', 'D']  # Distinct markers for each algorithm
        
        for idx, scenario in enumerate(self.scenarios):
            # Extract data (goodput, PLR, seeds)
            goodputs = self.results[scenario]['goodput']
            plrs = self.results[scenario]['plr']
            seeds = self.results[scenario]['seeds']

            # Subplot 1: Goodput per seed
            ax1.plot(
                seeds, goodputs, marker=markers[idx], linewidth=2, markersize=8,
                label=scenario.upper(), color=colors[idx], alpha=0.8
            )
            # Subplot 2: PLR per seed
            ax2.plot(
                seeds, plrs, marker=markers[idx], linewidth=2, markersize=8,
                label=scenario.upper(), color=colors[idx], alpha=0.8
            )

        # Configure Goodput subplot
        ax1.set_xlabel('Random Seed', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Goodput (Mbps)', fontsize=12, fontweight='bold')
        ax1.set_title('Goodput Variability Across Seeds\n(Each Seed = 1 Independent Run)', fontsize=14, fontweight='bold')
        ax1.legend(loc='best', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(seeds)  # Show all seed values on x-axis
        ax1.set_ylim(0, 0.3)
        # Configure PLR subplot
        ax2.set_xlabel('Random Seed', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Packet Loss Rate (%)', fontsize=12, fontweight='bold')
        ax2.set_title('PLR Variability Across Seeds\n(Each Seed = 1 Independent Run)', fontsize=14, fontweight='bold')
        ax2.legend(loc='best', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(seeds)  # Show all seed values on x-axis
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        seed_plot_path = os.path.join(self.output_plot_dir, "partC_seed_variability.png")
        plt.savefig(seed_plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Seed variability plot saved to: {seed_plot_path}")

    def save_results_to_csv(self, stats_summary):
        """Save all results to files"""
        
        # Save statistical summary
        summary_rows = []
        for scenario in self.scenarios:
            stats = stats_summary[scenario]
            summary_rows.append({
                'TCP_Algorithm': scenario.upper(),
                'Valid_Runs_Count': stats['valid_runs'],
                'Goodput_Mean_Mbps': stats['goodput_mean'],
                'Goodput_Std_Mbps': stats['goodput_std'],
                'Goodput_95CI_Lower_Mbps': stats['goodput_ci_lower'],
                'Goodput_95CI_Upper_Mbps': stats['goodput_ci_upper'],
                'PLR_Mean_Percent': stats['plr_mean'],
                'PLR_Std_Percent': stats['plr_std'],
                'PLR_95CI_Lower_Percent': stats['plr_ci_lower'],
                'PLR_95CI_Upper_Percent': stats['plr_ci_upper']
            })
        summary_df = pd.DataFrame(summary_rows)
        summary_csv_path = os.path.join(self.output_csv_dir, "partC_statistical_summary.csv")
        summary_df.to_csv(summary_csv_path, index=False)

        # Save individual run results
        individual_rows = []
        for scenario in self.scenarios:
            for seed_idx, seed in enumerate(self.SEEDS):
                individual_rows.append({
                    'TCP_Algorithm': scenario.upper(),
                    'Random_Seed': seed,
                    'Run_Number': seed_idx + 1,  # Optional: 1-5 run number for reference
                    'Goodput_Mbps': self.results[scenario]['goodput'][seed_idx],
                    'PLR_Percent': self.results[scenario]['plr'][seed_idx]
                })
        individual_df = pd.DataFrame(individual_rows)
        individual_csv_path = os.path.join(self.output_csv_dir, "partC_individual_seed_runs.csv")
        individual_df.to_csv(individual_csv_path, index=False)

        print("\nResults saved to CSV:")
        print(f"  - {summary_csv_path}")
        print(f"  - {individual_csv_path}")

    def run_analysis(self):
        """Main workflow: Collect → Analyze → Visualize → Save"""
        print("="*60)
        print("=== Part C: Light Reproducibility Analysis ===")
        print("="*60)

        # Step 1: Collect data from seed-based runs
        self.collect_all_results()

        # Step 2: Calculate statistical metrics
        print("\n" + "="*50)
        print("STATISTICAL ANALYSIS (95% Confidence Interval)")
        print("="*50)
        stats_summary = self.calculate_statistics()

        # Step 3: Generate visualizations
        print("\n" + "="*50)
        print("GENERATING VISUALIZATIONS")
        print("="*50)
        self.create_visualizations(stats_summary)

        # Step 4: Save results to CSV
        print("\n" + "="*50)
        print("SAVING RESULTS TO CSV FILES")
        print("="*50)
        self.save_results_to_csv(stats_summary)

        print("\n" + "="*60)
        print("=== Part C Analysis Complete ===")
        print(f"All outputs stored in:\n  - {self.output_csv_dir}\n  - {self.output_plot_dir}")
        print("="*60)


# Execute analysis when script is run directly
if __name__ == "__main__":
    analyser = PartCAnalyser()
    analyser.run_analysis()
