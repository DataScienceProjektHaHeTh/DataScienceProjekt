import requests
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("guardianApiKey")

params = {
    "q": "Trump",
    "from-date": "2025-01-01",
    "page-size": 200,
    "order-by": "oldest",
    "show-fields": "bodyText",
    "api-key": API_KEY,
}

all_articles = []
current_page = 1

while True:
    #update the current page in the parameters
    params["page"] = current_page

    #get the response from the API
    response = requests.get("https://content.guardianapis.com/search", params=params)

    #If the response is not successful, print the error and break the loop
    if response.status_code != 200:
        print(f"[FEHLER] HTTP {response.status_code} on page {current_page}")
        print(response.text)
        break

    #if the response is successful, process the articles and check if there are more pages
    else:
        #save the repsonse data
        data = response.json()["response"]

        #extract the articles from the response
        articles = data["results"]

        #add the new articles to the list of all articles
        all_articles.extend(articles)

        total_pages = data["pages"]
        
        #stop the loop if we have reached the last page
        if current_page >= total_pages:
            break

        print(f"[INFO] Collected {len(articles)} articles from page {current_page} of {total_pages}")

        current_page += 1
        #sleep for a short time to avoid hitting the API rate limit
        time.sleep(0.2)

#save the collected articles to a JSON file
with open("data/raw/guardian_articles.json", "w") as f:
    json.dump(all_articles, f, indent=4)

print(f"\n[INFO] Total articles collected: {len(all_articles)}")