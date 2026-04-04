import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from api.routes import peers_bp
from interface.peer import ValidationError


class TestPeersAPI(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(
            peers_bp,
            url_prefix="/<interface_name>/peers"
        )
        self.client = self.app.test_client()

    def test_post_empty_data_returns_bad_request(self):
        response = self.client.post("/wg0/peers/", json={})
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            ["This field is required."],
            response.json["public_key"]
        )

    @patch("api.routes.peers.Peer")
    def test_post_invalid_data_returns_bad_request(self, MockPeer):
        mock_peer_instance = MockPeer.return_value
        mock_peer_instance.save.side_effect = ValidationError({
            "public_key": ["Invalid public key format."]
        })

        response = self.client.post("/wg0/peers/", json={
            "public_key": "invalid_key"
        })

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            ["Invalid public key format."],
            response.json["public_key"]
        )

    @patch("api.routes.peers.Peer")
    def test_post_valid_data_returns_created(self, MockPeer):
        mock_peer_instance = MockPeer.return_value
        data = {
            "public_key": "1WwjBZqEqMytJNq9WoxFwvZXxSGBK5gqyMv9gL7HcVY=",
            "allowed_ips": "10.200.0.5/32",
            "endpoint": "103.139.33.1:812",
            "preshared_key": "1WwjBZqEqMytJNq9WoxFwvZXxSGBK5gqyMv9gL7HcVY="
        }
        mock_peer_instance.public_key=data["public_key"]
        mock_peer_instance.allowed_ips=data["allowed_ips"]
        mock_peer_instance.endpoint=data["endpoint"]
        mock_peer_instance.preshared_key=data["preshared_key"]

        response = self.client.post("/wg0/peers/", json=data)

        self.assertEqual(201, response.status_code)
        for k, v in data.items():
            self.assertEqual(
                v,
                response.json[k]
            )
