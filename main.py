from scrape import run
from analysis import analyze_reviews
import asyncio
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python script.py <company_name>")
        sys.exit(1)
    filename = asyncio.run(run(sys.argv[1]))
    
    print(f"Saved reviews to {filename}")
    analyze_reviews(filename, sys.argv[1])