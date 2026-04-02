from flask import Flask, request, jsonify
import wg_manager
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)


@app.route('/peers', method=['POST'])
def api_add_peer():
    data = request.json
    try:
        wg_manager.add_peer(
            INTERFACE_NAME,
            data["public_key"],
            data["allowed_ips"],
            data["endpoint"]
        )
        return 200


@app.route('/status', methods=['GET'])
def get_status():
    return jsonify({
        "interface": INTERFACE_NAME,
        "up": wg_manager.is_interface_up(INTERFACE_NAME),
        "active_handshakes": wg_manager.check_handshake(INTERFACE_NAME)
    })


if __name__ == "__main__":
    print("Running VPN Agent Initialization...")
    wg_manager.initialize_vpn_agent()
    
    print("Starting API Server...")
    app.run(host='0.0.0.0', port=5000)
