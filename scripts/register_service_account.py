import os
import sys
from dotenv import load_dotenv
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha.types import AccessBinding

def main():
    load_dotenv(".env.local")
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH")
    if not credentials_path:
        print("❌ Error: GA4_CREDENTIALS_PATH is not set in .env.local")
        sys.exit(1)
        
    abs_credentials_path = os.path.abspath(credentials_path)
    if not os.path.exists(abs_credentials_path):
        print(f"❌ Error: Credentials file not found at {abs_credentials_path}")
        sys.exit(1)
        
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_credentials_path

    client = AnalyticsAdminServiceClient()
    service_account = "ga4-reader@gen-lang-client-0234162974.iam.gserviceaccount.com"
    property_id = "properties/532508021"

    access_binding = AccessBinding(
        user=service_account,
        roles=["roles/analytics.viewer"]
    )

    try:
        print(f"🔄 Attempting to add service account {service_account} to Property {property_id}...")
        client.create_access_binding(
            parent=property_id,
            access_binding=access_binding
        )
        print("✅ GA4にサービスアカウントを追加しました！")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
