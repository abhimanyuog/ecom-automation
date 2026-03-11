#!/usr/bin/env python3
"""
Sportify — Gmail Draft Creator
================================
Creates 2 Gmail drafts for order ORD-48293 (Alex Sharma):
  1. Thank-You email (Repeat Buyer)
  2. Cross-Sell email (Fitness Smartwatch → earbuds, bands, tee)

SETUP (one-time, ~2 minutes):
  1. Go to https://console.cloud.google.com
  2. Create a project → Enable "Gmail API"
  3. APIs & Services → OAuth consent screen → External → add your Gmail as test user
  4. Credentials → Create → OAuth 2.0 Client ID → Desktop App → Download JSON
  5. Rename the downloaded file to "credentials.json"
  6. Move it to the same folder as this script
  7. Run: python3 create_gmail_drafts.py

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
DRAFTS = [
    {
        "label": "Thank-You (Repeat Buyer)",
        "to": "alex.sharma@email.com",
        "subject": "Great to see you again, Alex! 🎉",
        "body": (
            "Hi Alex,\n\n"
            "Great to see you again! 😊 You clearly have great taste.\n\n"
            "Your Fitness Smartwatch is confirmed and we're already getting it ready "
            "for you. This is your 2nd order with us — and we appreciate every single one.\n\n"
            "Here's your order summary:\n\n"
            "  • Fitness Smartwatch — ₹1,999\n"
            "  • Order #ORD-48293\n"
            "  • Estimated delivery: Standard Delivery to Delhi 110034\n\n"
            "As always, if you need anything at all, just hit reply.\n\n"
            "With thanks,\n"
            "Team Sportify"
        ),
    },
    {
        "label": "Cross-Sell",
        "to": "alex.sharma@email.com",
        "subject": "Level up your fitness game, Alex 💪",
        "body": (
            "Hi Alex,\n\n"
            "Since you just added a Fitness Smartwatch to your arsenal, here are a few "
            "things that'll make every workout even better:\n\n"
            "🎧 SoundPace Wireless Earbuds — ₹2,799\n"
            "IPX5 sweat-resistant with a secure fit built for movement — the perfect "
            "workout soundtrack companion for your new smartwatch.\n\n"
            "💪 PowerGrip Resistance Bands Set — ₹1,299\n"
            "Track your reps on your new smartwatch while you train — 5 tension levels "
            "for every exercise from warm-up to burnout.\n\n"
            "👕 AirDry Performance T-Shirt — ₹999\n"
            "Quick-dry, anti-odour fabric so you stay fresh whether you're hitting the "
            "gym or going for a run.\n\n"
            "Keep crushing it,\n"
            "Team Sportify"
        ),
    },
]


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("\n🔐  Connecting to Gmail...")
    service = get_gmail_service()
    print("✅  Connected!\n")

    results = []
    for d in DRAFTS:
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