import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# This allows your GitHub website to send requests to this Railway server
CORS(app)

@app.route('/')
def home():
    return "Liquid Leverage Backend is Running!"

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.get_json()
    action = data.get('action', 'unknown')
    amount = data.get('amount', '0')
    price = data.get('price', '0')
    
    print(f"🚨 Mini App Request: Attempting to {action} {amount} BTC at ${price}")
    
    return jsonify({
        "status": "success", 
        "message": f"Order to {action} placed successfully!"
    })

if __name__ == '__main__':
    # This falls back to 5000 if run locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
