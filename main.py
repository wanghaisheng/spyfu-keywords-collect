import os
import json
import httpx
import csv
from concurrent.futures import ThreadPoolExecutor

# Configuration defaults
DEFAULT_CONFIG = {
    "query": "default query",
    "rankingDifficultyStart": 1,
    "rankingDifficultyEnd": 100,
    "searchVolumeMin": 500
}

CONFIG_FILE = "config.json"
RESULT_FILE = "keywords_results.csv"

# Function to load configuration
def load_config():
    # Read from GitHub Actions inputs
    query = os.getenv("QUERY")
    ranking_difficulty_start = os.getenv("RANKING_DIFFICULTY_START")
    ranking_difficulty_end = os.getenv("RANKING_DIFFICULTY_END")
    search_volume_min = os.getenv("SEARCH_VOLUME_MIN")

    # Check for config.json as fallback
    if not query or not ranking_difficulty_start or not ranking_difficulty_end or not search_volume_min:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            query = query or config.get("query", DEFAULT_CONFIG["query"])
            ranking_difficulty_start = int(ranking_difficulty_start or config.get("rankingDifficultyStart", DEFAULT_CONFIG["rankingDifficultyStart"]))
            ranking_difficulty_end = int(ranking_difficulty_end or config.get("rankingDifficultyEnd", DEFAULT_CONFIG["rankingDifficultyEnd"]))
            search_volume_min = int(search_volume_min or config.get("searchVolumeMin", DEFAULT_CONFIG["searchVolumeMin"]))

    return {
        "query": query,
        "rankingDifficultyStart": int(ranking_difficulty_start),
        "rankingDifficultyEnd": int(ranking_difficulty_end),
        "searchVolumeMin": int(search_volume_min)
    }

# Function to make API request
def fetch_data(ranking_difficulty, query, search_volume_min):
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    payload = {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
                {"field": "searchVolume", "min": search_volume_min}
            ],
            "terms": []
        },
        "pageSize": 50,
        "query": query,
        "sortOrder": "descending",
        "startingRow": 1,
        "groups": [],
        "adultFilter": True,
        "isOverview": False,
        "countryCode": "US"
    }

    response = httpx.post(url, json=payload)
    response.raise_for_status()
    return response.json()

# Main function to run queries
def main():
    config = load_config()
    query = config["query"]
    ranking_difficulty_start = config["rankingDifficultyStart"]
    ranking_difficulty_end = config["rankingDifficultyEnd"]
    search_volume_min = config["searchVolumeMin"]

    all_results = []

    def process_batch(ranking_difficulty):
        try:
            data = fetch_data(ranking_difficulty, query, search_volume_min)
            keywords = data.get("keywords", [])
            all_results.extend(keywords)
        except Exception as e:
            print(f"Error fetching data for ranking difficulty {ranking_difficulty}: {e}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(process_batch, range(ranking_difficulty_start, ranking_difficulty_end + 1))

    # Save results to CSV
    with open(RESULT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["keyword", "searchVolume", "rankingDifficulty"])
        writer.writeheader()
        for result in all_results:
            writer.writerow({
                "keyword": result.get("keyword"),
                "searchVolume": result.get("searchVolume"),
                "rankingDifficulty": result.get("rankingDifficulty")
            })

    print(f"Results saved to {RESULT_FILE}")

if __name__ == "__main__":
    main()
