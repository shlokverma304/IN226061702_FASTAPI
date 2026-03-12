from fastapi import FastAPI, Query, Response, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

@app.get("/")
def home():
    return {"message": "FastAPI is working!"}

products = [
    {"id": 1, "name": "Notebook", "price": 50, "category": "Stationery", "in_stock": True},
    {"id": 2, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 4, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},
]

@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}

@app.get("/products/category/{category_name}")
def get_by_category(category_name: str):
    result = [p for p in products if p["category"] == category_name]
    
    if not result:
        return {"error": "No products found in this category"}
    
    return {
        "category": category_name,
        "products": result,
        "total": len(result)
    }

@app.get("/products/instock")
def get_instock():
    available = [p for p in products if p["in_stock"]]
    return {
        "in_stock_products": available,
        "count": len(available)
    }

#Bonus
@app.get("/products/deals")
def get_deals():
    cheapest = min(products, key=lambda p: p["price"])
    expensive = max(products, key=lambda p: p["price"])
    return {
        "best_deal": cheapest,
        "premium_pick": expensive
    }

#Bonus Day_3
@app.put("/products/discount")
def apply_discount(category: str, discount_percent: int):
    
    updated_products = []

    for p in products:
        if p["category"] == category:
            discount_amount = p["price"] * discount_percent / 100
            p["price"] = int(p["price"] - discount_amount)

            updated_products.append({
                "name": p["name"],
                "new_price": p["price"]
            })

    return {
        "category": category,
        "discount_percent": discount_percent,
        "updated_products": updated_products
    }

@app.get("/products/filter")
def filter_products(min_price: int = Query(None), max_price: int = Query(None)):
    result = products
    if min_price is not None:
        result = [p for p in result if p["price"] >= min_price]
    if max_price is not None:
        result = [p for p in result if p["price"] <= max_price]
    return {"products": result, "count": len(result)}

@app.get("/products/{product_id}/price")
def get_price(product_id: int):
    for p in products:
        if p["id"] == product_id:
            return {"name": p["name"], "price": p["price"]}
    return {"error": "Product not found"}

class NewProduct(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool = True

@app.get("/products/audit")
def products_audit():

    total_products = len(products)

    in_stock_products = [p for p in products if p["in_stock"]]
    out_stock_products = [p for p in products if not p["in_stock"]]

    total_stock_value = sum(p["price"] for p in in_stock_products)

    most_expensive = max(products, key=lambda p: p["price"])

    return {
        "total_products": total_products,
        "in_stock_count": len(in_stock_products),
        "out_of_stock_count": len(out_stock_products),
        "total_stock_value": total_stock_value,
        "most_expensive_product": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        }
    }    

@app.post("/products")
def add_product(new_product: NewProduct, response: Response):
    for p in products:
        if p["name"].lower() == new_product.name.lower():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"error": "Product with this name already exists"}

    next_id = max(p["id"] for p in products) + 1

    product = {
        "id": next_id,
        "name": new_product.name,
        "price": new_product.price,
        "category": new_product.category,
        "in_stock": new_product.in_stock
    }

    products.append(product)
    response.status_code = status.HTTP_201_CREATED

    return {
        "message": "Product added",
        "product": product
    }

@app.put("/products/{product_id}")
def update_product(product_id: int, response: Response, price: int = None, in_stock: bool = None):

    for p in products:
        if p["id"] == product_id:

            if price is not None:
                p["price"] = price

            if in_stock is not None:
                p["in_stock"] = in_stock

            return {"message": "Product updated", "product": p}

    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not found"}

@app.delete("/products/{product_id}")
def delete_product(product_id: int, response: Response):

    for p in products:
        if p["id"] == product_id:
            products.remove(p)
            return {"message": f"Product '{p['name']}' deleted"}

    response.status_code = status.HTTP_404_NOT_FOUND
    return {"error": "Product not found"}

feedback_list = []

class CustomerFeedback(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

@app.post("/feedback")
def submit_feedback(feedback: CustomerFeedback):
    feedback_list.append(feedback)
    return {
        "message": "Feedback submitted successfully",
        "feedback": feedback,
        "total_feedback": len(feedback_list)
    }

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str
    contact_email: str
    items: List[OrderItem]

@app.post("/orders/bulk")
def place_bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({"product_id": item.product_id, "reason": "Product not found"})

        elif not product["in_stock"]:
            failed.append({"product_id": item.product_id, "reason": f"{product['name']} is out of stock"})

        else:
            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }

#Bonus Day_2
orders = []
order_counter = 1

class SimpleOrder(BaseModel):
    product_id: int
    quantity: int

@app.post("/orders")
def create_order(order: SimpleOrder):

    global order_counter

    product = next((p for p in products if p["id"] == order.product_id), None)

    if not product:
        return {"error": "Product not found"}

    new_order = {
        "order_id": order_counter,
        "product": product["name"],
        "quantity": order.quantity,
        "status": "pending"
    }

    orders.append(new_order)
    order_counter += 1

    return {"message": "Order placed", "order": new_order}

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return order

    return {"error": "Order not found"}

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {"message": "Order confirmed", "order": order}

    return {"error": "Order not found"}

