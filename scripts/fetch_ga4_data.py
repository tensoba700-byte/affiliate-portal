import os
import sys
from dotenv import load_dotenv
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

def fetch_ga4_metrics():
    # Load env variables from .env.local
    load_dotenv(".env.local")
    
    property_id = os.getenv("GA4_PROPERTY_ID")
    credentials_path = os.getenv("GA4_CREDENTIALS_PATH")
    
    if not property_id:
        print("❌ Error: GA4_PROPERTY_ID is not set in .env.local")
        sys.exit(1)
        
    if not credentials_path:
        print("❌ Error: GA4_CREDENTIALS_PATH is not set in .env.local")
        sys.exit(1)
        
    # Get absolute path for credentials and set GOOGLE_APPLICATION_CREDENTIALS
    abs_credentials_path = os.path.abspath(credentials_path)
    if not os.path.exists(abs_credentials_path):
        print(f"❌ Error: Credentials file not found at {abs_credentials_path}")
        sys.exit(1)
        
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = abs_credentials_path
    
    print(f"🔄 Connecting to GA4 Property: {property_id}...")
    try:
        client = BetaAnalyticsDataClient()
        
        # Request: fetch active users, screen page views, and bounce rate per pagePath for last 30 days
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="activeUsers"),
                Metric(name="bounceRate")
            ],
            date_ranges=[DateRange(start_date="30daysAgo", end_date="today")],
        )
        
        response = client.run_report(request)
        
        print("\n📊 --- GA4 Traffic & User Engagement Report (Last 30 Days) ---")
        print(f"{'Page Path':<60} | {'PVs':<10} | {'Users':<10} | {'Bounce Rate':<12}")
        print("-" * 100)
        
        results = []
        for row in response.rows:
            page_path = row.dimension_values[0].value
            pvs = row.metric_values[0].value
            users = row.metric_values[1].value
            
            # Bounce rate is usually a float string (e.g. 0.45 or 45.0 depending on API format)
            # We parse and format it nicely
            try:
                bounce_val = float(row.metric_values[2].value)
                # GA4 API returns bounceRate as a fraction (e.g. 0.45) or percentage.
                # Usually it's a fraction. If it's <= 1.0, we convert it to percentage.
                if bounce_val <= 1.0:
                    bounce_rate = f"{bounce_val * 100:.1f}%"
                else:
                    bounce_rate = f"{bounce_val:.1f}%"
            except ValueError:
                bounce_rate = row.metric_values[2].value
                
            print(f"{page_path:<60} | {pvs:<10} | {users:<10} | {bounce_rate:<12}")
            results.append({
                "page_path": page_path,
                "pageviews": pvs,
                "users": users,
                "bounce_rate": bounce_rate
            })
            
        print("-" * 100)
        print(f"Total rows fetched: {len(results)}\n")
        return results

    except Exception as e:
        print(f"❌ Failed to fetch data from GA4: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fetch_ga4_metrics()
