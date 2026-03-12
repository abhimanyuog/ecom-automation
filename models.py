from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Store(BaseModel):
    store_id: str
    store_name: str

class ProductItem(BaseModel):
    product_id: str
    product_name: str
    category: str
    price: float
    quantity: int

class OrderDetails(BaseModel):
    order_id: str
    order_value: float
    currency: str
    payment_method: str
    items: List[ProductItem]

class Customer(BaseModel):
    customer_id: str
    name: str
    email: str
    city: str
    country: str
    order_count: int
    total_spent: float

class Address(BaseModel):
    city: str
    postal_code: str

class Shipping(BaseModel):
    method: str
    address: Address

class OrderEvent(BaseModel):
    event: str
    timestamp: str
    store: Store
    order: OrderDetails
    customer: Customer
    shipping: Shipping
