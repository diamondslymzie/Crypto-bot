import subprocess
import os
from flask import Flask, render_template

app = Flask(__name__)

# This tells Flask to show your index.html file when someone opens the link
@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    # This starts your bot.py in the background automatically!
    subprocess.Popen(["python", "bot.py"])
    
    # This starts your website on the port Railway wants
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

