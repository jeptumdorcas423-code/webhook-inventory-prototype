from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

stock = {}

WEBHOOK_SECRET = "my-secret-key"

@app.get("/")
def home():
    return {"message": "My webhook server is running!"}

@app.post("/webhook")
def receive_webhook(data: dict, x_webhook_secret: str = Header(None)):
    if x_webhook_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    product = data["product"]
    quantity = data["stock"]

    stock[product] = quantity

    return {
        "message": "Stock updated!",
        "product": product,
        "stock": quantity
    }
@app.get("/stock/{product}")
def get_stock(product: str):
    quantity = stock.get(product, 0)

    return {
        "product": product,
        "stock": quantity
    }