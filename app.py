import os
from flask import Flask, render_template

app = Flask(__name__)

# This tells Flask to show your index.html file when someone opens the link
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # Railway gives us a random port to use, we have to listen to it!
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
