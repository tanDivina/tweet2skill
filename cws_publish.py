import os
import zipfile
import sys
import json
import urllib.request
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Configuration details
EXTENSION_ID = "cbmghhnbpdfehmkifhlbckcphclmbifn"  # Replace with CWS Extension ID
KEY_FILE = "gsc_key.json"
ZIP_FILE = "tweet2skill-extension.zip"

def get_access_token():
    """Authenticates using the Service Account JSON and returns an access token."""
    if not os.path.exists(KEY_FILE):
        print(f"Error: {KEY_FILE} not found in workspace.")
        sys.exit(1)
        
    scopes = ["https://www.googleapis.com/auth/chromewebstore"]
    credentials = service_account.Credentials.from_service_account_file(
        KEY_FILE, scopes=scopes
    )
    
    # Refresh to retrieve the token
    credentials.refresh(Request())
    return credentials.token

def upload_extension(token):
    """Uploads the zip package to the Chrome Web Store draft."""
    if not os.path.exists(ZIP_FILE):
        print(f"Error: {ZIP_FILE} not found. Package the extension first.")
        sys.exit(1)

    print(f"Uploading {ZIP_FILE} to Chrome Web Store...")
    url = f"https://www.googleapis.com/upload/chromewebstore/v1.1/items/{EXTENSION_ID}"
    
    with open(ZIP_FILE, "rb") as f:
        zip_data = f.read()

    req = urllib.request.Request(
        url,
        data=zip_data,
        headers={
            "Authorization": f"Bearer {token}",
            "x-goog-api-version": "2"
        },
        method="PUT"
    )

    try:
        with urllib.request.urlopen(req) as res:
            result = json.loads(res.read().decode("utf-8"))
            if result.get("uploadState") == "SUCCESS":
                print("✔ Extension uploaded successfully!")
                print(f"Details: {result}")
            else:
                print(f"Upload failed: {result}")
    except Exception as e:
        print(f"HTTP Error during upload: {e}")

if __name__ == "__main__":
    print("Initiating automated Chrome Web Store upload...")
    token = get_access_token()
    upload_extension(token)
