import os
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

# 🔓 This allows your GitHub Pages Mini App to talk to your Railway server!
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 🏠 Basic load screen
@app.route('/')
def home():
    return "Liquid Leverage Backend is Running!"

# 🚨 This is the "endpoint" that listens for clicks from the Mini App
@app.route('/api/trade', methods=['POST', 'OPTIONS'])
def execute_trade():
    # Handle the browser's security check (pre-flight)
    if request.method == 'OPTIONS':
        return jsonify({"status": "ok"})
        
    data = request.get_json()
    action = data.get('action') # "buy" or "sell"
    amount = data.get('amount')
    price = data.get('price')
    
    # 📝 This prints in your Railway logs to prove it's connected!
    print(f"🚨 Mini App Request: Attempting to {action} {amount} BTC at ${price}")
    
    # Send a success message back to the Mini App screen
    return jsonify({
        "status": "success", 
        "message": f"Order to {action} placed successfully!"
    })

if __name__ == '__main__':
    # This automatically starts your bot.py file in the background!
    subprocess.Popen(["python", "bot.py"])
    
    # This grabs the port Railway wants to use
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
