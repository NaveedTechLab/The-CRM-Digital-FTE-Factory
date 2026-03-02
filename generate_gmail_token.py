"""
One-time script to generate Gmail OAuth2 token.
This will open your browser - sign in with pakmonsters@gmail.com
and allow access to send emails.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os
import json

SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_PATH = './credentials/gmail_credentials.json'
TOKEN_PATH = './credentials/gmail_token.json'

def main():
    print("=" * 50)
    print("Gmail OAuth2 Token Generator")
    print("=" * 50)
    print(f"\nCredentials file: {os.path.abspath(CREDENTIALS_PATH)}")
    print(f"Token will be saved to: {os.path.abspath(TOKEN_PATH)}")

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"\nERROR: Credentials file not found at {CREDENTIALS_PATH}")
        return

    if os.path.exists(TOKEN_PATH):
        print(f"\nToken already exists at {TOKEN_PATH}")
        resp = input("Regenerate? (y/n): ").strip().lower()
        if resp != 'y':
            print("Keeping existing token.")
            return

    print("\nOpening browser for Google Sign-In...")
    print("Sign in with: pakmonsters@gmail.com")
    print("Allow 'Send email' permission\n")

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=8090)

    # Save the token
    with open(TOKEN_PATH, 'w') as token_file:
        token_file.write(creds.to_json())

    print(f"\nToken saved to {TOKEN_PATH}")
    print("Email sending is now enabled!")

if __name__ == '__main__':
    main()
