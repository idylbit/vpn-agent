import unittest
from unittest.mock import patch, MagicMock
from interface.wg import WgInterface, ValidationError
from faker import Faker


faker = Faker()


class TestWgInterface(unittest.TestCase):
    def setUp(self):
        self.taken_name = "wg0"
        self.taken_ip_address = "10.200.0.1/24"
        self.taken_port = "323"

    def subprocess_run_side_effect(self, cmd, **kwargs):
        if cmd == ["wg", "show", "interfaces"]:
            return MagicMock(args=cmd, stdout=f"{self.taken_name}\n", returncode=0)
        if cmd == ["ip", "-o", "addr", "show"]:
            return MagicMock(args=cmd, returncode=0, stdout=f'1: lo    inet 27.0.0.1/8 scope host lo\\       valid_lft forever preferred_lft forever\n1: lo    inet6::1/128 scope host noprefixroute \\       valid_lft forever preferred_lft forever\n2: enp0s3    inet 10.0.2.15/24 metric 100 brd 10.0.2.255 scope global dynamic enp0s3\\       valid_lft 81642sec preferred_lft 81642sec\n2: enp0s3    inet6 fd17:625c:f037:2:a00:27ff:feff:b56a/64 scope global dynamic mngtmpaddr noprefixroute \\       valid_lft 86300sec preferred_lft 14300sec\n2: enp0s3    inet6 fe80::a00:27ff:feff:b56a/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n3: enp0s8    inet 192.168.56.101/24 metric 100 brd 192.168.56.255 scope global dynamic enp0s8\\       valid_lft 344sec preferred_lft 344sec\n3: enp0s8    inet6 fe80::a00:27ff:fe17:6052/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n4: docker0    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0\\       valid_lft forever preferred_lft forever\n4: docker0    inet6 fe80::3404:e0ff:fe3e:f0e8/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n5: br-9957c95d6098    inet 172.18.0.1/16 brd 172.18.255.255 scope global br-9957c95d6098\\       valid_lft forever preferred_lft forever\n5: br-9957c95d6098    inet6 fe80::c84e:ceff:feb6:b973/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n6: veth72fdd7d    inet6 fe80::1455:96ff:fe85:9b47/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n8: veth4030f6f    inet6 fe80::180c:56ff:fe0e:e556/64 scope link proto kernel_ll \\       valid_lft forever preferred_lft forever\n1219: {self.taken_name}    inet {self.taken_ip_address} scope global {self.taken_name}\\       valid_lft forever preferred_lft forever\n', stderr='')
        if cmd == ["ss", "-uln"]:
            return MagicMock(args=cmd, returncode=0, stdout=f'State  Recv-Q Send-Q                               Local Address:Port  Peer Address:Port \nUNCONN 0      0                                       10.200.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                       10.200.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                   192.168.56.101:53         0.0.0.0:*    \nUNCONN 0      0                                   192.168.56.101:53         0.0.0.0:*    \nUNCONN 0      0                                        10.0.2.15:53         0.0.0.0:*    \nUNCONN 0      0                                        10.0.2.15:53         0.0.0.0:*    \nUNCONN 0      0                                       172.18.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                       172.18.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                       172.17.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                       172.17.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                        127.0.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                        127.0.0.1:53         0.0.0.0:*    \nUNCONN 0      0                                       127.0.0.54:53         0.0.0.0:*    \nUNCONN 0      0                                    127.0.0.53%lo:53         0.0.0.0:*    \nUNCONN 0      0                            192.168.56.101%enp0s8:68         0.0.0.0:*    \nUNCONN 0      0                                 10.0.2.15%enp0s3:68         0.0.0.0:*    \nUNCONN 0      0                                        127.0.0.1:{self.taken_port}        0.0.0.0:*    \nUNCONN 0      0                                            [::1]:53            [::]:*    \nUNCONN 0      0                                            [::1]:53            [::]:*    \nUNCONN 0      0                [fe80::a00:27ff:feff:b56a]%enp0s3:53            [::]:*    \nUNCONN 0      0                [fe80::a00:27ff:feff:b56a]%enp0s3:53            [::]:*    \nUNCONN 0      0                [fe80::a00:27ff:fe17:6052]%enp0s8:53            [::]:*    \nUNCONN 0      0                [fe80::a00:27ff:fe17:6052]%enp0s8:53            [::]:*    \nUNCONN 0      0              [fe80::3404:e0ff:fe3e:f0e8]%docker0:53            [::]:*    \nUNCONN 0      0              [fe80::3404:e0ff:fe3e:f0e8]%docker0:53            [::]:*    \nUNCONN 0      0      [fe80::c84e:ceff:feb6:b973]%br-9957c95d6098:53            [::]:*    \nUNCONN 0      0      [fe80::c84e:ceff:feb6:b973]%br-9957c95d6098:53            [::]:*    \nUNCONN 0      0          [fe80::1455:96ff:fe85:9b47]%veth72fdd7d:53            [::]:*    \nUNCONN 0      0          [fe80::1455:96ff:fe85:9b47]%veth72fdd7d:53            [::]:*    \nUNCONN 0      0          [fe80::180c:56ff:fe0e:e556]%veth4030f6f:53            [::]:*    \nUNCONN 0      0          [fe80::180c:56ff:fe0e:e556]%veth4030f6f:53            [::]:*    \n', stderr='')
        if (
            len(cmd) == 6 and
            cmd[0] == "ip" and cmd[1] == "link" and
            cmd[2] == "add" and cmd[4] == "type" and
            cmd[5] == "wireguard"
        ):
            return MagicMock(args=cmd, returncode=0)
        if (
            len(cmd) == 6 and
            cmd[0] == "ip" and cmd[1] == "addr" and
            cmd[2] == "add" and cmd[4] == "dev"
        ):
            return MagicMock(args=cmd, returncode=0)
        if (
            len(cmd) == 7 and
            cmd[0] == "wg" and cmd[1] == "set" and
            cmd[3] == "private-key" and cmd[4] == "/dev/stdin"
        ):
            return MagicMock(args=cmd, returncode=0)

    def subprocess_check_output_side_effect(self, cmd, **kwargs):
        if cmd == ["wg", "genkey"]:
            return "MLsY6DL/VZxZ++EcqVT9j7+roOk2RAd5mB/Uiv0Gfkc="

    def subprocess_popen_side_effect(self, cmd, **kwargs):
        if cmd == ["wg", "pubkey"]:
            moc_proc = MagicMock()
            moc_proc.communicate.return_value = (
                "BvwalLMQTWDkBxhNMKLGyhYT5S/+FaVHT54lBOSNbnc=\n",
                None
            )
            moc_proc.returncode = 0
            return moc_proc

    @patch("subprocess.run")
    def test_invalid_data_fails_validation(self, subprocess_run):
        cases = [
            (
                {
                    "name": "",
                    "ip_address": "invalid-ip",
                    "port": "invalid-type"
                },
                {
                    "name": ["This field cannot be empty."],
                    "ip_address": ["Invalid IPv4 address or subnet mask."],
                    "port": ["Port must be an integer between 1 and 65535."]
                }
            ),
            (
                {
                    "name": faker.pystr(min_chars=16, max_chars=16),
                    "ip_address": self.taken_ip_address,
                    "port": "0"
                },
                {
                    "name": ["Ensure this field has no more than 15 characters."],
                    "ip_address": ["IP address is already assigned to another interface."],
                    "port": ["Port must be an integer between 1 and 65535."]
                }
            ),
            (
                {
                    "name": "In@||2n1d . )sr",
                    "ip_address": "10.29.30.1/24",
                    "port": "70000"
                },
                {
                    "name": ["May contain only a-z, 0-9, _, =, +, ., -."],
                    "port": ["Port must be an integer between 1 and 65535."]
                }
            ),
            (
                {
                    "name": self.taken_name,
                    "ip_address": "10.29.30.1/24",
                    "port": self.taken_port
                },
                {
                    "name": ["Interface with this name already exists."],
                    "port": ["This port is already in use by another service."]
                }
            )
        ]

        subprocess_run.side_effect = self.subprocess_run_side_effect
        for case, errors in cases:
            with self.subTest(case=case):
                interface = WgInterface(**case)
                with self.assertRaises(ValidationError) as cm:
                    interface.validate()
                self.assertEqual(errors, cm.exception.args[0])

    @patch("subprocess.Popen")
    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_valid_data_cases_validate_and_save(
        self,
        subprocess_run,
        subprocess_check_output,
        subprocess_popen
    ):
        cases = [
            {
                "name": faker.pystr(max_chars=15),
                "ip_address": "10.29.30.1",
                "port": 7488
            },
            {
                "name": faker.pystr(max_chars=10),
                "ip_address": "10.29.31.1/24",
                "port": "8000"
            }
        ]

        subprocess_run.side_effect = self.subprocess_run_side_effect
        subprocess_check_output.side_effect = self.subprocess_check_output_side_effect
        subprocess_popen.side_effect = self.subprocess_popen_side_effect
        for case in cases:
            with self.subTest(case=case):
                interface = WgInterface(**case)
                interface.save()
                self.assertIsNotNone(interface.public_key)

        interface = WgInterface(
            name=faker.pystr(max_chars=7),
            ip_address="198.156.33.1/24",
            port=51820
        )
        interface.save("gNNBxgDB/1E48F/UK9PiKcXoPIWR9/13Is6tJcxrUn4=")
        self.assertIsNotNone(interface.public_key)


if __name__ == '__main__':
    unittest.main()
