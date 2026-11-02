from flask import Flask, jsonify, request, send_from_directory
import os
import re

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024

PRODUCTS = [
    {"name": "Everyday Linen Shirt", "price": 48, "category": "Tops", "sizes": "XS, S, M, L, XL"},
    {"name": "Weekend Knit Sweater", "price": 64, "category": "Tops", "sizes": "XS, S, M, L, XL"},
    {"name": "Everyday Straight Jeans", "price": 72, "category": "Bottoms", "sizes": "waist sizes 24, 26, 28, 30, 32"},
    {"name": "Sunday Midi Dress", "price": 78, "category": "Dresses", "sizes": "XS, S, M, L, XL"},
    {"name": "Everyday Canvas Sneaker", "price": 58, "category": "Shoes", "sizes": "shoe sizes 6, 7, 8, 9, 10"},
    {"name": "Soft Ribbed Tank", "price": 28, "category": "Tops", "sizes": "XS, S, M, L, XL"},
    {"name": "Weekend Baseball Cap", "price": 32, "category": "Accessories", "sizes": "one size"},
    {"name": "Everywhere Crossbody", "price": 54, "category": "Accessories", "sizes": "one size"},
]


def find_product(text):
    lowered = text.lower()
    for product in PRODUCTS:
        if product["name"].lower() in lowered:
            return product
    aliases = {
        "shirt": "Everyday Linen Shirt", "linen": "Everyday Linen Shirt",
        "sweater": "Weekend Knit Sweater", "knit": "Weekend Knit Sweater",
        "jeans": "Everyday Straight Jeans", "denim": "Everyday Straight Jeans",
        "dress": "Sunday Midi Dress", "sneaker": "Everyday Canvas Sneaker",
        "shoes": "Everyday Canvas Sneaker", "tank": "Soft Ribbed Tank",
        "cap": "Weekend Baseball Cap", "hat": "Weekend Baseball Cap",
        "bag": "Everywhere Crossbody", "crossbody": "Everywhere Crossbody",
    }
    for word, name in aliases.items():
        if word in lowered:
            return next(product for product in PRODUCTS if product["name"] == name)
    return None


def reply_to(message, history):
    text = message.lower().strip()
    context = " ".join(item.get("content", "") for item in history[-4:-1] if item.get("role") == "user").lower()
    lookup = f"{text} {context}"
    product = find_product(lookup)

    if re.search(r"\b(hi|hello|hey|good morning|good afternoon)\b", text):
        return "Hi! I can help you browse the collection, check sizes and prices, or use the shopping bag. What are you looking for?"

    if any(word in text for word in ("shipping", "delivery", "return", "refund", "exchange", "payment", "pay", "checkout", "stock")):
        return "This is a demo shop, so checkout does not take payment and shipping, returns, and live stock details haven't been set up. You can still browse items and try the cart."

    if any(word in text for word in ("size", "sizing", "fit", "waist")):
        if product:
            return f"The {product['name']} is listed in {product['sizes']}. I can't tell your exact fit from here, but you can choose a size from the product card."
        return "Available sizes depend on the item: most tops and the dress come in XS–XL; jeans use waist sizes 24–32; sneakers come in sizes 6–10; the cap and crossbody are one size. Which item are you considering?"

    if product:
        return f"{product['name']} is a {product['category'].lower()} item priced at ${product['price']}. Available sizes: {product['sizes']}. Select a size on its product card and press + to add it to your bag."

    if any(word in text for word in ("recommend", "suggest", "looking for", "find", "outfit", "browse")):
        category = next((name for name in ("tops", "bottoms", "dresses", "shoes", "accessories") if name in text), None)
        budget_match = re.search(r"(?:under|below|less than|budget of)\s*\$?\s*(\d+)", text)
        budget = int(budget_match.group(1)) if budget_match else None
        choices = [p for p in PRODUCTS if (not category or p["category"].lower() == category) and (not budget or p["price"] <= budget)]
        if choices:
            picks = ", ".join(f"{p['name']} (${p['price']})" for p in choices[:3])
            return f"Here are a few picks that might work: {picks}. Tell me what style or price range you prefer and I can narrow it down."
        return "I couldn't find an item matching that category and budget. Try asking for tops, bottoms, dresses, shoes, or accessories."

    if any(word in text for word in ("cart", "bag", "add", "order")):
        return "To add an item, choose its size on the product card and click the + button. Open 'Your bag' at the top to review items or change quantities. Checkout is only a demo."

    if any(word in text for word in ("price", "cost", "how much", "catalog", "items", "products")):
        return "The collection has tops from $28, jeans for $72, a dress for $78, sneakers for $58, and accessories from $32. Ask me about a specific item for its price and sizes."

    return "I can help with product details, prices, sizes, outfit ideas, and using the cart. Try asking 'What sizes does the linen shirt come in?' or 'Show me tops under $50.'"


@app.get("/")
def home():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    messages = body.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify(error="Send a message first."), 400

    history = [item for item in messages[-12:] if isinstance(item, dict)]
    last = history[-1]
    if last.get("role") != "user" or not isinstance(last.get("content"), str):
        return jsonify(error="Send a message first."), 400

    return jsonify(reply=reply_to(last["content"][:1000], history))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)

