#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def main():
    load_dotenv(".env.local")

    # OAuth 2.0 Playground Default Credentials (used as fallback if not set in .env.local)
    PLAYGROUND_CLIENT_ID = "407408718192.apps.googleusercontent.com"
    PLAYGROUND_CLIENT_SECRET = "m863mZ7713A45KmHgkua1w45"

    client_id = os.getenv("GOOGLE_CLIENT_ID") or PLAYGROUND_CLIENT_ID
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET") or PLAYGROUND_CLIENT_SECRET
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    if not refresh_token:
        print("❌ Error: GOOGLE_REFRESH_TOKEN is not set in .env.local")
        print("Please follow the instructions to obtain a Refresh Token from OAuth 2.0 Playground.")
        sys.exit(1)

    print("🔑 Authenticating with User OAuth 2.0...")
    try:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/webmasters"]
        )
        service = build("webmasters", "v3", credentials=creds)
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        sys.exit(1)

    site_url = "https://www.mikke-style.com/"
    service_account_email = "ga4-reader@gen-lang-client-0234162974.iam.gserviceaccount.com"

    print(f"🔄 Attempting to register {service_account_email} as OWNER of {site_url} in Search Console...")
    try:
        body = {
            "mailAddress": service_account_email,
            "role": "owner"
        }
        # Call webmasters permissions.insert API
        result = service.permissions().insert(siteUrl=site_url, body=body).execute()
        print("\n==========================================")
        print("🎉 SUCCESS!")
        print(f"   Service Account is now registered as OWNER of {site_url}!")
        print("==========================================")
        print("\n👉 Now you can run: python3 scripts/request_url_deletions.py")
    except Exception as e:
        print("\n❌ Failed to register service account in Search Console.")
        print(f"Error details: {e}")
        print("\n💡 Tip: Please make sure the Google account you authenticated with has Owner permission on Search Console.")

if __name__ == "__main__":
    main()
