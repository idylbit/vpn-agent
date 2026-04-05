import os
import re
import ipaddress
from .executor import WgExecutor


class PeerManager:
    def __init__(self, interface):
        self.interface = interface

    def all(self) -> list[Peer]:
        results = WgExecutor.get_interface_peers(
            self.interface.name
        )
        return [
            Peer(
                interface=self.interface,
                **interface_peer
            )
            for interface_peer in results
        ]

    def get(self, **kwargs) -> Peer:
        peers = [
            peer
            for peer in self.all()
            if all(
                getattr(peer, k, None) == v
                for k, v in kwargs.items()
            )
        ]
        if len(peers) > 1:
            raise ManyPeersFound("More than one peer found.")
        elif len(peers) == 1:
            return peers[0]
        raise PeerDoesNotExist("Peer not found.")

    def create(self, **kwargs) -> Peer:
        peer = Peer(**kwargs)
        peer.save()
        return peer

    def delete(self, **kwargs):
        peer = self.get(**kwargs)
        peer.delete()

    def get_next_available_allowed_ip(self):
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

        raise IPExhausted(
            "No available IP addresses in the interface subnet."
        )


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
            if not re.match(
                r'^\d{1,3}(\.\d{1,3}){3}/\d{1,2}$',
                self.allowed_ips
            ):
                errors["allowed_ips"] = ["Invalid ip address format. Expected format like 10.0.0.2/32."]

        if self.endpoint:
            if not re.match(
                r'^([a-zA-Z0-9.-]+|\d{1,3}(\.\d{1,3}){3}):\d{1,5}$',
                self.endpoint
            ):
                errors["endpoint"] = ["Invalid endpoint format. Expected 'host:port' or 'ip:port'."]

        if self.preshared_key:
            if not re.match(
                r'^[A-Za-z0-9+/]{42,43}=$',
                self.preshared_key
            ):
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
            self.allowed_ips = self.interface.peers.get_next_available_allowed_ip()
            
        self.validate()
        WgExecutor.add_interface_peer(
            self.interface.name,
            self.public_key,
            self.allowed_ips,
            self.endpoint,
            self.preshared_key
        )

    def delete(self):
        WgExecutor.remove_interface_peer(
            self.interface.name,
            self.public_key
        )

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


class PeerDoesNotExist(Exception):
    pass


class IPExhausted(Exception):
    pass


class ManyPeersFound(Exception):
    pass
