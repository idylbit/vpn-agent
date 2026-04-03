from flask import Blueprint, request, jsonify
from dotenv import load_dotenv


load_dotenv()

peers_bp = Blueprint("peers", __name__)


@peers_bp.route(
    '/peers',
    methods=['POST']
)
def create_peer():
    peer = Peer(request.json)
    peer.validate()
    if not peer.is_valid:
        return jsonify(peer.validation_errors), 400
    peer.save()
    return jsonify(peer.data), 201


@peers_bp.route(
    '/status',
    methods=['GET']
)
def get_status():
    iface = os.getenv("INTERFACE_NAME")
    return jsonify({
        "interface": iface,
        "up": wg_manager.is_interface_up(iface),
        "active_handshakes": wg_manager.check_handshake(iface)
    })
