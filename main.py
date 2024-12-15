import httpx
import csv
import time
import concurrent.futures
import json
import os
import sys

# Define the API URL
url = "https://www.spyfu.com/NsaApi/RelatedKeyword/GetPhraseMatchedKeywords"

# Load configuration: check environment variables first, then fallback to config.json
def load_config():
    config = {}

    # Check environment variables (for GitHub Actions or other CI/CD tools)
    config['rankingDifficultyStart'] = int(os.getenv('RANKING_DIFFICULTY_START', 1))
    config['rankingDifficultyEnd'] = int(os.getenv('RANKING_DIFFICULTY_END', 100))
    config['searchVolumeMin'] = int(os.getenv('SEARCH_VOLUME_MIN', 500))
    config['searchVolumeMax'] = os.getenv('SEARCH_VOLUME_MAX', None)
    config['query'] = os.getenv('QUERY', None)

    # If any required variables are missing, fall back to `config.json`
    if not config['query']:
        try:
            with open('config.json', 'r') as file:
                json_config = json.load(file)
                config.update(json_config)
        except FileNotFoundError:
            print("Neither environment variables nor config.json are available. Exiting.")
            sys.exit(1)

    return config

# Define the request payload template
def get_payload(query, rankingDifficulty, searchVolumeMin):
    return {
        "facets": {
            "ranges": [
                {"field": "rankingDifficulty", "min": rankingDifficulty, "max": rankingDifficulty},
                {"field": "searchVolume", "min": searchVolumeMin, "max": None}
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

# Function to fetch keywords from API
def fetch_keywords(page, query, rankingDifficulty, searchVolumeMin):
    payload = get_payload(query, rankingDifficulty, searchVolumeMin)
    payload['startingRow'] = (page - 1) * payload['pageSize'] + 1

    # Make the HTTP request
    with httpx.Client() as client:
        response = client.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            keywords = data.get('keywords', [])
            return keywords
        else:
            print(f"Error on request {page} for rankingDifficulty {rankingDifficulty}: {response.status_code}")
            return []

# Read keywords (from GitHub Action input or urls.txt)
def get_keywords_from_input():
    # Check if GitHub Action input (via sys.argv or environment variables) or file is available
    if len(sys.argv) > 1:
        # Keywords passed as comma-separated values in GitHub Action input
        keywords_input = sys.argv[1]
        return keywords_input.split(",")
    
    # If no GitHub Action input, check for 'urls.txt' file
    try:
        with open("urls.txt", "r") as file:
            keywords = file.read().strip().splitlines()
        return keywords
    except FileNotFoundError:
        print("No GitHub input or 'urls.txt' file found, exiting.")
        sys.exit(1)

# Read the config settings
config = load_config()

# Read keywords (from GitHub Action input or urls.txt)
keywords_list = get_keywords_from_input()

# Set the maximum number of requests to fetch
max_requests = 100
results = []

# Use ThreadPoolExecutor to send requests in batches of 10
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # Loop through the rankingDifficulty values
    for rankingDifficulty in range(config['rankingDifficultyStart'], config['rankingDifficultyEnd'] + 1):
        # Submit the tasks to the executor for each keyword
        future_to_page = {executor.submit(fetch_keywords, page, keyword, rankingDifficulty, config['searchVolumeMin']): page for page in range(1, max_requests + 1) for keyword in keywords_list}

        # Process the results as they complete
        for future in concurrent.futures.as_completed(future_to_page):
            keywords = future.result()
            if keywords:
                results.extend(keywords)
        
        # To avoid hitting the server too quickly, introduce a delay (optional)
        time.sleep(0.1)  # Adjust sleep time to control request rate

# Save the results to a CSV file
csv_filename = "keywords_results.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=["keyword"])
    writer.writeheader()
    for result in results:
        writer.writerow({"keyword": result})  # Save each keyword

print(f"Saved {len(results)} results to {csv_filename}.")
