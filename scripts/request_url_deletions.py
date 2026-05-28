#!/usr/bin/env python3
import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
credentials_path = os.path.join(ROOT_DIR, "credentials", "ga4-key.json")

if not os.path.exists(credentials_path):
    print(f"❌ Error: Credentials file not found at {credentials_path}")
    sys.exit(1)

# List of deleted slugs
slugs = [
    "20260427-2026年片付け上手になれる見せる収納隠す収納おす",
    "20260428-台所に手間をかけない道具を共働き家庭の時短キッチン",
    "20260428-肌に正直なものだけを乾燥肌敏感肌のスキンケアアイテ",
    "20260429-思考が加速する机の話在宅ワーカーのデスク文具6選",
    "20260430-在宅ワークの肩こりに本気の回答を筋膜ケアボディリカ",
    "20260502-家をもっと賢くするスマートホームデバイス6選",
    "20260502-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ",
    "20260503-料理人が静かに選ぶ本物の道具燕三条関産の本格キッチ",
    "20260503-深い眠りには静かな準備がある睡眠の質を高める寝室入",
    "20260508-書くことがもっと好きになるこだわりデスク文具6選",
    "20260512-湯船でほどける夜に疲れた日の入浴グッズバスケア6選",
    "20260518-体を動かすのが楽しくなってきたフィットネスボディケ",
    "20260519-ながら聴きをもっと豊かにワイヤレスイヤホン-こだわ",
    "20260520-夜空の下へ持ち出したいアウトドアキャンプギア6選",
    "20260522-音で彩る自分だけの朝ポータブルスピーカーbluet",
    "20260524-日常に小さな贅沢を重ねる収納上手なスタッキングマグ6選",
    "20260524-肌は夜に育てる30代から始めるメンズスキンケア夜ル",
    "20260525-灯を落としてから肌と向き合う夜就寝前ナイトケアコス"
]

urls = [f"https://www.mikke-style.com/articles/{slug}" for slug in slugs]

print("🔑 Authenticating with Service Account for Google Indexing API...")
try:
    creds = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=["https://www.googleapis.com/auth/indexing"]
    )
    service = build("indexing", "v3", credentials=creds)
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    sys.exit(1)

print(f"🔄 Requesting URL deletion index updates for {len(urls)} URLs...")
success_count = 0
for url in urls:
    try:
        body = {
            "url": url,
            "type": "URL_DELETED"
        }
        # Execute indexing delete API notification
        result = service.urlNotifications().publish(body=body).execute()
        print(f"✅ Successfully requested DELETION index update: {url}")
        success_count += 1
    except Exception as e:
        print(f"❌ Failed deletion request for {url}: {e}")

print(f"\n==========================================")
print(f"🎉 Completed deletion notifications!")
print(f"   - Success: {success_count}/{len(urls)}")
print(f"==========================================")
