from flask import Flask
from .routes.peers import peers_bp


app = Flask(__name__)

app.register_blueprint(peers_bp, url_prefix="/peers")
