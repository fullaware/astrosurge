"""
Minimal Flask webapp for the AstroSurge walkthrough UI.
"""

import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    public_api_base_url = os.getenv("PUBLIC_API_BASE_URL", "").rstrip("/")
    public_api_port = os.getenv("API_PUBLIC_PORT", os.getenv("API_PORT", "8000"))
    return render_template(
        "dashboard.html",
        public_api_base_url=public_api_base_url,
        public_api_port=public_api_port,
    )


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=False, host="0.0.0.0", port=port)
