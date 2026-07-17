import subprocess
import json
import datetime

def main():
    project = "crawler-488903"
    # We want logs since 16 hours ago
    t_str = (datetime.datetime.utcnow() - datetime.timedelta(hours=16)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Use gcloud logging read to get textPayload from the stdout/stderr logs of caremyplants
    log_filter = (
        f'resource.type="cloud_run_revision" '
        f'AND resource.labels.service_name="caremyplants" '
        f'AND logName:"logs/run.googleapis.com%2Fstd" '
        f'AND timestamp >= "{t_str}"'
    )
    
    cmd = [
        "gcloud", "logging", "read", log_filter,
        f"--project={project}",
        "--format=json",
        "--limit=2000"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error: {res.stderr}")
        return
        
    try:
        entries = json.loads(res.stdout)
    except Exception as e:
        print(f"Failed to parse JSON: {e}")
        return
        
    print(f"Retrieved {len(entries)} log entries.")
    
    # Sort by timestamp ascending
    entries.sort(key=lambda x: x.get("timestamp", ""))
    
    # Write to local file
    out_path = "/Users/ritika/Garden/scratch/worker_logs.json"
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Successfully wrote {len(entries)} entries to {out_path}")

if __name__ == "__main__":
    main()
