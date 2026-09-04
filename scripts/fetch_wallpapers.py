import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

URL = "https://alphacoders.com/kawaii-wallpapers"
# A standard user-agent is required, otherwise the site's bot protection will block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
SAVE_DIR = "wallpapers"

def fetch_wallpapers():
    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"Fetching page: {URL}")

    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch webpage: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all image tags. AlphaCoders serves wallpaper thumbnails via img tags
    images = soup.find_all('img')
    downloaded = 0

    for img in images:
        src = img.get('src')
        if not src or not src.startswith('http'):
            continue

        # Filter out UI elements, logos, and avatars
        if 'avatar' in src or 'logo' in src:
            continue

        try:
            img_name = os.path.basename(urlparse(src).path)
            # Ensure it has a valid image extension
            if not img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                img_name += '.jpg'

            save_path = os.path.join(SAVE_DIR, img_name)

            # Skip if we already downloaded this image in a previous run
            if os.path.exists(save_path):
                continue

            img_data = requests.get(src, headers=HEADERS, timeout=10).content
            with open(save_path, 'wb') as f:
                f.write(img_data)
            
            print(f"Downloaded: {img_name}")
            downloaded += 1

        except Exception as e:
            print(f"Error downloading {src}: {e}")

    print(f"Finished. Downloaded {downloaded} new wallpapers.")

if __name__ == "__main__":
    fetch_wallpapers()
