import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

CATEGORIES = {
    "kawaii": "https://alphacoders.com/kawaii-wallpapers"
}

GITHUB_USER = "abdelhakimelmoumen"
REPO_NAME = "CuteWall-API"
BRANCH = "main"
BASE_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{REPO_NAME}/refs/heads/{BRANCH}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_DIR = "wallpapers"
JSON_FILE = "wallpapers.json"

CATEGORY_TAGS = {
    "kawaii": ["anime", "cartoon", "chibi", "cute", "kawaii"],
    "pastel": ["aesthetic", "minimal", "pastel", "pink", "soft"],
    "animals": ["animals", "cute", "furry", "kawaii", "pets"],
    "nature": ["calm", "landscape", "nature", "outdoors", "scenery"],
    "galaxy": ["galaxy", "planets", "space", "stars"],
    "ocean": ["blue", "calm", "ocean", "sea", "water"]
}

def fetch_wallpapers():
    master_data = {
        "heroImages": [
            {
                "id": "hero_1",
                "heroImageUrl": f"{BASE_RAW_URL}/hero/1_.png"
            },
            {
                "id": "hero_2",
                "heroImageUrl": f"{BASE_RAW_URL}/hero/2_.png"
            },
            {
                "id": "hero_3",
                "heroImageUrl": f"{BASE_RAW_URL}/hero/3_.png"
            }
        ],
        "categories": []
    }

    for category_id, start_url in CATEGORIES.items():
        category_dir = os.path.join(BASE_DIR, category_id)
        os.makedirs(category_dir, exist_ok=True)
        
        category_wallpapers = []
        counter = 1
        current_url = start_url
        page = 1
        visited_urls = set()

        while current_url and current_url not in visited_urls:
            visited_urls.add(current_url)
            print(f"Fetching category '{category_id}' - Page {page}: {current_url}")

            try:
                response = requests.get(current_url, headers=HEADERS, timeout=15)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch {current_url}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            wallpapers = soup.select('picture img, .thumb-container img, .thumb-pic img')

            if not wallpapers:
                print(f"No wallpapers found on {current_url}.")
                break

            new_images_on_page = 0

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

                    if not os.path.exists(save_path):
                        img_data = requests.get(src, headers=HEADERS, timeout=10).content
                        with open(save_path, 'wb') as f:
                            f.write(img_data)
                        print(f"Downloaded: {category_id}/{img_name}")

                    image_url = f"{BASE_RAW_URL}/{BASE_DIR}/{category_id}/{img_name}"
                    wallpaper_id = f"{category_id}_{counter}"
                    tags = CATEGORY_TAGS.get(category_id, ["cute", "wallpaper"])

                    # Prevent duplicate array entries if the same thumbnail is referenced multiple times
                    if not any(w['imageUrl'] == image_url for w in category_wallpapers):
                        category_wallpapers.append({
                            "id": wallpaper_id,
                            "imageUrl": image_url,
                            "tags": tags
                        })
                        counter += 1
                        new_images_on_page += 1

                except Exception as e:
                    print(f"Error processing image: {e}")

            print(f"Processed {new_images_on_page} new wallpapers from this page.")

            # Dynamically find the "Next" page link from the website's pagination layout
            next_link = soup.select_one('a.next, .pagination a:-soup-contains(">"), .pagination a:-soup-contains("Next"), ul.pagination li.active + li a')
            
            # Fallback search strategy for common pagination button classes if specific selectors miss
            if not next_link:
                for a in soup.select('.pagination a, .pages a'):
                    if 'next' in a.text.lower() or '»' in a.text or '>' in a.text:
                        next_link = a
                        break

            if next_link and next_link.get('href'):
                current_url = urljoin(start_url, next_link.get('href'))
                page += 1
            else:
                print(f"Reached the last page for '{category_id}'.")
                break

        category_block = {
            "id": category_id,
            "name": category_id.capitalize(),
            "wallpapers": category_wallpapers
        }
        master_data["categories"].append(category_block)

    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, indent=4, ensure_ascii=False)

    print(f"Successfully generated {JSON_FILE} with all scraped wallpapers.")

if __name__ == "__main__":
    fetch_wallpapers()
