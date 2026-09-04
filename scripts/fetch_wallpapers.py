import os
import json
import requests
from bs4::BeautifulSoup import BeautifulSoup # wait, standard import is just from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Define your categories and their source URLs here
CATEGORIES = {
    "kawaii": "https://alphacoders.com/kawaii-wallpapers",
    # Add more categories here as needed, e.g.:
    # "pastel": "https://alphacoders.com/pastel-wallpapers",
}

# Your GitHub raw base URL template
GITHUB_USER = "abdelhakimelmoumen"
REPO_NAME = "CuteWall-API" # Adjust if your repo name differs
BRANCH = "main"
BASE_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/refs/heads/{BRANCH}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_DIR = "wallpapers"
JSON_FILE = "wallpapers.json"

# Default tags map for categories
CATEGORY_TAGS = {
    "kawaii": ["anime", "cartoon", "chibi", "cute", "kawaii"],
    "pastel": ["aesthetic", "minimal", "pastel", "pink", "soft"],
    "animals": ["animals", "cute", "furry", "kawaii", "pets"],
    "nature": ["calm", "landscape", "nature", "outdoors", "scenery"],
    "galaxy": ["galaxy", "planets", "space", "stars"],
    "ocean": ["blue", "calm", "ocean", "sea", "water"]
}

def fetch_wallpapers():
    # Structure to hold the final JSON data
    master_data = {
        "heroImages": [],
        "categories": []
    }

    all_downloaded_wallpapers = []

    for category_id, base_url in CATEGORIES.items():
        category_dir = os.path.join(BASE_DIR, category_id)
        os.makedirs(category_dir, exist_ok=True)
        
        category_wallpapers = []
        counter = 1
        page = 1

        while True:
            page_url = f"{base_url}?page={page}"
            print(f"Fetching category '{category_id}' - Page {page}: {page_url}")

            try:
                response = requests.get(page_url, headers=HEADERS, timeout=15)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch {page_url}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            wallpapers = soup.select('picture img, .thumb-container img, .thumb-pic img')

            if not wallpapers:
                print(f"Reached the end of pagination for '{category_id}'.")
                break

            found_new_on_page = False

            for img in wallpapers:
                src = img.get('src') or img.get('data-src')
                
                if not src or not src.startswith('http'):
                    continue

                if src.endswith('.svg') or any(keyword in src for keyword in ['avatar', 'logo', 'icon', 'badge']):
                    continue

                try:
                    parsed_path = urlparse(src).path
                    ext = os.path.splitext(parsed_path)[1].lower()
                    if ext not in ['.png', '.jpg', '.jpeg', '.webp']:
                        ext = '.jpg'

                    img_name = f"{counter}_{ext}"
                    save_path = os.path.join(category_dir, img_name)

                    # Download image if it doesn't exist locally
                    if not os.path.exists(save_path):
                        img_data = requests.get(src, headers=HEADERS, timeout=10).content
                        with open(save_path, 'wb') as f:
                            f.write(img_data)
                        print(f"Downloaded: {category_id}/{img_name}")

                    # Construct GitHub Raw URL matching your exact structure
                    image_url = f"{BASE_RAW_URL}/{BASE_DIR}/{category_id}/{img_name}"
                    wallpaper_id = f"{category_id}_{counter}"
                    tags = CATEGORY_TAGS.get(category_id, ["cute", "wallpaper"])

                    wallpaper_entry = {
                        "id": wallpaper_id,
                        "imageUrl": image_url,
                        "tags": tags
                    }

                    category_wallpapers.append(wallpaper_entry)
                    all_downloaded_wallpapers.append(image_url)
                    
                    counter += 1
                    found_new_on_page = True

                except Exception as e:
                    print(f"Error processing image in {category_id}: {e}")

            if not found_new_on_page and page > 1:
                break

            page += 1

        # Append category block
        category_block = {
            "id": category_id,
            "name": category_id.capitalize(),
            "wallpapers": category_wallpapers
        }
        master_data["categories"].append(category_block)

    # Populate hero images using the first 3 downloaded wallpapers (or fewer if less exist)
    hero_limit = min(3, len(all_downloaded_wallpapers))
    for i in range(hero_limit):
        master_data["heroImages"].append({
            "id": f"hero_{i + 1}",
            "heroImageUrl": all_downloaded_wallpapers[i]
        })

    # Save out to wallpapers.json
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=4, ensure_ascii=False)

    print(f"Successfully generated {JSON_FILE} with structured categories and hero images.")

if __name__ == "__main__":
    fetch_wallpapers()
