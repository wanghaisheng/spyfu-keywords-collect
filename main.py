import requests
import json
import csv
import os
from datetime import datetime

def load_config():
    """Load configuration from GitHub Actions environment variables or config.json."""
    config = {
        "queries": os.getenv("QUERIES", None),
        "rankingDifficultyStart": int(os.getenv("RANKING_DIFFICULTY_START", 1)),
        "rankingDifficultyEnd": int(os.getenv("RANKING_DIFFICULTY_END", 100)),
        "searchVolumeMin": int(os.getenv("SEARCH_VOLUME_MIN", 500)),
        "searchVolumeMax": int(os.getenv("SEARCH_VOLUME_MAX",100)),
        "filename": os.getenv("FILENAME", "keywords_results.csv")
    }

    # Parse queries into a list
    if config["queries"]:
        config["queries"] = [q.strip() for q in config["queries"].split(",")]

    # Fallback to config.json if needed
    if not config["queries"]:
        try:
            with open("config.json", "r") as f:
                file_config = json.load(f)
                config["queries"] = file_config.get("queries", [])
                config["rankingDifficultyStart"] = file_config.get("rankingDifficultyStart", 1)
                config["rankingDifficultyEnd"] = file_config.get("rankingDifficultyEnd", 100)
                config["searchVolumeMin"] = file_config.get("searchVolumeMin", 500)
                config["searchVolumeMax"] = file_config.get("searchVolumeMax")
                config["filename"] = file_config.get("filename", "keywords_results.csv")
        except FileNotFoundError:
            print("Config file not found and no environment variables provided.")

    return config

def fetch_data_sync(query, ranking_difficulty, search_volume_min, search_volume_max):
    """SpyFu同步调用：获取关键词相关信息"""
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    
    payload = {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
                {"field": "searchVolume", "min": search_volume_min, "max": search_volume_max or None}
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

    headers = {
        'content-type': 'application/json;charset=UTF-8',
        # Optional cookie if SpyFu requires it (used in FastAPI example)
        # 'Cookie': 'ASP.NET_SessionId=rutmlg02sfx4yakg0nd0asxw'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if "keywords" in data else None
    except requests.RequestException as e:
        print(f"[Error] Failed to fetch for '{query}' @ Difficulty {ranking_difficulty}: {e}")
        return None

def process_query_sync(query, config):
    results = []
    for ranking_difficulty in range(config["rankingDifficultyStart"], config["rankingDifficultyEnd"] + 1):
        print(f"Processing: {query} | Difficulty: {ranking_difficulty}")
        data = fetch_data_sync(
            query,
            ranking_difficulty,
            config["searchVolumeMin"],
            config["searchVolumeMax"]
        )
        if data and "keywords" in data:
            results.extend(data["keywords"])
    return results

def format_results(query, raw_results):
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

def save_to_csv(results, filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"keywords_results_{timestamp}.csv" if filename == "keywords_results.csv" else filename
    os.makedirs("results", exist_ok=True)
    final_path = os.path.join("results", final_filename)

    with open(final_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["query", "keyword", "searchVolume", "rankingDifficulty", "cpc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"✅ Results saved to: {final_path}")

def main_sync():
    config = load_config()
    if not config["queries"]:
        print("❌ No queries provided in environment or config.json.")
        return

    all_results = []
    for query in config["queries"]:
        raw_results = process_query_sync(query, config)
        all_results.extend(format_results(query, raw_results))

    save_to_csv(all_results, config["filename"])

if __name__ == "__main__":
    main_sync()
import requests
import json
import csv
import os
from datetime import datetime

def load_config():
    """Load configuration from GitHub Actions environment variables or config.json."""
    config = {
        "queries": os.getenv("QUERIES", None),
        "rankingDifficultyStart": int(os.getenv("RANKING_DIFFICULTY_START", 1)),
        "rankingDifficultyEnd": int(os.getenv("RANKING_DIFFICULTY_END", 100)),
        "searchVolumeMin": int(os.getenv("SEARCH_VOLUME_MIN", 500)),
        "searchVolumeMax": int(os.getenv("SEARCH_VOLUME_MAX")) if os.getenv("SEARCH_VOLUME_MAX") else None,
        "filename": os.getenv("FILENAME", "keywords_results.csv")
    }

    # Parse queries into a list
    if config["queries"]:
        config["queries"] = [q.strip() for q in config["queries"].split(",")]

    # Fallback to config.json if needed
    if not config["queries"]:
        try:
            with open("config.json", "r") as f:
                file_config = json.load(f)
                config["queries"] = file_config.get("queries", [])
                config["rankingDifficultyStart"] = file_config.get("rankingDifficultyStart", 1)
                config["rankingDifficultyEnd"] = file_config.get("rankingDifficultyEnd", 100)
                config["searchVolumeMin"] = file_config.get("searchVolumeMin", 500)
                config["searchVolumeMax"] = file_config.get("searchVolumeMax")
                config["filename"] = file_config.get("filename", "keywords_results.csv")
        except FileNotFoundError:
            print("Config file not found and no environment variables provided.")

    return config

def fetch_data_sync(query, ranking_difficulty, search_volume_min, search_volume_max):
    """SpyFu同步调用：获取关键词相关信息"""
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    
    payload = {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
                {"field": "searchVolume", "min": search_volume_min, "max": search_volume_max or None}
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

    headers = {
        'content-type': 'application/json;charset=UTF-8',
        # Optional cookie if SpyFu requires it (used in FastAPI example)
        # 'Cookie': 'ASP.NET_SessionId=rutmlg02sfx4yakg0nd0asxw'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if "keywords" in data else None
    except requests.RequestException as e:
        print(f"[Error] Failed to fetch for '{query}' @ Difficulty {ranking_difficulty}: {e}")
        return None

def process_query_sync(query, config):
    results = []
    for ranking_difficulty in range(config["rankingDifficultyStart"], config["rankingDifficultyEnd"] + 1):
        print(f"Processing: {query} | Difficulty: {ranking_difficulty}")
        data = fetch_data_sync(
            query,
            ranking_difficulty,
            config["searchVolumeMin"],
            config["searchVolumeMax"]
        )
        if data and "keywords" in data:
            results.extend(data["keywords"])
    return results

def format_results(query, raw_results):
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

def save_to_csv(results, filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"keywords_results_{timestamp}.csv" if filename == "keywords_results.csv" else filename
    os.makedirs("results", exist_ok=True)
    final_path = os.path.join("results", final_filename)

    with open(final_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["query", "keyword", "searchVolume", "rankingDifficulty", "cpc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"✅ Results saved to: {final_path}")

def main_sync():
    config = load_config()
    if not config["queries"]:
        print("❌ No queries provided in environment or config.json.")
        return

    all_results = []
    for query in config["queries"]:
        raw_results = process_query_sync(query, config)
        all_results.extend(format_results(query, raw_results))

    save_to_csv(all_results, config["filename"])

if __name__ == "__main__":
    main_sync()
import requests
import json
import csv
import os
from datetime import datetime

def load_config():
    """Load configuration from GitHub Actions environment variables or config.json."""
    config = {
        "queries": os.getenv("QUERIES", None),
        "rankingDifficultyStart": int(os.getenv("RANKING_DIFFICULTY_START", 1)),
        "rankingDifficultyEnd": int(os.getenv("RANKING_DIFFICULTY_END", 100)),
        "searchVolumeMin": int(os.getenv("SEARCH_VOLUME_MIN", 500)),
        "searchVolumeMax": int(os.getenv("SEARCH_VOLUME_MAX")) if os.getenv("SEARCH_VOLUME_MAX") else None,
        "filename": os.getenv("FILENAME", "keywords_results.csv")
    }

    # Parse queries into a list
    if config["queries"]:
        config["queries"] = [q.strip() for q in config["queries"].split(",")]

    # Fallback to config.json if needed
    if not config["queries"]:
        try:
            with open("config.json", "r") as f:
                file_config = json.load(f)
                config["queries"] = file_config.get("queries", [])
                config["rankingDifficultyStart"] = file_config.get("rankingDifficultyStart", 1)
                config["rankingDifficultyEnd"] = file_config.get("rankingDifficultyEnd", 100)
                config["searchVolumeMin"] = file_config.get("searchVolumeMin", 500)
                config["searchVolumeMax"] = file_config.get("searchVolumeMax")
                config["filename"] = file_config.get("filename", "keywords_results.csv")
        except FileNotFoundError:
            print("Config file not found and no environment variables provided.")

    return config

def fetch_data_sync(query, ranking_difficulty, search_volume_min, search_volume_max):
    """SpyFu同步调用：获取关键词相关信息"""
    url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"
    
    payload = {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": ranking_difficulty, "max": ranking_difficulty},
                {"field": "searchVolume", "min": search_volume_min, "max": search_volume_max or None}
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

    headers = {
        'content-type': 'application/json;charset=UTF-8',
        # Optional cookie if SpyFu requires it (used in FastAPI example)
        # 'Cookie': 'ASP.NET_SessionId=rutmlg02sfx4yakg0nd0asxw'
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if "keywords" in data else None
    except requests.RequestException as e:
        print(f"[Error] Failed to fetch for '{query}' @ Difficulty {ranking_difficulty}: {e}")
        return None

def process_query_sync(query, config):
    results = []
    for ranking_difficulty in range(config["rankingDifficultyStart"], config["rankingDifficultyEnd"] + 1):
        print(f"Processing: {query} | Difficulty: {ranking_difficulty}")
        data = fetch_data_sync(
            query,
            ranking_difficulty,
            config["searchVolumeMin"],
            config["searchVolumeMax"]
        )
        if data and "keywords" in data:
            results.extend(data["keywords"])
    return results

def format_results(query, raw_results):
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

def save_to_csv(results, filename):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_filename = f"keywords_results_{timestamp}.csv" if filename == "keywords_results.csv" else filename
    os.makedirs("results", exist_ok=True)
    final_path = os.path.join("results", final_filename)

    with open(final_path, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["query", "keyword", "searchVolume", "rankingDifficulty", "cpc"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)

    print(f"✅ Results saved to: {final_path}")

def main_sync():
    config = load_config()
    if not config["queries"]:
        print("❌ No queries provided in environment or config.json.")
        return

    all_results = []
    for query in config["queries"]:
        raw_results = process_query_sync(query, config)
        all_results.extend(format_results(query, raw_results))

    save_to_csv(all_results, config["filename"])

if __name__ == "__main__":
    main_sync()
