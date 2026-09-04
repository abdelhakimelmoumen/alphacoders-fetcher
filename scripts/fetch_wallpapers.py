import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Add your categories here
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
        wallpapers = soup.select('picture img, .thumb-container img, .thumb-pic img')

        # Find the next available index for this category based on what's already in the database
        category_entries = [e for e in database if e.get('category') == category]
        counter = len(category_entries) + 1

        for img in wallpapers:
            src = img.get('src') or img.get('data-src')
            
            if not src or not src.startswith('http'):
                continue

            if src.endswith('.svg') or any(keyword in src for keyword in ['avatar', 'logo', 'icon', 'badge']):
                continue

            if src in existing_urls:
                continue

            try:
                # Detect extension from original URL (default to .jpg if missing)
                parsed_path = urlparse(src).path
                ext = os.path.splitext(parsed_path)[1].lower()
                if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
                    ext = '.jpg'

                # Formulate the requested name pattern: e.g., 1_.jpg, 2_.png
                img_name = f"{counter}_{}{ext}".replace("{}", "") # Results in 1_.jpg, etc.
                # Cleaner format: f"{counter}_" + ext[1:] -> e.g. 1_.jpg
                img_name = f"{counter}_{ext[1:]}" # Wait, let's keep it strictly like 1_.jpg or 1_.png
                img_name = f"{counter}_{ext.replace('.', '')}" # or let's use explicit string:
                img_name = f"{counter}_{ext}" # wait, ext has the dot. Let's do:
                ext_clean = ext.lstrip('.')
                img_name = f"{counter}_.{ext_clean}" # yields 1_.png or 1_.jpg

                save_path = os.path.join(category_dir, img_name)

                # Download the image
                if not os.path.exists(save_path):
                    img_data = requests.get(src, headers=HEADERS, timeout=10).content
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                
                # Create structured JSON entry for Flutter
                entry = {
                    "id": f"{category}_{counter}",
                    "category": category,
                    "file_name": img_name,
                    "local_path": save_path.replace("\\", "/"),
                    "original_url": src
                }
                
                database.append(entry)
                existing_urls.add(src)
                counter += 1
                downloaded_total += 1
                
                print(f"Downloaded: {category}/{img_name}")

            except Exception as e:
                print(f"Error processing {src}: {e}")

    save_json(database)
    print(f"Finished. Downloaded {downloaded_total} wallpapers with custom naming.")

if __name__ == "__main__":
    fetch_wallpapers()
