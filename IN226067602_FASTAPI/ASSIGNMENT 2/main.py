from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()


products = [

    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "Office Chair", "price": 4999, "category": "Furniture", "in_stock": False},

]

feedback = []
orders = []


class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=300)


class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem] = Field(..., min_items=1)


class OrderRequest(BaseModel):
    product_id: int
    quantity: int


@app.get("/")
def home():
    return {"message": "FastAPI Day 2 Assignment API"}



@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


# Q1 — Filter products using query parameters

@app.get("/products/filter")
def filter_products(
    category: str = Query(None),
    max_price: int = Query(None),
    min_price: int = Query(None)
):

    result = products

    if category:
        result = [p for p in result if p["category"].lower() == category.lower()]

    if max_price:
        result = [p for p in result if p["price"] <= max_price]

    if min_price:
        result = [p for p in result if p["price"] >= min_price]

    return {"filtered_products": result, "total": len(result)}



# Q2 — Get only product name and price

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:

        if product["id"] == product_id:
            return {"name": product["name"], "price": product["price"]}

    return {"error": "Product not found"}




# Q3 — Submit customer feedback


@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.model_dump())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data.model_dump(),
        "total_feedback": len(feedback)
    }

@app.get("/feedback")
def get_feedback():

    return {
        "total_feedback": len(feedback),
        "feedback_list": feedback
    }



# Q4 — Product summary dashboard


@app.get("/products/summary")
def product_summary():

    in_stock = [p for p in products if p["in_stock"]]
    out_stock = [p for p in products if not p["in_stock"]]

    expensive = max(products, key=lambda p: p["price"])
    cheapest = min(products, key=lambda p: p["price"])

    categories = list(set(p["category"] for p in products))

    return {

        "total_products": len(products),

        "in_stock_count": len(in_stock),

        "out_of_stock_count": len(out_stock),

        "most_expensive": {
            "name": expensive["name"],
            "price": expensive["price"]
        },

        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },

        "categories": categories
    }



# Q5 — Bulk order processing


@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:

            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    order_record = {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }
    orders.append(order_record)

    return order_record

@app.get("/orders/bulk")
def view_bulk_orders():
    return {"orders": orders}

# Bonus — Order tracking system


@app.post("/orders")
def place_order(order: OrderRequest):

    order_data = {

        "order_id": len(orders) + 1,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "status": "pending"

    }

    orders.append(order_data)

    return {"message": "Order placed", "order": order_data}

@app.get("/orders")
def get_orders():
    return {
        "total_orders": len(orders),
        "orders": orders
    }

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:

        if order["order_id"] == order_id:
            return {"order": order}

    return {"error": "Order not found"}


@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:

        if order["order_id"] == order_id:

            order["status"] = "confirmed"

            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}