import unittest
from unittest.mock import patch, MagicMock
from peer import Peer


class TestPeerModel(unittest.TestCase):
    def setUp(self):
        self.valid_payload = {
            "public_key": "abc123DEF456ghi789JKL012mno345PQR678stu901=",
            "allowed_ips": "10.200.0.5/32",
            "endpoint": "1.2.3.4:51820"
        }

    @patch("wg_manager.peer_exists")
    @patch("wg_manager.is_ip_taken")
    @patch("wg_manager.is_key_self")
    def test_successful_validation(
        self,
        mock_self_key,
        mock_ip_taken,
        mock_exists
    ):
        mock_exists.return_value = False
        mock_ip_taken.return_value = False
        mock_self_key.return_value = False

        peer = Peer(self.valid_payload)
        peer.validate()

        self.assertTrue(peer.is_valid)
        self.assertEqual(peer.public_key, self.valid_payload["public_key"])
        self.assertEqual(len(peer.validation_errors), 0)


if __name__ == '__main__':
    unittest.main()
