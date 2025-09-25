import os
import logging

from flask import Flask
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "supermarket_dashboard_secret")

# Enable CORS for Streamlit integration
CORS(app)

# Import routes after app creation to avoid circular imports
from flask_api.routes import *

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
