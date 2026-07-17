import json

def main():
    path = "/Users/ritika/Garden/scratch/worker_logs_3am.json"
    with open(path, "r") as f:
        entries = json.load(f)
        
    print(f"Total entries: {len(entries)}")
    
    overview_starts = []
    identify_starts = []
    detail_starts = []
    imagen_failures = []
    imagen_successes = []
    other_errors = []
    
    for entry in entries:
        payload = entry.get("textPayload", "")
        ts = entry.get("timestamp", "")
        
        if "Running garden overview AI for garden" in payload:
            overview_starts.append((ts, payload))
        elif "Identifying plants for garden" in payload:
            identify_starts.append((ts, payload))
        elif "Running detailed Gemini analysis for" in payload:
            detail_starts.append((ts, payload))
        elif "Failed to generate visualization" in payload:
            imagen_failures.append((ts, payload))
        elif "Successfully generated and saved visualization" in payload:
            imagen_successes.append((ts, payload))
        elif "Exception during Gemini call" in payload or "Gemini call failed" in payload:
            # Check what error
            other_errors.append((ts, payload))
            
    print(f"\nGarden Overview Starts ({len(overview_starts)}):")
    for ts, p in overview_starts:
        print(f"  [{ts}] {p.strip()}")
        
    print(f"\nPlant Identification Starts ({len(identify_starts)}):")
    for ts, p in identify_starts:
        print(f"  [{ts}] {p.strip()}")
        
    print(f"\nPlant Detail Analysis Starts ({len(detail_starts)}):")
    for ts, p in detail_starts:
        print(f"  [{ts}] {p.strip()}")
        
    print(f"\nImagen Failures ({len(imagen_failures)}):")
    for ts, p in imagen_failures:
        print(f"  [{ts}] {p.strip()}")
        
    print(f"\nImagen Successes ({len(imagen_successes)}):")
    for ts, p in imagen_successes:
        print(f"  [{ts}] {p.strip()}")
        
    # Categorize other errors
    print(f"\nTotal Gemini API Errors/Exceptions: {len(other_errors)}")
    unique_errors = set()
    for ts, p in other_errors:
        # Extract error message (usually after exception or fail)
        unique_errors.add(p.strip())
    print(f"Unique Gemini errors: {len(unique_errors)}")
    # Print a few unique errors
    for e in list(unique_errors)[:10]:
        print(f"  - {e}")

if __name__ == "__main__":
    main()
