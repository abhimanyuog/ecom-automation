import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

def authenticate():
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found! Please download it from Google Cloud Console.")
        return

    print("🌐 Starting local authentication server...")
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    
    # run_local_server uses a local web server to automatically receive the auth callback.
    # No need to manually copy and paste redirect URLs anymore!
    # Using port=0 lets the OS pick a random available port.
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())

    print("✅ Successfully authenticated and saved fresh token.json!")

if __name__ == '__main__':
    authenticate()
