#!/usr/bin/env python3
"""
Sportify — Gmail Draft Creator (Dynamic GenAI version)
================================
Creates 2 dynamic personalized Gmail drafts for order ORD-48293 (Alex Sharma):
  1. Thank-You email (Repeat Buyer)
  2. Cross-Sell email (Fitness Smartwatch → earbuds, bands, tee)

SETUP (one-time, ~2 minutes):
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable "Gmail API"
  3. APIs & Services → OAuth consent screen → External → add your Gmail as test user
  4. Credentials → Create → OAuth 2.0 Client ID → Desktop App → Download JSON
  5. Rename the downloaded file to "credentials.json"
  6. Move it to the same folder as this script
  7. Run: python3 create_dynamic_gmail_drafts.py

On first run you will be asked to paste a URL into your browser and then paste
back the redirect URL. After that a token.json is saved — future runs are
fully automatic with no login needed.
"""

import os
import base64
import subprocess
from email.mime.text import MIMEText

# ── Scopes ────────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


# ── Auth ──────────────────────────────────────────────────────────────────────
def get_gmail_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None

    # Re-use saved token if it exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                print("\n❌  credentials.json not found.")
                print("    Follow the SETUP instructions at the top of this file.\n")
                raise SystemExit(1)

            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

            # Build the auth URL
            auth_url, _ = flow.authorization_url(
                access_type="offline",
                prompt="consent",
            )

            # Try to open browser automatically on macOS
            print("\n🌐  Opening Gmail authorisation page...")
            try:
                subprocess.run(["open", auth_url], check=True)
                print("    Browser opened. If nothing appeared, use the URL below.\n")
            except Exception:
                print("    Could not open browser automatically. Use the URL below.\n")

            print(f"    {auth_url}\n")
            print("──────────────────────────────────────────────────────────────")
            print("  After approving access, Google redirects to a page that may")
            print("  say 'This site can't be reached' — that is expected.")
            print("  Copy the FULL URL from your browser's address bar and paste")
            print("  it below.\n")

            redirect = input("  Paste redirect URL here: ").strip()

            flow.fetch_token(authorization_response=redirect)
            creds = flow.credentials

        # Save token for next run
        with open("token.json", "w") as fh:
            fh.write(creds.to_json())
        print("\n✅  Auth saved to token.json — no login needed next time.\n")

    return build("gmail", "v1", credentials=creds)


# ── Draft builder ─────────────────────────────────────────────────────────────
def create_draft(service, to, subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["to"] = to
    msg["subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()
    return draft


# ── Draft content ─────────────────────────────────────────────────────────────
def get_dynamic_drafts(customer_name="Alex Sharma", customer_email="alex.sharma@email.com", product="Fitness Smartwatch", order_num=2):
    import json
    try:
        import google.generativeai as genai
    except ImportError:
        print("\n❌ google-generativeai package is not installed.")
        print("   Please run: python3 -m pip install google-generativeai\n")
        raise SystemExit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ GEMINI_API_KEY environment variable not set.")
        print("   Please set it before running the script:")
        print("   export GEMINI_API_KEY='your_api_key'")
        print("   Get your API key at: https://aistudio.google.com/app/apikey\n")
        raise SystemExit(1)

    genai.configure(api_key=api_key)
    # Using gemini-2.5-flash which is fast and supports JSON response validation
    model = genai.GenerativeModel('gemini-2.5-flash')

    prompt = f"""
    You are Sportify's expert customer success AI. Generate two personalized emails for a customer named {customer_name} ({customer_email}) who just bought a '{product}'. This is their order #{order_num} with us.

    Email 1: Thank-You (Repeat Buyer)
    - Tone: Enthusiastic, personalized, and professional.
    - Mention the specific product they bought.
    - Include a brief dummy order summary (Order #ORD-48293, Estimated delivery: Standard Delivery to Delhi 110034).
    - Vary the phrasing significantly from typical generic templates.

    Email 2: Cross-Sell
    - Tone: Athletic and encouraging.
    - Suggest 3 relevant complementary products for the {product} (e.g., SoundPace Wireless Earbuds - ₹2,799, PowerGrip Resistance Bands Set - ₹1,299, AirDry Performance T-Shirt - ₹999).
    - Give a brief, appealing reason to buy each product.

    Respond STRICTLY in the following JSON format:
    [
      {{
        "label": "Thank-You (Repeat Buyer)",
        "to": "{customer_email}",
        "subject": "<Generate a highly personalized catchy subject>",
        "body": "<Generate the raw text email body (use standard newlines \\n)>"
      }},
      {{
        "label": "Cross-Sell",
        "to": "{customer_email}",
        "subject": "<Generate a highly personalized catchy cross-sell subject>",
        "body": "<Generate the raw text email body (use standard newlines \\n)>"
      }}
    ]
    """
    
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json"
        )
    )
    
    try:
        drafts = json.loads(response.text)
        return drafts
    except Exception as e:
        print(f"\n❌ Failed to parse Gemini response: {e}")
        print("Raw response:")
        print(response.text)
        raise SystemExit(1)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n🔐  Connecting to Gmail...")
    service = get_gmail_service()
    print("✅  Connected!\n")

    print("🧠  Generating personalized drafts via Gemini...")
    drafts = get_dynamic_drafts()

    results = []
    for d in drafts:
        print(f"📧  Creating draft: {d['label']}...")
        draft = create_draft(service, d["to"], d["subject"], d["body"])
        draft_id = draft.get("id", "unknown")
        print(f"    ✅  Done  (Draft ID: {draft_id})")
        print(f"    To:      {d['to']}")
        print(f"    Subject: {d['subject']}\n")
        results.append({"label": d["label"], "id": draft_id})

    print("─" * 52)
    print("🎉  Both drafts are in your Gmail Drafts folder.")
    print("─" * 52)
    for r in results:
        print(f"  • {r['label']}  (ID: {r['id']})")
    print()


if __name__ == "__main__":
    main()
