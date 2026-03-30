import os
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)

# 🔓 This automatically handles all the complicated browser security checks!
CORS(app)

# 🏠 Basic load screen to prove it's online
@app.route('/')
def home():
    return "Liquid Leverage Backend is Running!"

# 🚨 Listens for clicks from the Mini App
@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.get_json()
    
    # Safely get the data coming in from GitHub
    action = data.get('action') if data else 'unknown'
    amount = data.get('amount') if data else '0'
    price = data.get('price') if data else '0'
    
    # This prints in your Railway logs to prove it's connected!
    print(f"🚨 Mini App Request: Attempting to {action} {amount} BTC at ${price}")
    
    return jsonify({
        "status": "success", 
        "message": f"Order to {action} placed successfully!"
    })

if __name__ == '__main__':
    # Grab the port Railway wants to use
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
