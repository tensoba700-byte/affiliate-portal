import os
import requests
import base64
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

# Load env variables from .env.local
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env.local')
load_dotenv(env_path)

CLIENT_ID = os.getenv("PINTEREST_CLIENT_ID")
CLIENT_SECRET = os.getenv("PINTEREST_CLIENT_SECRET")
REDIRECT_URI = os.getenv("PINTEREST_REDIRECT_URI", "http://localhost:8085")
USE_SANDBOX = os.getenv("PINTEREST_USE_SANDBOX", "True").lower() == "true"

BASE_DOMAIN = "https://api-sandbox.pinterest.com" if USE_SANDBOX else "https://api.pinterest.com"
AUTH_DOMAIN = "https://www.pinterest.com"

def generate_auth_url():
    scopes = "boards:read,boards:write,pins:read,pins:write"
    url = f"{AUTH_DOMAIN}/oauth/?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={scopes}"
    return url

def list_boards(access_token):
    boards_url = f"{BASE_DOMAIN}/v5/boards"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(boards_url, headers=headers)
    if response.status_code == 200:
        boards = response.json().get("items", [])
        print("\n=== Available Boards ===")
        for b in boards:
            print(f"Name: {b.get('name')} | ID: {b.get('id')}")
        print("=========================\n")
    else:
        print(f"Failed to fetch boards: {response.status_code}")
        print(response.text)

def get_tokens(auth_code):
    token_url = f"{BASE_DOMAIN}/v5/oauth/token"
    
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI
    }
    
    response = requests.post(token_url, data=data, headers=headers)
    if response.status_code == 200:
        res_data = response.json()
        print("Success! Tokens obtained.")
        print(f"Access Token: {res_data.get('access_token')[:20]}...")
        print(f"Refresh Token: {res_data.get('refresh_token')}")
        
        # List boards using the obtained access token
        list_boards(res_data.get("access_token"))
        
        return res_data.get("refresh_token")
    else:
        print(f"Failed to obtain tokens: {response.status_code}")
        print(response.text)
        return None

def update_env_file(refresh_token):
    if not refresh_token:
        return
        
    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("PINTEREST_REFRESH_TOKEN="):
            new_lines.append(f"PINTEREST_REFRESH_TOKEN='{refresh_token}'\n")
            updated = True
        else:
            new_lines.append(line)
            
    if not updated:
        new_lines.append(f"PINTEREST_REFRESH_TOKEN='{refresh_token}'\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print(f"Updated PINTEREST_REFRESH_TOKEN in {env_path}")

def main():
    print("=== Pinterest OAuth Helper ===")
    print(f"Target Environment: {'SANDBOX' if USE_SANDBOX else 'PRODUCTION'}")
    print(f"Client ID: {CLIENT_ID}")
    
    auth_url = generate_auth_url()
    print("\n1. Open the following URL in your browser and authorize the application:")
    print("-" * 80)
    print(auth_url)
    print("-" * 80)
    
    print("\n2. After authorization, you will be redirected to localhost (which might show a connection error, this is fine).")
    print("   Copy the entire redirect URL from your browser's address bar and paste it below.")
    
    redirect_url = input("\nRedirect URL: ").strip()
    
    try:
        parsed = urlparse(redirect_url)
        qs = parse_qs(parsed.query)
        auth_code = qs.get("code")[0]
        print(f"\nExtracted Authorization Code: {auth_code}")
        
        refresh_token = get_tokens(auth_code)
        if refresh_token:
            update_env_file(refresh_token)
    except Exception as e:
        print(f"Error parsing redirect URL or obtaining token: {e}")

if __name__ == "__main__":
    main()
