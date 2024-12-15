import os
import json
import httpx
import csv
from concurrent.futures import ThreadPoolExecutor

# Configuration defaults
DEFAULT_CONFIG = {
    "queries": [],  # A list of keywords
    "rankingDifficultyStart": 1,
    "rankingDifficultyEnd": 100,
    "searchVolumeMin": 500,
    "searchVolumeMax": None
}

CONFIG_FILE = "config.json"
RESULT_FILE = "keywords_results.csv"

# Function to load configuration
def load_config():
    # Read from GitHub Actions inputs
    queries = os.getenv("QUERIES")
    ranking_difficulty_start = os.getenv("RANKING_DIFFICULTY_START")
    ranking_difficulty_end = os.getenv("RANKING_DIFFICULTY_END")
    search_volume_min = os.getenv("SEARCH_VOLUME_MIN")
    search_volume_max = os.getenv("SEARCH_VOLUME_MAX")

    # Fallback to config.json
    config = DEFAULT_CONFIG
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config.update(json.load(f))

    queries = queries.split(",") if queries else config.get("queries", [])
    ranking_difficulty_start = int(ranking_difficulty_start or config.get("rankingDifficultyStart", DEFAULT_CONFIG["rankingDifficultyStart"]))
    ranking_difficulty_end = int(ranking_difficulty_end or config.get("rankingDifficultyEnd", DEFAULT_CONFIG["rankingDifficultyEnd"]))
    search_volume_min = int(search_volume_min or config.get("searchVolumeMin", DEFAULT_CONFIG["searchVolumeMin"]))
    search_volume_max = int(search_volume_max) if search_volume_max else config.get("searchVolumeMax")

    if not queries:
        raise ValueError("At least one query must be provided either via GitHub Actions or config.json.")

    return {
        "queries": queries,
        "rankingDifficultyStart": ranking_difficulty_start,
        "rankingDifficultyEnd": ranking_difficulty_end,
        "searchVolumeMin": search_volume_min,
        "searchVolumeMax": search_volume_max
    }

# Function to make API request
def fetch_data(ranking_difficulty, query, search_volume_min, search_volume_max):
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    ranges = [
        {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
        {"field": "searchVolume", "min": search_volume_min}
    ]
    if search_volume_max is not None:
        ranges.append({"field": "searchVolume", "max": search_volume_max})

    payload = {
        "facets": {
            "ranges": ranges,
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
    queries = config["queries"]
    ranking_difficulty_start = config["rankingDifficultyStart"]
    ranking_difficulty_end = config["rankingDifficultyEnd"]
    search_volume_min = config["searchVolumeMin"]
    search_volume_max = config["searchVolumeMax"]

    all_results = []

    def process_batch(ranking_difficulty, query):
        try:
            data = fetch_data(ranking_difficulty, query, search_volume_min, search_volume_max)
            keywords = data.get("keywords", [])
            for keyword in keywords:
                keyword["query"] = query  # Add query for tracking
            all_results.extend(keywords)
        except Exception as e:
            print(f"Error fetching data for query '{query}' with ranking difficulty {ranking_difficulty}: {e}")

    with ThreadPoolExecutor(max_workers=10) as executor:
        for query in queries:
            executor.map(lambda rd: process_batch(rd, query), range(ranking_difficulty_start, ranking_difficulty_end + 1))

    # Save results to CSV
    with open(RESULT_FILE, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["query", "keyword", "searchVolume", "rankingDifficulty"])
        writer.writeheader()
        for result in all_results:
            writer.writerow({
                "query": result.get("query"),
                "keyword": result.get("keyword"),
                "searchVolume": result.get("searchVolume"),
                "rankingDifficulty": result.get("rankingDifficulty")
            })

    print(f"Results saved to {RESULT_FILE}")

if __name__ == "__main__":
    main()
