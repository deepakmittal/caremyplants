import json
import re

def main():
    path = "/Users/ritika/Garden/scratch/worker_logs_3am.json"
    with open(path, "r") as f:
        entries = json.load(f)
        
    print(f"Loaded {len(entries)} log entries from 3 AM - 4 AM UTC.")
    
    # Sort chronologically
    entries.sort(key=lambda x: x.get("timestamp", ""))
    
    for entry in entries:
        payload = entry.get("textPayload", "")
        ts = entry.get("timestamp", "")
        
        # Check for start of workflows or activities
        if "Activity" in payload or "Running garden overview AI" in payload or "Identifying plants" in payload or "Gemini" in payload or "Imagen" in payload or "visualization" in payload.lower():
            # Skip RESOURCE_EXHAUSTED messages to keep the output readable
            if "RESOURCE_EXHAUSTED" in payload or "spending cap" in payload:
                continue
            print(f"[{ts}] {payload.strip()}")

if __name__ == "__main__":
    main()
