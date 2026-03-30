import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔓 Allows GitHub Pages to talk to Railway without security blocks
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 🏠 Basic load screen to prove it's online
@app.route('/')
def home():
    return "Liquid Leverage Backend is Running!"

# 🚨 Listens for clicks from the Mini App
@app.route('/api/trade', methods=['POST', 'OPTIONS'])
def execute_trade():
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
        
    data = request.get_json()
    action = data.get('action') 
    amount = data.get('amount')
    price = data.get('price')
    
    print(f"🚨 Mini App Request: Attempting to {action} {amount} BTC at ${price}")
    
    return jsonify({
        "status": "success", 
        "message": f"Order to {action} placed successfully!"
    })

if __name__ == '__main__':
    # Grab the port Railway wants to use
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
