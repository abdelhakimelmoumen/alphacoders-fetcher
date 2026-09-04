import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Add new categories and URLs here
CATEGORIES = {
    "kawaii": "https://alphacoders.com/kawaii-wallpapers"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_DIR = "wallpapers"
JSON_FILE = "wallpapers.json"

def load_json():
    """Loads existing database to prevent duplicate entries."""
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_json(data):
    """Saves the updated database."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def fetch_wallpapers():
    database = load_json()
    # Track existing URLs to avoid downloading the same image twice
    existing_urls = {entry.get('original_url') for entry in database if 'original_url' in entry}
    
    downloaded_total = 0

    for category, url in CATEGORIES.items():
        category_dir = os.path.join(BASE_DIR, category)
        os.makedirs(category_dir, exist_ok=True)
        print(f"Fetching category '{category}': {url}")

        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        images = soup.find_all('img')

        for img in images:
            src = img.get('src')
            if not src or not src.startswith('http'):
                continue

            # Ignore UI elements
            if 'avatar' in src or 'logo' in src:
                continue

            if src in existing_urls:
                continue

            try:
                img_name = os.path.basename(urlparse(src).path)
                if not img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    img_name += '.jpg'

                save_path = os.path.join(category_dir, img_name)

                # Download the image
                if not os.path.exists(save_path):
                    img_data = requests.get(src, headers=HEADERS, timeout=10).content
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                
                # Create the structured JSON entry
                entry = {
                    "id": img_name.split('.')[0],
                    "category": category,
                    "file_name": img_name,
                    "local_path": save_path.replace("\\", "/"), # Forward slashes for Dart/Flutter compatibility
                    "original_url": src
                }
                
                database.append(entry)
                existing_urls.add(src)
                downloaded_total += 1
                
                print(f"Downloaded: {category}/{img_name}")

            except Exception as e:
                print(f"Error processing {src}: {e}")

    save_json(database)
    print(f"Finished. Downloaded {downloaded_total} new wallpapers and updated JSON database.")

if __name__ == "__main__":
    fetch_wallpapers()