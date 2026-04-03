import os
import re
import ipaddress
import subprocess


class PeerManager:
    def __init__(self, interface):
        self.interface = interface

    def all(self):
        try:
            output = subprocess.check_output(
                ["wg", "show", self.interface.name, "dump"],
                text=True
            )
            lines = output.strip().split('\n')
            
            results = []
            for line in lines[1:]:
                parts = line.split('\t')
                results.append(Peer(
                    interface=self.interface,
                    public_key=parts[0],
                    preshared_key=parts[1],
                    endpoint=parts[2] if parts[2] != '(none)' else None,
                    allowed_ips=parts[3],
                    latest_handshake=int(parts[4]),
                    transfer_rx=int(parts[5]),
                    transfer_tx=int(parts[6])
                ))
            return results
        except (subprocess.CalledProcessError, IndexError):
            return []

    def filter(self, **kwargs):
        return [
            p for p in self.all() 
            if all(
                getattr(p, k, None) == v
                for k, v in kwargs.items()
            )
        ]
                
    def get(self, **kwargs):
        for p in self.all():
            if all(
                getattr(p, k, None) == v
                for k, v in kwargs.items()
            ):
                return p
        return None

    def create(self, **kwargs):
        peer = Peer(**kwargs)
        peer.save()

    def delete(self, **kwargs):
        peer = self.get(**kwargs)
        if not peer:
            raise PeerNotFound("Peer not found.")
        peer.delete()

    def get_next_available_ip(self):
        interface_ip_address = ipaddress.IPv4Interface(
            self.interface.ip_address
        )
        interface_network = interface_ip_address.network

        used_ips = {
            p.allowed_ips.split('/')[0]
            for p in self.all()
        }

        server_ip = str(interface_ip_address.ip)
        used_ips.add(server_ip)

        for ip in interface_network.hosts():
            if str(ip) not in used_ips:
                return f"{ip}/32"

        raise IPExhaustedError("No available IP addresses in the interface subnet.")


class Peer:
    def __init__(
        self,
        interface,
        public_key,
        endpoint=None,
        allowed_ips=None,
        preshared_key=None,
        **kwargs
    ):
        self.interface = interface
        self.public_key = public_key
        self.endpoint = endpoint
        self.allowed_ips = allowed_ips
        self.preshared_key = preshared_key

        self._latest_handshake = kwargs.get("latest_handshake", 0)
        self._transfer_rx = kwargs.get("transfer_rx", 0)
        self._transfer_tx = kwargs.get("transfer_tx", 0)
        self._persistent_keepalive = kwargs.get("persistent_keepalive", "off")

    def validate(self):
        errors = {}

        if not re.match(r'^[A-Za-z0-9+/]{42,43}=$', self.public_key):
            errors["public_key"] = ["Invalid public key format."]

        if self.allowed_ips:
            if not re.match(r'^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$', self.allowed_ips):
                errors["allowed_ips"] = ["Invalid ip address format. Expected format like 10.0.0.2/32."]

        if self.endpoint:
            if not re.match(
                r'^([a-zA-Z0-9.-]+|\d{1,3}(\.\d{1,3}){3}):\d{1,5}$',
                self.endpoint
            ):
                errors["endpoint"] = ["Invalid endpoint format. Expected 'host:port' or 'ip:port'."]

        if self.preshared_key:
            if not re.match(r'^[A-Za-z0-9+/]{42,43}=$', self.preshared_key):
                errors["preshared_key"] = ["Invalid preshared key format."]

        if not errors:
            for p in self.interface.peers.all():
                if p.public_key == self.public_key:
                    errors["public_key"] = ["Peer with this public key already exists."]
                    break
                if self.allowed_ips and p.allowed_ips == self.allowed_ips:
                    errors["allowed_ips"] = ["This ip address is already in use by another peer."]
                    break

        if errors:
            raise ValidationError(errors)

    def save(self):
        if not self.allowed_ips:
            self.allowed_ips = self.interface.peers.get_next_available_ip()
            
        self.validate()

        cmd = [
            "wg", "set", self.interface.name,
            "peer", self.public_key,
            "allowed-ips", self.allowed_ips
        ]

        if self.endpoint:
            cmd.extend(["endpoint", self.endpoint])

        if self.preshared_key:
            cmd.extend(["preshared-key", "/dev/stdin"])
            subprocess.run(cmd, input=self.preshared_key, text=True, check=True)
        else:
            subprocess.run(cmd, check=True)

    def delete(self):
        subprocess.run([
            "wg", "set", self.interface.name, 
            "peer", self.public_key, "remove"
        ], check=True)

    @property
    def latest_handshake(self):
        return self._latest_handshake

    @property
    def transfer_rx(self):
        return self._transfer_rx

    @property
    def transfer_tx(self):
        return self._transfer_tx


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors)

class PeerNotFound(Exception):
    pass

class IPExhaustedError(Exception):
    pass
