import subprocess
import time
import datetime
import os

MAX_CONTAINERS = 4
MIN_CONTAINERS = 1
SCALE_OUT_THRESHOLD = 70.0
SCALE_IN_THRESHOLD = 30.0
CHECK_INTERVAL = 15

CONTAINER_IMAGE = "quadratic-solver"
NETWORK_NAME = "cc-network"
METRICS_FILE = "metrics.csv"

NGINX_CONF_TEMPLATE = """events {
    worker_connections 1024;
}

http {
    upstream backend_servers {
%s
    }

    server {
        listen 80;

        location / {
            proxy_pass http://backend_servers;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
"""

def get_running_containers():
    try:
        out = subprocess.check_output(
            ["docker", "ps", "--filter", "name=app-instance-", "--format", "{{.Names}}"],
            text=True
        )
        names = [n.strip() for n in out.strip().split("\n") if n.strip()]
        return sorted(names)
    except Exception as e:
        print(f"Error getting containers: {e}")
        return ["app-instance-1"]

def get_cpu_and_mem_stats(container_names):
    if not container_names:
        return 0.0, 0.0

    total_cpu = 0.0
    total_mem = 0.0
    valid_count = 0

    for name in container_names:
        try:
            out = subprocess.check_output(
                ["docker", "stats", name, "--no-stream", "--format", "{{.CPUPerc}},{{.MemPerc}}"],
                text=True
            ).strip()
            parts = out.split(",")
            if len(parts) == 2:
                cpu_val = float(parts[0].replace("%", "").strip())
                mem_val = float(parts[1].replace("%", "").strip())
                total_cpu += cpu_val
                total_mem += mem_val
                valid_count += 1
        except Exception:
            pass

    if valid_count == 0:
        return 0.0, 0.0
    return total_cpu / valid_count, total_mem / valid_count

def update_nginx(running_containers):
    servers = "\n".join([f"        server {c}:5000;" for c in running_containers])
    conf_content = NGINX_CONF_TEMPLATE % servers

    with open("nginx.conf", "w") as f:
        f.write(conf_content)

    try:
        subprocess.run(["docker", "exec", "nginx-proxy", "nginx", "-s", "reload"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Nginx configuration updated and reloaded.")
    except Exception as e:
        print(f"Failed to reload Nginx: {e}")

def scale_out(next_instance_num):
    instance_name = f"app-instance-{next_instance_num}"
    port = 5000 + next_instance_num
    print(f"Scaling out: Starting {instance_name}")
    try:
        subprocess.run([
            "docker", "run", "-d",
            "--name", instance_name,
            "--network", NETWORK_NAME,
            "-p", f"{port}:5000",
            CONTAINER_IMAGE
        ], check=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error starting {instance_name}: {e}")

def scale_in(instance_name):
    print(f"Scaling in: Stopping {instance_name}")
    try:
        subprocess.run(["docker", "rm", "-f", instance_name], check=True, stdout=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error removing {instance_name}: {e}")

def main():
    print("Autoscaler service started. Polling every 15s...")
    while True:
        try:
            containers = get_running_containers()
            count = len(containers)
            avg_cpu, avg_mem = get_cpu_and_mem_stats(containers)

            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            print(f"[{now}] Containers: {count}, Avg CPU: {avg_cpu:.2f}%, Avg Mem: {avg_mem:.2f}%")

            with open(METRICS_FILE, "a") as f:
                f.write(f"{now},{count},{avg_cpu:.2f},{avg_mem:.2f}\n")

            if avg_cpu > SCALE_OUT_THRESHOLD and count < MAX_CONTAINERS:
                scale_out(count + 1)
                new_containers = get_running_containers()
                update_nginx(new_containers)

            elif avg_cpu < SCALE_IN_THRESHOLD and count > MIN_CONTAINERS:
                highest_instance = containers[-1]
                scale_in(highest_instance)
                new_containers = get_running_containers()
                update_nginx(new_containers)

        except Exception as ex:
            print(f"Error in autoscaler loop: {ex}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
