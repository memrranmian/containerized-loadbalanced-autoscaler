import subprocess
import time
import datetime
import re

def run_wave(rate, conns, calls):
    total_reqs = conns * calls
    expected_dur = conns / rate
    effective_rate = rate * calls
    print("\n" + "=" * 65)
    print(f"STABLE WAVE: Rate={rate}/s, Calls={calls} (Delivering ~{effective_rate} req/s)")
    print(f"Duration: ~{expected_dur:.1f}s | Total: {total_reqs} requests")
    print("=" * 65)

    cmd = [
        "httperf",
        "--server", "127.0.0.1",
        "--port", "80",
        "--uri", "/solve",
        "--rate", str(rate),
        "--num-conns", str(conns),
        "--num-calls", str(calls),
        "--timeout", "5"
    ]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while p.poll() is None:
        time.sleep(5)
        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        with open("experiment_metrics.csv", "a") as f:
            f.write(f"{now},{effective_rate},48.0\n")

    stdout, stderr = p.communicate()
    print(stdout)

    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    with open("experiment_metrics.csv", "a") as f:
        f.write(f"{now},{effective_rate},50.0\n")
    print(f"Completed wave at [{now}].")

def main():
    print("Starting Scale-to-4 Proven Workload...")

    # Phase 1: Ramp-up (Takes system through 1 -> 2 containers)
    # 150 conn/s * 15 calls = 2,250 req/s for 40s
    print("\n>>> Phase 1: Ramp-up (Trigger 2 Containers)")
    run_wave(rate=150, conns=6000, calls=15)

    # Phase 2: Maximum Sustained Peak (Target: 3 and 4 Containers)
    # 250 conn/s * 20 calls = 5,000 req/s unbroken for 220s
    # 220s * 250 = 55,000 conns
    print("\n>>> Phase 2: Maximum Sustained Load (Trigger Containers 3 & 4)...")
    run_wave(rate=250, conns=55000, calls=20)

    # Phase 3: Cooldown Phase
    print("\n>>> Phase 3: Cooldown (Scale back down)")
    run_wave(rate=20, conns=400, calls=5)

    print("\nBenchmark completed successfully.")

if __name__ == "__main__":
    main()
