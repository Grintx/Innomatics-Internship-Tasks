from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI()

# --------------------------------------------------
# Product Data
# --------------------------------------------------

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
]

# --------------------------------------------------
# Runtime Storage
# --------------------------------------------------

cart = []
orders = []

# --------------------------------------------------
# Checkout Model
# --------------------------------------------------

class CheckoutRequest(BaseModel):
    customer_name: str
    delivery_address: str


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def find_product(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return p
    return None


def calculate_total(product, quantity):
    return product["price"] * quantity


# ==================================================
# CART SYSTEM
# ==================================================

# --------------------------------------------------
# Add to Cart
# --------------------------------------------------

@app.post("/cart/add")
def add_to_cart(
        product_id: int = Query(...),
        quantity: int = Query(1, gt=0)
):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(
            status_code=400,
            detail=f"{product['name']} is out of stock"
        )

    # Check if already in cart
    for item in cart:

        if item["product_id"] == product_id:

            item["quantity"] += quantity
            item["subtotal"] = calculate_total(product, item["quantity"])

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    new_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": calculate_total(product, quantity)
    }

    cart.append(new_item)

    return {
        "message": "Added to cart",
        "cart_item": new_item
    }


# --------------------------------------------------
# View Cart
# --------------------------------------------------

@app.get("/cart")
def view_cart():

    if not cart:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# --------------------------------------------------
# Remove Item from Cart
# --------------------------------------------------

@app.delete("/cart/{product_id}")
def remove_from_cart(product_id: int):

    for item in cart:

        if item["product_id"] == product_id:
            cart.remove(item)

            return {"message": f"{item['product_name']} removed from cart"}

    raise HTTPException(status_code=404, detail="Item not found in cart")


# --------------------------------------------------
# Checkout
# --------------------------------------------------

@app.post("/cart/checkout")
def checkout(data: CheckoutRequest):

    if not cart:
        raise HTTPException(
            status_code=400,
            detail="Cart is empty — add items first"
        )

    grand_total = 0
    placed_orders = []

    for item in cart:

        order = {
            "order_id": len(orders) + 1,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "total_price": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        placed_orders.append(order)

        grand_total += item["subtotal"]

    cart.clear()

    return {
        "message": "Checkout successful",
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# ==================================================
# ORDERS SYSTEM
# ==================================================

@app.get("/orders")
def get_orders():
    return {
        "orders": orders,
        "total_orders": len(orders)
    }


# ==================================================
# PRODUCT ENDPOINTS
# ==================================================

@app.get("/products")
def get_products():
    return {
        "products": products,
        "total": len(products)
    }


@app.get("/products/{product_id}")
def get_product(product_id: int):

    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"product": product}