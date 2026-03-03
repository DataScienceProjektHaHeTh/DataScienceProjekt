import requests
import os
from dotenv import load_dotenv
import csv 

load_dotenv()

API_KEY = os.getenv("guardianApiKey")

params = {
    "q": "Trump",
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
    print(f"[OK] {len(articles)} Artikel erhalten")

    os.makedirs("data/raw", exist_ok=True)

    with open("data/raw/articles.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "title", "body"])
        writer.writeheader()
        for article in articles:
            writer.writerow({
                "date": article["webPublicationDate"][:10],
                "title": article["webTitle"],
                "body": article.get("fields", {}).get("bodyText", "")
            })

    print("Gespeichert: data/raw/articles.csv")