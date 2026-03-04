import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("guardianApiKey")

params = {
    "q": "Trump AND tariff",
    "from-date": "2025-01-01",
    "page-size": 5,
    "order-by": "oldest",
    "show-fields": "bodyText",
    "api-key": API_KEY,
}

response = requests.get("https://content.guardianapis.com/search", params=params)

if response.status_code != 200:
    print(f"[FEHLER] HTTP {response.status_code}")
    print(response.text)
else:
    articles = response.json()["response"]["results"]
    print(f"[OK] {len(articles)} Artikel erhalten:\n")
    for i, article in enumerate(articles, 1):
        print(f"--- Artikel {i} ---")
        print(f"Datum : {article['webPublicationDate'][:10]}")
        print(f"Titel : {article['webTitle']}")
        body = article.get("fields", {}).get("bodyText", "")
        print(f"Text  : {body[:300]}...")
        print()