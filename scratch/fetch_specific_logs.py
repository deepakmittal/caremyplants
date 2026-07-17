import subprocess
import json

def main():
    project = "crawler-488903"
    # Filter logs specifically during the period of the workflows: 03:00 to 04:00 UTC
    log_filter = (
        'resource.type="cloud_run_revision" '
        'AND resource.labels.service_name="caremyplants" '
        'AND logName:"logs/run.googleapis.com%2Fstd" '
        'AND timestamp >= "2026-07-11T03:00:00Z" '
        'AND timestamp <= "2026-07-11T04:00:00Z"'
    )
    
    cmd = [
        "gcloud", "logging", "read", log_filter,
        f"--project={project}",
        "--format=json",
        "--limit=5000"
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
    
    # Write to local file
    out_path = "/Users/ritika/Garden/scratch/worker_logs_3am.json"
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"Successfully wrote to {out_path}")

if __name__ == "__main__":
    main()
