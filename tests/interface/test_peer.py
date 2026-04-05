import unittest
from unittest.mock import patch, MagicMock
from interface.peer import Peer, PeerDoesNotExist, ValidationError
from interface.wg import WgInterface


class TestPeer(unittest.TestCase):
    def setUp(self):
        self.taken_public_key = "1WwjBZqEqMytJNq9WoxFwvZXxSGBK5gqyMv9gL7HcVY="
        self.taken_allowed_ips = "10.200.0.5/32"
        self.new_public_key = "luScmBj4B5+Dz0x4VQWAKSaYLCvDNC9A9J0szbfUejQ="
        self.interface = WgInterface(
            name="wg0",
            ip_address="10.200.0.1/24",
            port="3949"
        )

    def wg_executor_sudo_run_side_effect(self, cmd, **kwargs):
        if (
            len(cmd) == 7 and
            cmd[0] == "wg" and cmd[1] == "set" and
            cmd[3] == "peer" and cmd[5] == "allowed-ips"
        ):
            return None
        elif (
            len(cmd) == 4 and
            cmd[0] == "wg" and cmd[1] == "show" and
            cmd[3] == "dump"
        ):
            return f'eInCyoU8GpGk7ZzkHYNo/uV0CJKKTYXElElc0qsHyn8=\tiRZw/KhsKYIlP/HEfyPtebkEdsHLxuRhb5BRHyWmkSM=\t51820\toff\n{self.taken_public_key}\t(none)\t(none)\t{self.taken_allowed_ips}\t0\t0\t0\toff\n'
        elif (
            len(cmd) == 6 and
            cmd[0] == "wg" and cmd[1] == "set" and
            cmd[3] == "peer" and cmd[4] == self.taken_public_key and
            cmd[5] == "remove"
        ):
            return None
        elif (
            len(cmd) == 6 and
            cmd[0] == "wg" and cmd[1] == "set" and
            cmd[3] == "peer" and cmd[4] == self.taken_public_key and
            cmd[5] == "remove"
        ):
            raise PeerDoesNotExist("Peer not found.")

    @patch("interface.executor.WgExecutor._sudo_run")
    def test_invalid_data_fails_validation(self, wg_executor_sudo_run):
        cases = [
            (
                {
                    "public_key": "Incvalid public key",
                    "endpoint": "2ſ#&%'invalid-type",
                    "allowed_ips": "invalid-ip",
                    "preshared_key": "Incvalid preshared key"
                },
                {
                    "public_key": ["Invalid public key format."],
                    "endpoint": ["Invalid endpoint format. Expected 'host:port' or 'ip:port'."],
                    "allowed_ips": ["Invalid ip address format. Expected format like 10.0.0.2/32."],
                    "preshared_key": ["Invalid preshared key format."]
                }
            ),
            (
                {
                    "public_key": self.taken_public_key
                },
                {
                    "public_key": ["Peer with this public key already exists."]
                }
            ),
            (
                {
                    "public_key": self.new_public_key,
                    "allowed_ips": self.taken_allowed_ips
                },
                {
                    "allowed_ips": ["This ip address is already in use by another peer."]
                }
            )
        ]

        wg_executor_sudo_run.side_effect = self.wg_executor_sudo_run_side_effect
        for case, errors in cases:
            with self.subTest(case=case):
                peer = Peer(self.interface, **case)
                with self.assertRaises(ValidationError) as cm:
                    peer.validate()
                self.assertEqual(
                    errors,
                    cm.exception.args[0]
                )

    @patch("interface.executor.WgExecutor._sudo_run")
    def test_valid_data_cases_validate_and_save(self, wg_executor_sudo_run):
        cases = [
            {
                "public_key": self.new_public_key,
                "endpoint": "103.139.33.1:32984",
                "allowed_ips": "10.29.30.1/32",
                "preshared_key": self.new_public_key
            },
            {
                "public_key": self.new_public_key,
                "allowed_ips": "10.29.30.1/32",
                "preshared_key": self.new_public_key
            },
            {
                "public_key": self.new_public_key,
                "preshared_key": self.new_public_key
            },
            {
                "public_key": self.new_public_key
            }
        ]

        wg_executor_sudo_run.side_effect = self.wg_executor_sudo_run_side_effect
        for case in cases:
            with self.subTest(case=case):
                peer = Peer(self.interface, **case)
                peer.save()
                self.assertIsNotNone(peer.allowed_ips)

    @patch("interface.executor.WgExecutor._sudo_run")
    def test_remove_non_existing_peer_throws_an_error(self, wg_executor_sudo_run):
        wg_executor_sudo_run.side_effect = self.wg_executor_sudo_run_side_effect
        with self.assertRaises(PeerDoesNotExist):
            self.interface.peers.delete(public_key=self.new_public_key)

    @patch("interface.executor.WgExecutor._sudo_run")
    def test_remove_existing_peer_deletes_it(self, wg_executor_sudo_run):
        wg_executor_sudo_run.side_effect = self.wg_executor_sudo_run_side_effect
        self.interface.peers.delete(public_key=self.taken_public_key)


if __name__ == '__main__':
    unittest.main()
