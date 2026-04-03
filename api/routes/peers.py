from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from interface.peer import Peer
from interface.wg import WgInterface


load_dotenv()

peers_bp = Blueprint("peers", __name__)

INTERFACE_NAME=os.getenv("INTERFACE_NAME")
INTERFACE_IP_ADDRESS=os.getenv("INTERFACE_IP_ADDRESS")
INTERFACE_PORT=os.getenv("INTERFACE_PORT", 51820)


@peers_bp.route(
    '',
    methods=['POST']
)
def create_peer():
    data = request.json

    errors = {}
    for k in [
        "public_key"
    ]:
        if k not in data:
            errors[k] = ["This field is required."]

    if errors:
        return jsonify(errors), 400

    try:
        interface = WgInterface(
            name=INTERFACE_NAME,
            ip_address=INTERFACE_IP_ADDRESS,
            port=INTERFACE_PORT
        )
        peer = Peer(
            interface=interface,
            public_key=data["public_key"],
            endpoint=data.get("endpoint", None),
            allowed_ips=data.get("allowed_ips", None),
            preshared_key=data.get("preshared_key", None)
        )
        peer.validate()
        peer.save()
        return jsonify({
            "public_key": peer.public_key,
            "endpoint": peer.endpoint,
            "allowed_ips": peer.allowed_ips,
            "preshared_key": peer.preshared_key
        }), 201
    except ValidationError as e:
        return jsonify(e), 400
    except Exception:
        return jsonify({"detail": "Something went wrong."}), 500


@peers_bp.route(
    '',
    methods=['GET']
)
def list_peers():
    try:
        interface = WgInterface(
            name=INTERFACE_NAME,
            ip_address=INTERFACE_IP_ADDRESS,
            port=INTERFACE_PORT
        )
        peers = interface.peers.all()
        return jsonify({
            "results": peers,
            "count": len(peers)
        }), 200
    except Exception:
        return jsonify({"detail": "Something went wrong."}), 500
