import requests
import os
from dotenv import load_dotenv
import csv 

load_dotenv()

API_KEY = os.getenv("guardianApiKey")

params = {
    "q": "Trump",
    "from-date": "2025-01-20",
    "page-size": 200,
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

    total = response.json()["response"]["total"]
    print(f"[OK] {len(articles)} von {total} Artikeln erhalten")
    
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



# --- Search queries by categorie---
#   
#   Trade policy 
#   "q": "Trump AND (tariff OR tariffs OR \"trade war\" OR \"trade deal\" 
#      OR import OR export OR customs OR \"trade deficit\" OR WTO 
#      OR USMCA OR \"reciprocal tariff\" OR steel OR aluminum 
#      OR Mexico OR Canada)"
#
#   Geopolitcs
#   "q": "(Trump OR \"White House\" OR administration) AND (NATO OR Ukraine 
#      OR Russia OR China OR military OR sanctions OR \"foreign policy\" 
#      OR troops OR Pentagon OR \"Middle East\" OR Taiwan OR Korea 
#      OR Greenland OR Panama)"
#
#   Domestic politics
#   "q": "(Trump OR \"White House\" OR administration) AND (\"executive order\" 
#      OR congress OR senate OR immigration OR deportation OR DOGE OR Musk 
#      OR FBI OR DOJ OR \"supreme court\" OR budget OR \"national debt\" 
#      OR federal)"