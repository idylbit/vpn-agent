import os
import re
import wg_manager


class PeerManager:
    def __init__(self, interface):
        self.interface = interface

    def all(self):
        try:
            output = subprocess.check_output(
                ["wg", "show", self.name, "dump"],
                text=True
            )
            lines = output.strip().split('\n')
            
            results = []
            for line in lines[:1]:
                parts = line.split('\t')
                results.append(Peer(
                    interface=self,
                    public_key=parts[0],
                    allowed_ips=parts[3],
                    endpoint=parts[2] if parts[2] != '(none)' else None,
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
            raise ValueError("Peer not found.")
        peer.delete()


class Peer:
    def __init__(
        self,
        interface,
        public_key,
        allowed_ips,
        endpoint=None,
        **kwargs
    ):
        self.interface = interface
        self.public_key = public_key
        self.allowed_ips = allowed_ips
        self.endpoint = endpoint

        self._latest_handshake = kwargs.get("latest_handshake", 0)
        self._transfer_rx = kwargs.get("transfer_rx", 0)
        self._transfer_tx = kwargs.get("transfer_tx", 0)
        self._persistent_keepalive = kwargs.get("persistent_keepalive", "off")

    @property
    def latest_handshake(self):
        return self._latest_handshake

    @property
    def transfer_rx(self):
        return self._transfer_rx

    @property
    def transfer_tx(self):
        return self._transfer_tx

    def validate(self):
        errors = {}

        if not re.match(r'^[A-Za-z0-9+/]{42,43}=$', self.public_key):
            errors[k] = ["Invalid public key format."]

        if not re.match(r'^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$', self.allowed_ips):
            errors[k] = ["Invalid ip address format. (e.g., 10.0.0.2/32)."]

        if self.endpoint:
            if not re.match(
                r'^([a-zA-Z0-9.-]+|\d{1,3}(\.\d{1,3}){3}):\d{1,5}$',
                endpoint
            ):
                errors[k] = ["Invalid endpoint format. Expected 'host:port' or 'ip:port'."]

        if not errors:
            for p in self.interface.peers.all():
                if p.public_key == self.public_key:
                    error["public_key"] = ["Peer with this public key already exists."]
                    break
                elif p.allowed_ips == self.allowed_ips:
                    error["ip_address"] = ["This ip address is already in use by another peer."]
                    break

        if errors:
            raise ValueError(errors)

    def save(self):
        self.validate()
        cmd = [
            "wg", "set", self.interface.name,
            "peer", self.public_key,
            "allowed-ips", self.allowed_ips
        ]
        if self.endpoint:
            cmd.extend(["endpoint", self.endpoint])
        subprocess.run(cmd, check=True)

    def delete(self):
        subprocess.run([
            "wg", "set", self.interface.name, 
            "peer", self.public_key, "remove"
        ], check=True)
