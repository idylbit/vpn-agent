import subprocess
import ipaddress
import re
from .peer import PeerManager


class WgInterface:
    def __init__(self, name: str, ip_address, port: int):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.public_key = None

    def validate(self):
        errors = {}

        name_errors = []
        if not self.name:
            name_errors.append("This field cannot be empty.")
        else:
            if len(self.name) > 15:
                name_errors.append("Ensure this field has no more than 15 characters.")
            if not re.match(r'^[a-zA-Z0-9_=+.-]+$', self.name):
                name_errors.append("May contain only a-z, 0-9, _, =, +, ., -.")

        if not name_errors:
            try:
                result = subprocess.run(
                    ["wg", "show", "interfaces"],
                    capture_output=True,
                    check=True,
                    text=True
                )
                if self.name in result.stdout.split("\n"):
                    name_errors.append("Interface with this name already exists.")
            except subprocess.CalledProcessError:
                errors.setdefault("system", []).append(
                    "Could not verify if name is available. Please try again."
                )
        
        if name_errors:
            errors["name"] = name_errors

        try:
            parsed_ipv4interface = ipaddress.IPv4Interface(self.ip_address)

            result = subprocess.run(
                ["ip", "-o", "addr", "show"],
                capture_output=True, text=True, check=True
            )
            
            if str(parsed_ipv4interface.ip) in result.stdout:
                for line in result.stdout.splitlines():
                    if (
                        str(parsed_ipv4interface.ip) in line and
                        self.name not in line
                    ):
                        errors.setdefault("ip_address", []).append(
                            f"IP address is already assigned to another interface."
                        )
                        break
        except (ipaddress.AddressValueError, ValueError):
            errors["ip_address"] = ["Invalid IPv4 address or subnet mask."]
        except subprocess.CalledProcessError:
            errors.setdefault("system", []).append(
                "Could not verify system IP assignments."
            )

        try:
            port_int = int(self.port)
            if not (1 <= port_int <= 65535):
                raise ValueError()
            result = subprocess.run(
                ["ss", "-uln"], 
                capture_output=True, text=True, check=True
            )
            if f":{port_int} " in result.stdout:
                errors.setdefault("port", []).append(
                    "This port is already in use by another service."
                )
        except (ValueError, TypeError):
            errors.setdefault("port", []).append(
                "Port must be an integer between 1 and 65535."
            )

        if errors:
            raise ValidationError(errors)

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
                ["wg", "genkey"],
                text=True
            ).strip()
            
        proc = subprocess.Popen(
            ["wg", "pubkey"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
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
                "wg", "set", self.name,
                "listen-port", str(self.port),
                "private-key", "/dev/stdin"
            ],
            input=private_key,
            check=True,
            text=True
        )

    def exists(self):
        try:
            result = subprocess.run(
                ["wg", "show", "interfaces"],
                capture_output=True,
                check=True,
                text=True
            )
            return self.name in result.stdout.split("\n")
        except subprocess.CalledProcessError:
            errors.setdefault("system", []).append(
                "Could not verify if name is available. Please try again."
            )

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


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors)

class WgInterfaceNotFound(Exception):
    pass
