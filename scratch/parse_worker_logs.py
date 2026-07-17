import json
import datetime

def main():
    path = "/Users/ritika/Garden/scratch/worker_logs.json"
    with open(path, "r") as f:
        entries = json.load(f)
        
    print(f"Loaded {len(entries)} log entries.")
    
    if entries:
        print(f"First timestamp: {entries[0].get('timestamp')}")
        print(f"Last timestamp: {entries[-1].get('timestamp')}")
        
    print("\n--- Non-cap, Non-ping log entries ---")
    other_count = 0
    for entry in entries:
        payload = entry.get("textPayload", "")
        if "spending cap" in payload or "RESOURCE_EXHAUSTED" in payload or "ping" in payload or "Uvicorn" in payload or "startup" in payload or "Starting Garden Temporal Worker" in payload:
            continue
        print(f"[{entry.get('timestamp')}] {payload.strip()}")
        other_count += 1
        if other_count >= 50:
            print("Truncated non-cap/ping output...")
            break
            
    # Count cap exceeded errors
    cap_errors = sum(1 for e in entries if "monthly spending cap" in e.get("textPayload", ""))
    print(f"\nTotal 'monthly spending cap' errors in logs: {cap_errors}")

if __name__ == "__main__":
    main()
