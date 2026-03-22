"""
One-time script to generate YouTube OAuth2 credentials.
Run this LOCALLY before setting up GitHub Actions.

Usage:
  1. Download OAuth2 client_secrets.json from Google Cloud Console
  2. Run: python scripts/setup_youtube_auth.py
  3. Copy the printed JSON into your GitHub secret: YOUTUBE_CREDENTIALS_JSON
"""

import json
import os
import google_auth_oauthlib.flow
import google.oauth2.credentials

CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def main():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"ERROR: {CLIENT_SECRETS_FILE} not found.")
        print("Download it from: https://console.cloud.google.com/apis/credentials")
        print("Create an OAuth2 Client ID → Desktop App → Download JSON")
        return

    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES
    )

    print("Opening browser for Google OAuth2 authorization...")
    print("Sign in with the YouTube channel account.\n")
    creds = flow.run_local_server(port=8080)

    creds_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes),
    }

    print("\n" + "=" * 60)
    print("SUCCESS! Copy this JSON into your GitHub secret:")
    print("Secret name: YOUTUBE_CREDENTIALS_JSON")
    print("=" * 60)
    print(json.dumps(creds_dict, indent=2))
    print("=" * 60)

    # Also save locally
    with open("youtube_credentials.json", "w") as f:
        json.dump(creds_dict, f, indent=2)
    print(f"\nAlso saved to: youtube_credentials.json")
    print("(Add this file to .gitignore — never commit credentials!)")


if __name__ == "__main__":
    main()
