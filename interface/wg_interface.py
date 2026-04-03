import subprocess
from .peer import PeerManager


class WgInterface:
    def __init__(self, name: str, ip_address, port: int):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.public_key = None

    def is_up(self):
        try:
            result = subprocess.run(
                ["ip", "link", "show", self.name],
                capture_output=True,
                check=True,
                text=True
            )
            return "UP" in result.stdout
        except subprocess.CalledProcessError:
            return False

    def check_handshake(self):
        try:
            output = subprocess.check_output(
                ["wg", "show", self.name, "latest-handshakes"],
                text=True
            )
            return (
                any(
                    line.split()[1] != '0'
                    for line in output.strip().split('\n')
                )
            )
        except Exception:
            return False

    def validate(self):
        result = subprocess.run(
            ["wg", "show", "interfaces"],
            capture_output=True,
            check=True,
            text=True
        )
        if self.name in result.stdout.split("\n"):
            raise ValidationError("Interface already exists.")

    def save(self, private_key=None):
        self.validate()

        subprocess.run(
            [
                "ip", "link", "add", f"{self.name}",
                "type", "wireguard"
            ],
            check=True
        )

        if not private_key:
            private_key = subprocess.check_output(
                ["wg", "genkey"]
            ).decode().strip()
            
        proc = subprocess.Popen(
            ["wg", "pubkey"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            check=True
        )
        pub_key, _ = proc.communicate(input=private_key)
        self.public_key = pub_key.strip()

        subprocess.run(
            [
                "ip", "addr", "add", self.ip_address,
                "dev", self.name
            ],
            check=True
        )
        subprocess.run(
            [
                "wg", "set", name,
                "listen-port", str(port),
                "private-key", "/dev/stdin"
            ],
            input=private_key,
            check=True,
            text=True
        )

    def bring_up(self):
        subprocess.run(
            ["ip", "link", "set", self.name, "up"],
            check=True
        )

    def bring_down(self):
        subprocess.run(
            ["ip", "link", "set", name, "down"],
            check=True
        )

    def delete(self):
        subprocess.run(
            ["ip", "link", "delete", "dev", self.name],
            check=True
        )

    @property
    def peers(self):
        return PeerManager(self)
