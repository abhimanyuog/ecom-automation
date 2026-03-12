import os
import json
import base64
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from email.mime.text import MIMEText

from models import OrderEvent

app = FastAPI(title="Sportify Drafts Webhook")

# ── Scopes ────────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# ── Auth (Stateless for Cloud/Render) ─────────────────────────────────────────
def get_gmail_service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = None
    
    # Check for credentials in environment variables first (for Render)
    token_json_str = os.environ.get("GMAIL_TOKEN_JSON")
    
    # If not in env vars, try reading from local files (for local dev)
    if not token_json_str and os.path.exists("token.json"):
        with open("token.json", "r") as f:
            token_json_str = f.read()
            
    if token_json_str:
        try:
            token_info = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            print(f"❌ Failed to parse Google credentials: {e}")
            raise HTTPException(status_code=500, detail="Invalid Gmail credentials format.")
            
    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("🔄 Refreshed expired Gmail token successfully.")
                # We can save it back locally if it exists, so we don't refetch frequently locally
                if os.path.exists("token.json"):
                    with open("token.json", "w") as fh:
                        fh.write(creds.to_json())
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                raise HTTPException(status_code=500, detail="Gmail token expired. Run `python auth.py` locally and update GMAIL_TOKEN_JSON if on Render.")
        else:
            raise HTTPException(status_code=500, detail="Gmail token missing or invalid. Run `python auth.py`.")

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

# ── Gemini Draft Generator ────────────────────────────────────────────────────
def get_dynamic_drafts(payload: OrderEvent):
    try:
        import google.generativeai as genai
    except ImportError:
        raise HTTPException(status_code=500, detail="google-generativeai package missing.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Extract details from webhook payload
    customer_name = payload.customer.name
    customer_email = payload.customer.email
    order_num = payload.customer.order_count
    
    # Extract purchased products (join names if multiple)
    purchased_items = [item.product_name for item in payload.order.items]
    purchased_str = ", ".join(purchased_items)
    primary_product = purchased_items[0] if purchased_items else "Sporting Goods"

    # Build dummy order summary strictly for the prompt from real details
    order_summary_snippet = ""
    for item in payload.order.items:
        order_summary_snippet += f"  • {item.product_name} — ₹{item.price}\n"
    order_summary_snippet += f"  • Order #{payload.order.order_id}\n"
    order_summary_snippet += f"  • Estimated delivery: {payload.shipping.method} to {payload.shipping.address.city} {payload.shipping.address.postal_code}"

    prompt = f"""
    You are Sportify's expert customer success AI. Generate two personalized emails for a customer named {customer_name} ({customer_email}) who just bought '{purchased_str}'. This is their order #{order_num} with us.

    Email 1: Thank-You
    - Tone: Enthusiastic, personalized, and professional.
    - Mention exactly what they bought ({purchased_str}).
    - Include this exact order summary verbatim:
    {order_summary_snippet}
    - Vary the phrasing significantly from typical generic templates.

    Email 2: Cross-Sell
    - Tone: Athletic and encouraging.
    - Suggest 3 relevant complementary products for the {primary_product} they purchased.
    - Invent reasonable prices in INR (₹) for the suggestions.
    - Give a brief, appealing reason to buy each product.

    Respond STRICTLY in the following JSON format:
    [
      {{
        "label": "Thank-You",
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
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json"
            )
        )
        drafts = json.loads(response.text)
        return drafts
    except Exception as e:
        print(f"❌ Failed to parse Gemini response: {e}")
        raise HTTPException(status_code=500, detail=f"Gemini generation failed: {str(e)}")


# ── Webhook Routes ────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"status": "Sportify Webhook Service is running!"}

@app.post("/webhook")
async def process_order_webhook(payload: OrderEvent):
    """
    Receives JSON webhook, generates drafts via Gemini, and pushes them to Gmail.
    """
    # 1. Connect to Gmail
    print(f"🔗 Processing order {payload.order.order_id} for {payload.customer.name}...")
    service = get_gmail_service()
    
    # 2. Ask Gemini to write the drafts
    print("🧠 Generating personalized drafts via Gemini...")
    drafts = get_dynamic_drafts(payload)
    
    # 3. Create the drafts in Gmail
    results = []
    for d in drafts:
        print(f"📧 Creating draft: {d['label']}...")
        draft = create_draft(service, d["to"], d["subject"], d["body"])
        draft_id = draft.get("id", "unknown")
        results.append({
            "label": d["label"],
            "id": draft_id,
            "subject": d["subject"]
        })
        print(f"   ✅ Done (Draft ID: {draft_id})")

    return {
        "status": "success",
        "message": f"Successfully created {len(results)} drafts",
        "order_id": payload.order.order_id,
        "drafts": results
    }

if __name__ == "__main__":
    import uvicorn
    # Render assigns a port dynamically via the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
