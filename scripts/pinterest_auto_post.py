import os
import sys
import argparse
import base64
import json
import re
import glob
import random
import requests
from dotenv import load_dotenv

ENV_FILE = '.env.local'
load_dotenv(ENV_FILE)

CLIENT_ID = os.getenv('PINTEREST_CLIENT_ID')
CLIENT_SECRET = os.getenv('PINTEREST_CLIENT_SECRET')
REFRESH_TOKEN = os.getenv('PINTEREST_REFRESH_TOKEN')
BOARD_ID = os.getenv('PINTEREST_BOARD_ID')
USE_SANDBOX = os.getenv('PINTEREST_USE_SANDBOX', 'False').lower() in ('true', '1', 'yes')

API_BASE = "https://api-sandbox.pinterest.com" if USE_SANDBOX else "https://api.pinterest.com"

# Resolve paths relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "pinterest_posted_log.json")

def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        print("Error: Pinterest OAuth credentials are not fully configured in .env.local.")
        print("Please run scripts/pinterest_auth.py first.")
        sys.exit(1)
        
    token_url = f"{API_BASE}/v5/oauth/token"
    
    # Basic Auth header
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {b64_auth}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }
    
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code != 200:
        print(f"Error refreshing access token (Endpoint: {token_url}): {response.status_code}")
        print(response.text)
        sys.exit(1)
        
    return response.json().get('access_token')

def list_boards(access_token):
    url = f"{API_BASE}/v5/boards"
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching boards: {response.status_code}")
        print(response.text)
        return
        
    data = response.json()
    items = data.get('items', [])
    
    if not items:
        print("No boards found in your account.")
        return
        
    print("\n" + "="*50)
    print(f"Your Pinterest Boards ({'SANDBOX' if USE_SANDBOX else 'PRODUCTION'}):")
    print("="*50)
    for item in items:
        print(f"Name: {item.get('name')}")
        print(f"ID  : {item.get('id')}")
        print(f"URL : {item.get('board_pins_modified_at') or ''}")
        print("-"*50)

def create_board(access_token, name, description="Created by API"):
    url = f"{API_BASE}/v5/boards"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "name": name,
        "description": description,
        "privacy": "PUBLIC"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        res_data = response.json()
        print(f"Success! Board '{name}' created.")
        print(f"Board ID: {res_data.get('id')}")
        return res_data.get('id')
    else:
        print(f"Error creating board: {response.status_code}")
        print(response.text)
        return None

def create_pin(access_token, board_id, title, description, link, image_url):
    if not board_id:
        print("Error: PINTEREST_BOARD_ID is not configured in .env.local.")
        print("Please fetch board ID using --list-boards and set it in your .env.local file.")
        return False
        
    url = f"{API_BASE}/v5/pins"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "board_id": board_id,
        "title": title[:100],  # Max 100 characters
        "description": description[:500],  # Max 500 characters
        "link": link,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        }
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code in [200, 201]:
        res_data = response.json()
        print(f"Success! Pin created.")
        print(f"Pin ID: {res_data.get('id')}")
        print(f"Pin URL: https://www.pinterest.com/pin/{res_data.get('id')}/")
        return True
    else:
        print(f"Error creating pin: {response.status_code}")
        print(response.text)
        return False

# --- New Functions for Automatic Rotation & Specific Post ---

def parse_markdown(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    meta = {}
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if match:
        front_matter = match.group(1)
        for line in front_matter.split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip().strip('"').strip("'")
    return meta

def get_posted_slugs():
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("posted_slugs", [])
        except Exception as e:
            print(f"Warning: Failed to read posted log: {e}")
    return []

def add_to_posted_log(slug):
    posted = get_posted_slugs()
    if slug not in posted:
        posted.append(slug)
        try:
            with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump({"posted_slugs": posted}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error writing to posted log: {e}")

def post_article_by_slug(slug):
    articles_dir = os.path.join(PROJECT_ROOT, "src", "content", "articles")
    file_path = os.path.join(articles_dir, f"{slug}.md")
    
    if not os.path.exists(file_path):
        print(f"Error: Article markdown not found for slug {slug} at {file_path}")
        return False
        
    meta = parse_markdown(file_path)
    if not meta:
        print(f"Error: Failed to parse markdown for slug {slug}")
        return False
        
    title = meta.get("title", "")
    # Clean HTML tags like <br>, <br />, \n from title
    title = re.sub(r'<[^>]*>', ' ', title)
    title = title.replace('\n', ' ').strip()
    # Normalize spaces
    title = re.sub(r'\s+', ' ', title)
    
    description = meta.get("excerpt", "")
    if not description:
        description = f"{title}に関する徹底比較・おすすめ情報をご紹介します。"
        
    link = f"https://www.mikke-style.com/articles/{slug}"
    image_url = f"https://www.mikke-style.com/eyecatch/{slug}-pin.png"
    
    print("\n" + "="*50)
    print(f"Posting Article Pin: {slug}")
    print(f"Base Domain: {API_BASE}")
    print(f"Target Board: {BOARD_ID}")
    print(f"Title: {title}")
    print(f"Desc : {description}")
    print(f"Link : {link}")
    print(f"Image: {image_url}")
    print("="*50 + "\n")
    
    access_token = get_access_token()
    success = create_pin(
        access_token=access_token,
        board_id=BOARD_ID,
        title=title,
        description=description,
        link=link,
        image_url=image_url
    )
    
    if success:
        add_to_posted_log(slug)
        print(f"Article '{slug}' successfully posted and logged.")
    return success

def post_past_article():
    articles_dir = os.path.join(PROJECT_ROOT, "src", "content", "articles")
    if not os.path.exists(articles_dir):
        print(f"Error: Articles directory not found at {articles_dir}")
        return False
        
    md_files = glob.glob(os.path.join(articles_dir, "*.md"))
    
    slugs = []
    for f in md_files:
        basename = os.path.basename(f)
        slug = basename[:-3]  # Remove '.md'
        
        # Exclude patterns
        if slug in ["GENERATION_RULES", "COLUMN_RULES", "COLUMN_SCHEMA"]:
            continue
        if slug.endswith("-fix"):
            continue
        slugs.append(slug)
        
    if not slugs:
        print("No eligible articles found to post.")
        return False
        
    posted_slugs = get_posted_slugs()
    unposted_slugs = [s for s in slugs if s not in posted_slugs]
    
    if not unposted_slugs:
        print("All articles have been rotated! Resetting log for the next round.")
        try:
            with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump({"posted_slugs": []}, f, indent=2)
        except Exception as e:
            print(f"Error resetting log: {e}")
        unposted_slugs = slugs
        
    # Choose one randomly
    selected_slug = random.choice(unposted_slugs)
    print(f"Selected unposted past article: {selected_slug} (out of {len(unposted_slugs)} remaining)")
    return post_article_by_slug(selected_slug)

def main():
    parser = argparse.ArgumentParser(description="Pinterest Auto-Post Utility")
    parser.add_argument('--list-boards', action='store_true', help='List all boards with their IDs')
    parser.add_argument('--create-board', type=str, help='Create a new board with the specified name')
    parser.add_argument('--post', action='store_true', help='Create and post a new pin')
    parser.add_argument('--title', type=str, help='Pin title')
    parser.add_argument('--desc', type=str, help='Pin description')
    parser.add_argument('--link', type=str, help='Destination URL')
    parser.add_argument('--image', type=str, help='Public image URL for the pin')
    parser.add_argument('--test', action='store_true', help='Run a test pin creation with mock data')
    
    # New CLI arguments
    parser.add_argument('--post-slug', type=str, help='Post a specific article by its slug name')
    parser.add_argument('--post-past', action='store_true', help='Automatically find and post an unposted past article')
    
    args = parser.parse_args()
    
    if not any([args.list_boards, args.create_board, args.post, args.test, args.post_slug, args.post_past]):
        parser.print_help()
        sys.exit(0)
        
    # Actions
    if args.post_past:
        post_past_article()
        
    elif args.post_slug:
        post_article_by_slug(args.post_slug)
        
    else:
        # Require access token for standard operations
        access_token = get_access_token()
        
        if args.list_boards:
            list_boards(access_token)
            
        elif args.create_board:
            create_board(access_token, args.create_board)
            
        elif args.test:
            print(f"Running test pin creation in {'SANDBOX' if USE_SANDBOX else 'PRODUCTION'} mode...")
            test_image = "https://images.unsplash.com/photo-1608248597279-f99d160bfcbc?w=800"
            test_title = "テストピン / Skin Care"
            test_desc = "これは自動投稿スクリプトによるテストピンです。スキンケアの情報を整理して発信します。"
            test_link = "https://www.mikke-style.com/"
            
            create_pin(
                access_token=access_token,
                board_id=BOARD_ID,
                title=test_title,
                description=test_desc,
                link=test_link,
                image_url=test_image
            )
            
        elif args.post:
            if not all([args.title, args.desc, args.link, args.image]):
                print("Error: --title, --desc, --link, and --image are all required for posting a pin.")
                sys.exit(1)
                
            create_pin(
                access_token=access_token,
                board_id=BOARD_ID,
                title=args.title,
                description=args.desc,
                link=args.link,
                image_url=args.image
            )

if __name__ == '__main__':
    main()
