#!/usr/bin/env python3
import os
import json
import re
import glob
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

# Load env variables from .env.local
load_dotenv(".env.local")

# Paths and Configs
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(ROOT_DIR, "src/content/articles")
SITEMAP_PATH = os.path.join(ROOT_DIR, "public/sitemap-0.xml")
CACHE_DIR = os.path.join(ROOT_DIR, ".cache")
YESTERDAY_PV_CACHE = os.path.join(CACHE_DIR, "ga4_pvs_yesterday.json")

os.makedirs(CACHE_DIR, exist_ok=True)

def update_sitemap():
    print("🔄 [Step 1] Updating Sitemap via Next-Sitemap...")
    try:
        # Run npx next-sitemap
        subprocess.run(["npx", "next-sitemap"], check=True, cwd=ROOT_DIR)
        print("✅ Sitemap updated successfully.")
    except Exception as e:
        print(f"❌ Failed to update sitemap: {e}")

def get_indexing_service():
    # Attempt to authenticate with OAuth 2.0 Playground credentials first
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
    
    # Default Playground Credentials
    PLAYGROUND_CLIENT_ID = "407408718192.apps.googleusercontent.com"
    PLAYGROUND_CLIENT_SECRET = "m863mZ7713A45KmHgkua1w45"
    
    client_id = os.getenv("GOOGLE_CLIENT_ID") or PLAYGROUND_CLIENT_ID
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or PLAYGROUND_CLIENT_SECRET
    
    if refresh_token:
        print("🔑 Authenticating with OAuth 2.0 Playground credentials...")
        try:
            creds = Credentials(
                token=None,
                refresh_token=refresh_token,
                client_id=client_id,
                client_secret=client_secret,
                token_uri="https://oauth2.googleapis.com/token",
                scopes=["https://www.googleapis.com/auth/indexing"]
            )
            return build("indexing", "v3", credentials=creds)
        except Exception as e:
            print(f"⚠️ OAuth 2.0 Playground authentication failed: {e}")

            
    # Fallback to Service Account
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH")
    if credentials_path:
        abs_path = os.path.abspath(credentials_path)
        if os.path.exists(abs_path):
            print("🔑 Authenticating with Service Account...")
            try:
                creds = service_account.Credentials.from_service_account_file(
                    abs_path,
                    scopes=["https://www.googleapis.com/auth/indexing"]
                )
                return build("indexing", "v3", credentials=creds)
            except Exception as e:
                print(f"❌ Service Account authentication failed: {e}")
                
    print("❌ No valid authentication methods found for Google Indexing API.")
    return None

def request_indexing(urls):
    print("🔄 [Step 2] Sending URL Indexing Requests...")
    service = get_indexing_service()
    if not service:
        print("⚠️ Indexing service unavailable. Skipping.")
        return
        
    # Standard limit is 200/day
    limit = 200
    requested = 0
    
    for url in urls[:limit]:
        try:
            body = {
                "url": url,
                "type": "URL_UPDATED"
            }
            # Execute standard Google Indexing API publish
            service.urlNotifications().publish(body=body).execute()
            print(f"   - Requested Indexing for: {url}")
            requested += 1
        except Exception as e:
            print(f"   ❌ Failed request for {url}: {e}")
            
    print(f"✅ Indexing requests sent: {requested}/{len(urls)}")

def fetch_ga4_pvs():
    property_id = os.getenv("GA4_PROPERTY_ID")
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH")
    
    if not property_id or not credentials_path:
        print("⚠️ GA4 credentials missing. Skipping GA4 fetch.")
        return {}
        
    abs_path = os.path.abspath(credentials_path)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_path
    
    try:
        client = BetaAnalyticsDataClient()
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews")],
            date_ranges=[DateRange(start_date="today", end_date="today")], # Compare current day's PV
        )
        response = client.run_report(request)
        
        pvs = {}
        for row in response.rows:
            path = row.dimension_values[0].value
            pv_val = int(row.metric_values[0].value)
            pvs[path] = pv_val
        return pvs
    except Exception as e:
        print(f"❌ GA4 fetch failed: {e}")
        return {}

def report_ga4_growth():
    print("🔄 [Step 3] Analyzing GA4 Traffic and PV Growth...")
    current_pvs = fetch_ga4_pvs()
    if not current_pvs:
        return
        
    # Read yesterday's PVs from cache
    yesterday_pvs = {}
    if os.path.exists(YESTERDAY_PV_CACHE):
        try:
            with open(YESTERDAY_PV_CACHE, "r", encoding="utf-8") as f:
                yesterday_pvs = json.load(f)
        except Exception as e:
            print(f"⚠️ Failed to read yesterday's PV cache: {e}")
            
    # Calculate difference
    print("\n📈 --- GA4 PV Daily Comparison Report ---")
    print(f"{'Page Path':<60} | {'Yesterday PV':<15} | {'Today PV':<10} | {'Change':<10}")
    print("-" * 105)
    
    for path, today_pv in current_pvs.items():
        # Only check articles
        if not path.startswith("/articles/"):
            continue
            
        yesterday_pv = yesterday_pvs.get(path, 0)
        diff = today_pv - yesterday_pv
        change_str = f"+{diff}" if diff > 0 else f"{diff}"
        print(f"{path:<60} | {yesterday_pv:<15} | {today_pv:<10} | {change_str:<10}")
        
    print("-" * 105)
    
    # Save current PVs as yesterday's cache for tomorrow
    try:
        with open(YESTERDAY_PV_CACHE, "w", encoding="utf-8") as f:
            json.dump(current_pvs, f, ensure_ascii=False, indent=2)
        print("✅ Saved current PVs to yesterday's cache.")
    except Exception as e:
        print(f"❌ Failed to cache current PVs: {e}")

def detect_low_internal_links():
    print("🔄 [Step 4] Detecting Articles with low internal links (< 3)...")
    md_files = [f for f in glob.glob(os.path.join(ARTICLES_DIR, "*.md")) if os.path.basename(f) != "GENERATION_RULES.md"]
    
    low_link_articles = []
    
    for fpath in md_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            
        slug = os.path.basename(fpath).replace(".md", "")
        
        # Match links to other articles: e.g. [title](/articles/slug)
        # Note: we search for "/articles/" in markdown links
        links = re.findall(r"\]\(/articles/[a-zA-Z0-9\-%_\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+", content)
        
        # Count links
        link_count = len(links)
        
        if link_count < 3:
            low_link_articles.append((slug, link_count))
            
    print(f"\n⚠️ --- Articles with Low Internal Links (< 3) ---")
    print(f"{'Article Slug':<65} | {'Internal Links Count':<20}")
    print("-" * 90)
    for slug, count in low_link_articles:
        print(f"{slug:<65} | {count:<20}")
    print("-" * 90)
    print(f"Total articles with low links: {len(low_link_articles)}\n")

def main():
    print(f"=== SEO Automation Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    update_sitemap()
    
    # Read URLs from sitemap
    urls = []
    if os.path.exists(SITEMAP_PATH):
        try:
            with open(SITEMAP_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            matches = re.findall(r"<loc>(https?://[^<]+)</loc>", content)
            urls = [m.strip() for m in matches if "/articles/" in m]
        except Exception as e:
            print(f"❌ Failed to parse sitemap: {e}")
            
    if urls:
        request_indexing(urls)
        
    report_ga4_growth()
    detect_low_internal_links()
    print("=== SEO Automation Run Finished ===\n")

if __name__ == "__main__":
    main()
