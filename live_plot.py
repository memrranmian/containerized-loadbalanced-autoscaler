import os
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

METRICS_FILE = "metrics.csv"
EXPERIMENT_FILE = "experiment_metrics.csv"
OUTPUT_IMAGE = "live_dashboard.png"
TEMP_IMAGE = "live_dashboard_tmp.png"
UPDATE_INTERVAL = 3

def parse_timestamp(df, col_name='timestamp'):
    df[col_name] = pd.to_datetime(df[col_name], format='%d-%m-%Y %H:%M:%S', errors='coerce')
    return df.dropna(subset=[col_name]).sort_values(col_name)

def update_dashboard():
    if not os.path.exists(METRICS_FILE) or os.stat(METRICS_FILE).st_size == 0:
        return

    try:
        df_sys = pd.read_csv(
            METRICS_FILE,
            header=None,
            names=['timestamp', 'containers', 'cpu', 'memory'],
            on_bad_lines='skip'
        )
        df_sys = parse_timestamp(df_sys, 'timestamp')
    except Exception:
        return

    if df_sys.empty:
        return

    df_exp = pd.DataFrame()
    if os.path.exists(EXPERIMENT_FILE) and os.stat(EXPERIMENT_FILE).st_size > 0:
        try:
            df_exp = pd.read_csv(
                EXPERIMENT_FILE,
                header=None,
                names=['timestamp', 'req_rate', 'resp_time'],
                on_bad_lines='skip'
            )
            df_exp = parse_timestamp(df_exp, 'timestamp')
        except Exception:
            df_exp = pd.DataFrame()

    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
    plt.subplots_adjust(hspace=0.25)

    # Panel 1: Request Rate
    if not df_exp.empty and 'req_rate' in df_exp.columns:
        axes[0].plot(df_exp['timestamp'], df_exp['req_rate'], color='blue', marker='o', markersize=3, label='Request Rate (req/s)')
        axes[0].legend(loc='upper left', fontsize=8)
    axes[0].set_ylabel("Req Rate (req/s)", fontsize=9)
    axes[0].grid(True, linestyle='--', alpha=0.6)

    # Panel 2: CPU Utilization
    axes[1].plot(df_sys['timestamp'], df_sys['cpu'], color='orange', label='Avg CPU (%)')
    axes[1].axhline(y=70, color='red', linestyle='--', linewidth=1.2, label='Scale-Out Threshold (70%)')
    axes[1].axhline(y=30, color='green', linestyle='--', linewidth=1.2, label='Scale-In Threshold (30%)')
    axes[1].set_ylabel("CPU (%)", fontsize=9)
    axes[1].set_ylim(0, 105)
    axes[1].legend(loc='upper left', fontsize=8)
    axes[1].grid(True, linestyle='--', alpha=0.6)

    # Panel 3: Response Time
    if not df_exp.empty and 'resp_time' in df_exp.columns:
        axes[2].plot(df_exp['timestamp'], df_exp['resp_time'], color='red', marker='o', markersize=3, label='Avg Response Time (ms)')
        axes[2].legend(loc='upper left', fontsize=8)
    axes[2].set_ylabel("Response Time (ms)", fontsize=9)
    axes[2].grid(True, linestyle='--', alpha=0.6)

    # Panel 4: Containers
    axes[3].plot(df_sys['timestamp'], df_sys['containers'], color='purple', marker='s', markersize=3, label='Running Containers')
    axes[3].set_ylabel("Containers", fontsize=9)
    axes[3].set_xlabel("Time", fontsize=9)
    axes[3].set_ylim(0.5, 4.5)
    axes[3].set_yticks([1, 2, 3, 4])
    axes[3].legend(loc='upper left', fontsize=8)
    axes[3].grid(True, linestyle='--', alpha=0.6)

    fig.autofmt_xdate()

    try:
        fig.savefig(TEMP_IMAGE, bbox_inches='tight', dpi=100)
        plt.close(fig)
        os.replace(TEMP_IMAGE, OUTPUT_IMAGE)
        print(f"[{time.strftime('%H:%M:%S')}] Updated {OUTPUT_IMAGE}")
    except Exception as e:
        plt.close(fig)
        if os.path.exists(TEMP_IMAGE):
            try:
                os.remove(TEMP_IMAGE)
            except OSError:
                pass
        print(f"Skipped frame due to file access lock: {e}")

def main():
    print(f"Live plotter running. Updating '{OUTPUT_IMAGE}' every {UPDATE_INTERVAL}s...")
    while True:
        try:
            update_dashboard()
        except Exception as err:
            print(f"Error updating plot: {err}")
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
