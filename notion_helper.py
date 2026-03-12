import os
from notion_client import Client
from fastapi import HTTPException
from models import OrderEvent

def log_order_to_notion(payload: OrderEvent):
    notion_api_key = os.environ.get("NOTION_API_KEY")
    database_id = os.environ.get("NOTION_DATABASE_ID")

    if not notion_api_key or not database_id:
        print("⚠️ Notion credentials not found in environment variables. Skipping Notion logging.")
        return

    try:
        notion = Client(auth=notion_api_key)
        
        # Build a list of purchased products
        items_str = ", ".join([f"{item.quantity}x {item.product_name}" for item in payload.order.items])

        # Create the page (row) in the Notion Database
        new_page = {
            "Order ID": {"title": [{"text": {"content": payload.order.order_id}}]},
            "Customer Name": {"rich_text": [{"text": {"content": payload.customer.name}}]},
            "Customer Email": {"email": payload.customer.email},
            "Total Value": {"number": payload.order.order_value},
            "Currency": {"rich_text": [{"text": {"content": payload.order.currency}}]},
            "Items": {"rich_text": [{"text": {"content": items_str}}]},
            "Status": {"select": {"name": "New Order"}}
        }

        response = notion.pages.create(
            parent={"database_id": database_id},
            properties=new_page
        )
        print(f"✅ Successfully logged Order {payload.order.order_id} to Notion!")
        return response

    except Exception as e:
        print(f"❌ Failed to log to Notion: {e}")
        # We don't want to crash the whole webhook if Notion fails, just log it.
        pass
