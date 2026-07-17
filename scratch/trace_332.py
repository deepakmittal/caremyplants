import json

def main():
    path = "/Users/ritika/Garden/scratch/worker_logs_3am.json"
    with open(path, "r") as f:
        entries = json.load(f)
        
    entries.sort(key=lambda x: x.get("timestamp", ""))
    
    start_trace = False
    for entry in entries:
        ts = entry.get("timestamp", "")
        payload = entry.get("textPayload", "")
        
        if "03:32:00" in ts:
            start_trace = True
            
        if start_trace:
            # We want to print everything including exceptions and errors
            # Let's skip the repeating transient retries but show the final exception/error
            if "transient error" in payload:
                continue
            print(f"[{ts}] {payload.strip()}")

if __name__ == "__main__":
    main()
