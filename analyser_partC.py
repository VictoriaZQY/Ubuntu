import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import os

class PartCAnalyser:
    def __init__(self):
        self.runs = 5
        self.scenarios = ["cubic", "reno", "yeah", "vegas"]
        self.results = {}

    def parse_trace_file(self, filename):
        """Read and understand the simulation result files"""
        lines = []
        try:
            with open(filename, 'r') as file:
                for line in file:
                    lines.append(line.split())
        except FileNotFoundError:
            print(f"Warning: File {filename} not found")

            return None
        return lines

    def calculate_goodput(self, data):
        """Calculate how much data was successfully delivered"""
        if not data:
            return 0

        total_acks = 0
        for line in data:
            if 'ack_' in line and len(line) > 1:
                # Count ACK packets (successfully delivered)
                total_acks += 1

        # Convert to Mbps (Internet speed measurement)
        simulation_time = 100.0  # 100 seconds
        goodput_mbps = (total_acks * 1000 * 8) / (simulation_time * 1e6)
        return goodput_mbps


    def calculate_plr(self, data):
        """Calculate how many packets were lost"""
        if not data:
            return 0

        total_packets = 0
        lost_packets = 0
        
        for line in data:
            if len(line) < 2:
                continue

            if line[0] == 'd':  # 'd' means packet was dropped
                lost_packets += 1
            elif 'ack_' in line or 'tcp' in line:  # Packet was sent
                total_packets += 1

        if total_packets + lost_packets == 0:
            return 0
            
        plr = (lost_packets / (total_packets + lost_packets)) * 100
        return plr

    def collect_all_results(self):
        """Gather results from all 5 runs"""
        print("Collecting results from all runs...")

        for scenario in self.scenarios:
            self.results[scenario] = {
                'goodput': [],
                'plr': []
            }

            for run in range(1, self.runs + 1):
                filename = f"partC_results/{scenario}_run{run}.tr"
                data = self.parse_trace_file(filename)


                if data:
                    goodput = self.calculate_goodput(data)
                    plr = self.calculate_plr(data)
                    
                    self.results[scenario]['goodput'].append(goodput)
                    self.results[scenario]['plr'].append(plr)

                    print(f"  {scenario} Run {run}: Goodput = {goodput:.4f} Mbps, PLR = {plr:.2f}%")
                else:
                    # Use zeros if file not found
                    self.results[scenario]['goodput'].append(0)
                    self.results[scenario]['plr'].append(0)
                    print(f"  {scenario} Run {run}: No data found")

    def calculate_statistics(self):
        """Calculate average and confidence ranges"""
        stats_summary = {}
        
        for scenario in self.scenarios:
            goodputs = self.results[scenario]['goodput']
            plrs = self.results[scenario]['plr']

            # Calculate average and variation
            goodput_mean = np.mean(goodputs)
            goodput_std = np.std(goodputs, ddof=1)
        
            plr_mean = np.mean(plrs)
            plr_std = np.std(plrs, ddof=1)


            # Calculate 95% confidence interval (where we're 95% sure the true value lies)
            if len(goodputs) > 1:
                goodput_ci = stats.t.interval(0.95, len(goodputs)-1, 
                                            loc=goodput_mean, 
                                            scale=goodput_std/np.sqrt(len(goodputs)))
                plr_ci = stats.t.interval(0.95, len(plrs)-1,
                                    loc=plr_mean,
                                    scale=plr_std/np.sqrt(len(plrs)))
            else:
                goodput_ci = (goodput_mean, goodput_mean)
                plr_ci = (plr_mean, plr_mean)

            stats_summary[scenario] = {
                'goodput_mean': goodput_mean,
                'goodput_std': goodput_std,
                'goodput_ci_lower': goodput_ci[0],
                'goodput_ci_upper': goodput_ci[1],
                'plr_mean': plr_mean,
                'plr_std': plr_std,
                'plr_ci_lower': plr_ci[0],
                'plr_ci_upper': plr_ci[1]
            }

            print(f"\n{scenario.upper()} Statistics:")
            print(f"  Goodput: {goodput_mean:.4f} ± {(goodput_ci[1]-goodput_mean):.4f} Mbps")
            print(f"  PLR: {plr_mean:.2f} ± {(plr_ci[1]-plr_mean):.2f}%")
    
        return stats_summary

    def create_visualizations(self, stats_summary):
        """Create charts showing the results with better layout"""
    
        # Prepare data for plotting
        scenarios = list(stats_summary.keys())
        goodput_means = [stats_summary[s]['goodput_mean'] for s in scenarios]
        goodput_errors = [[stats_summary[s]['goodput_mean'] - stats_summary[s]['goodput_ci_lower'] 
                          for s in scenarios],
                         [stats_summary[s]['goodput_ci_upper'] - stats_summary[s]['goodput_mean'] 
                          for s in scenarios]]

        plr_means = [stats_summary[s]['plr_mean'] for s in scenarios]
        plr_errors = [[stats_summary[s]['plr_mean'] - stats_summary[s]['plr_ci_lower'] 
                      for s in scenarios],
                     [stats_summary[s]['plr_ci_upper'] - stats_summary[s]['plr_mean'] 
                      for s in scenarios]]

        # Create figure with two charts - larger size and more spacing
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(25, 10))

        # Define colors for better visual distinction
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        
        # Chart 1: Goodput with confidence intervals
        x_pos = np.arange(len(scenarios))
        width = 0.6  # Bar width

        bars1 = ax1.bar(x_pos, goodput_means, width=width, yerr=goodput_errors, 
                       capsize=10, alpha=0.8, color=colors, edgecolor='black', linewidth=1)

        ax1.set_xlabel('TCP Algorithms', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Goodput (Mbps)', fontsize=14, fontweight='bold')
        ax1.set_title('Goodput Comparison with 95% Confidence Intervals\n(5 Runs Each)', 
                     fontsize=14, fontweight='bold', pad=25)
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels([s.upper() for s in scenarios], fontsize=13, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='y')

        # Adjust Y-axis limits for goodput to provide space for labels
        max_goodput = max(goodput_means) if max(goodput_means) > 0 else 0.1
        ax1.set_ylim(0, max_goodput * 1.35)  # 35% headroom for labels
        
        # Add value labels on bars with better positioning
        for i, bar in enumerate(bars1):
            height = bar.get_height()
            error_margin = goodput_errors[1][i]  # Use upper error for positioning

            # Position label just above the error bar with small margin
            label_height = height + error_margin + 0.1
            ax1.text(bar.get_x() + bar.get_width()/2., label_height,
                    f'{height:.4f}\n±{error_margin:.4f}', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.9, edgecolor='gray'))

        # Chart 2: PLR with confidence intervals
        bars2 = ax2.bar(x_pos, plr_means, width=width, yerr=plr_errors,
                       capsize=10, alpha=0.8, color=colors, edgecolor='black', linewidth=1)
        
        ax2.set_xlabel('TCP Algorithms', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
        ax2.set_title('Packet Loss Rate with 95% Confidence Intervals \n(5 Runs Each)', 
                     fontsize=14, fontweight='bold', pad=25)
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels([s.upper() for s in scenarios], fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')

        # Adjust Y-axis limits for PLR to provide space for labels
        max_plr = max(plr_means) if max(plr_means) > 0 else 5
        ax2.set_ylim(0, max_plr * 1.5)  # 50% headroom for PLR labels
        
        # Add value labels on bars with better positioning for PLR
        for i, bar in enumerate(bars2):
            height = bar.get_height()
            error_margin = plr_errors[1][i]  # Use upper error for positioning

            # Position label just above the error bar
            label_height = height + error_margin + 0.1
            ax2.text(bar.get_x() + bar.get_width()/2., label_height,
                    f'{height:.2f}%\n±{error_margin:.2f}%', 
                    ha='center', va='bottom', fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor='lightyellow', alpha=0.9, edgecolor='gray'))

        # Add overall figure title
        fig.suptitle('TCP Algorithm Performance: Reproducibility Analysis (5 Runs)', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Adjust layout with more spacing between subplots
        plt.tight_layout()
        plt.subplots_adjust(top=0.88, bottom=0.12, wspace=0.35)  # Increased spacing

        # Save with high quality
        plt.savefig('partC_plots/partC_reproducibility_results.png', dpi=300, bbox_inches='tight', 
                    facecolor='white', edgecolor='none')
        plt.show()
        
        # Also create individual run results plot with better layout
        self.plot_individual_runs()

    def plot_individual_runs(self):
        """Plot individual run results to show variability with better layout"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        markers = ['o', 's', '^', 'D']
        line_styles = ['-', '--', '-.', ':']

        for i, scenario in enumerate(self.scenarios):
            goodputs = self.results[scenario]['goodput']
            plrs = self.results[scenario]['plr']

            # Plot goodput for each run
            ax1.plot(range(1, self.runs + 1), goodputs, 
                    marker=markers[i], linewidth=3, markersize=12, 
                    label=scenario.upper(), color=colors[i], linestyle=line_styles[i],
                    markeredgecolor='black', markeredgewidth=1)

            # Plot PLR for each run
            ax2.plot(range(1, self.runs + 1), plrs,
                    marker=markers[i], linewidth=3, markersize=12, 
                    label=scenario.upper(), color=colors[i], linestyle=line_styles[i],
                    markeredgecolor='black', markeredgewidth=1)

        # Configure first subplot
        ax1.set_xlabel('Run Number', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Goodput (Mbps)', fontsize=14, fontweight='bold')
        ax1.set_title('Goodput Variability Across 5 Runs', fontsize=16, fontweight='bold', pad=20)
        ax1.legend(fontsize=12, loc='best', framealpha=0.9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xticks(range(1, self.runs + 1))
        ax1.tick_params(axis='both', which='major', labelsize=12)

        # Configure second subplot
        ax2.set_xlabel('Run Number', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Packet Loss Rate (%)', fontsize=14, fontweight='bold')
        ax2.set_title('PLR Variability Across 5 Runs', fontsize=16, fontweight='bold', pad=20)
        ax2.legend(fontsize=12, loc='best', framealpha=0.9)
        ax2.grid(True, alpha=0.3)
        ax2.set_xticks(range(1, self.runs + 1))
        ax2.tick_params(axis='both', which='major', labelsize=12)

        # Add overall title
        fig.suptitle('Individual Run Performance: TCP Algorithm Consistency', 
                    fontsize=18, fontweight='bold', y=0.98)
        
        # Adjust layout
        plt.tight_layout()
        plt.subplots_adjust(top=0.90, wspace=0.3)

        plt.savefig('partC_plots/partC_individual_runs.png', dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
        plt.show()

    def save_results_to_csv(self, stats_summary):
        """Save all results to files"""
        
        # Save statistical summary
        summary_data = []
        for scenario in self.scenarios:
            summary_data.append({
                'Algorithm': scenario.upper(),
                'Goodput_Mean_Mbps': stats_summary[scenario]['goodput_mean'],
                'Goodput_Std': stats_summary[scenario]['goodput_std'],
                'Goodput_CI_Lower': stats_summary[scenario]['goodput_ci_lower'],
                'Goodput_CI_Upper': stats_summary[scenario]['goodput_ci_upper'],
                'PLR_Mean_Percent': stats_summary[scenario]['plr_mean'],
                'PLR_Std': stats_summary[scenario]['plr_std'],
                'PLR_CI_Lower': stats_summary[scenario]['plr_ci_lower'],
                'PLR_CI_Upper': stats_summary[scenario]['plr_ci_upper']
            })

        summary_df = pd.DataFrame(summary_data)
        summary_df.to_csv('partC_results/partC_statistical_summary.csv', index=False)

        # Save individual run results
        individual_data = []
        for scenario in self.scenarios:
            for run in range(self.runs):
                individual_data.append({
                    'Algorithm': scenario.upper(),
                    'Run': run + 1,
                    'Goodput_Mbps': self.results[scenario]['goodput'][run],
                    'PLR_Percent': self.results[scenario]['plr'][run]
                })

        individual_df = pd.DataFrame(individual_data)
        individual_df.to_csv('partC_results/partC_individual_runs.csv', index=False)
        
        print("\nResults saved to CSV files:")
        print("  - partC_results/partC_statistical_summary.csv")
        print("  - partC_results/partC_individual_runs.csv")

    def run_analysis(self):
        """Main method to run complete Part C analysis"""
        print("=== Part C: Light Reproducibility Analysis ===")
        
        # Step 1: Collect results from all runs
        self.collect_all_results()

        # Step 2: Calculate statistics
        print("\n" + "="*50)
        print("STATISTICAL ANALYSIS")
        print("="*50)
        stats_summary = self.calculate_statistics()

        # Step 3: Create visualizations
        print("\n" + "="*50)
        print("GENERATING VISUALIZATIONS")
        print("="*50)
        self.create_visualizations(stats_summary)

        # Step 4: Save results
        print("\n" + "="*50)
        print("SAVING RESULTS")
        print("="*50)
        self.save_results_to_csv(stats_summary)
        
        print("\n=== Part C Analysis Complete ===")


# Run the analysis
if __name__ == "__main__":
    analyser = PartCAnalyser()
    analyser.run_analysis()
