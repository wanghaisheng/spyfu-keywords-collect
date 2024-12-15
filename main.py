import httpx
import asyncio
import json
import csv
import os
from typing import Optional

def load_config():
    """Load configuration from GitHub Actions environment variables or config.json."""
    config = {
        "queries": os.getenv("QUERIES", None),
        "rankingDifficultyStart": os.getenv("RANKING_DIFFICULTY_START", 1),
        "rankingDifficultyEnd": os.getenv("RANKING_DIFFICULTY_END", 100),
        "searchVolumeMin": os.getenv("SEARCH_VOLUME_MIN", 500),
        "searchVolumeMax": os.getenv("SEARCH_VOLUME_MAX", None),
    }
    # Parse queries into a list
    
    if config["queries"]:
        config["queries"] = [q.strip() for q in config["queries"].split(",")]

    # If GitHub Actions variables are not set, load from config.json
    if not config["queries"]:
        try:
            with open("config.json", "r") as f:
                file_config = json.load(f)
                config["queries"] = file_config.get("queries", None)
                config["rankingDifficultyStart"] = file_config.get("rankingDifficultyStart", 1)
                config["rankingDifficultyEnd"] = file_config.get("rankingDifficultyEnd", 100)
                config["searchVolumeMin"] = file_config.get("searchVolumeMin", 500)
                config["searchVolumeMax"] = file_config.get("searchVolumeMax", None)
        except FileNotFoundError:
            print("Config file not found, and no environment variables provided.")


    return config

async def fetch_data(client, query, ranking_difficulty, search_volume_min, search_volume_max):
    """Fetch data from the API."""
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    payload = {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
                {"field": "searchVolume", "min": search_volume_min, "max": search_volume_max or None},
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

    try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Error parsing JSON for query '{query}' with ranking difficulty {ranking_difficulty}: {response.text}")
            return None
        return data
    except httpx.RequestError as e:
        print(f"Network error for query '{query}' with ranking difficulty {ranking_difficulty}: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"HTTP error for query '{query}' with ranking difficulty {ranking_difficulty}: {e}")
        return None

async def process_query(query, config):
    """Process a single query across the ranking difficulty range."""
    results = []
    async with httpx.AsyncClient() as client:
        for ranking_difficulty in range(
            int(config["rankingDifficultyStart"]), int(config["rankingDifficultyEnd"]) + 1
        ):
            data = await fetch_data(
                client,
                query,
                ranking_difficulty,
                int(config["searchVolumeMin"]),
                config["searchVolumeMax"] if config["searchVolumeMax"] else None,
            )
            if data and "keywords" in data:
                results.extend(data["keywords"])
    return results

def save_to_csv(results, filename="keywords_results.csv"):
    """Save results to a CSV file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"keywords_results_{timestamp}.csv"
    
    with open(filename, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["query", "keyword", "searchVolume", "rankingDifficulty", "cpc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def format_results(query, raw_results):
    """Format raw API results for CSV writing."""
    formatted = []
    for keyword_data in raw_results:
        formatted.append({
            "query": query,
            "keyword": keyword_data.get("keyword", ""),
            "searchVolume": keyword_data.get("searchVolume", 0),
            "rankingDifficulty": keyword_data.get("rankingDifficulty", 0),
            "cpc": keyword_data.get("cpc", 0),
        })
    return formatted

async def main():
    config = load_config()
    if not config["queries"]:
        print("No queries provided.")
        return

    all_results = []
    for query in config["queries"]:
        print(f"Processing query: {query}")
        raw_results = await process_query(query, config)
        all_results.extend(format_results(query, raw_results))

    save_to_csv(all_results)
    print("Results saved to keywords_results.csv.")

if __name__ == "__main__":
    asyncio.run(main())
