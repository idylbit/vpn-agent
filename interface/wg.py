import ipaddress
import re
from .peer import PeerManager
from .executor import WgExecutor


class WgInterfaceManager:
    def all(self) -> list[WgInterface]:
        interfaces = WgExecutor.get_interfaces()
        return [
            WgInterface(**interface)
            for interface in interfaces
        ]

    def get(self, **kwargs) -> WgInterface:
        interfaces = [
            interface
            for interface in self.all()
            if all(
                getattr(p, k, None) == v
                for k, v in kwargs.items()
            )
        ]
        if len(interfaces) > 1:
            raise ManyWgInterfacesFound("More than one interfaces found.")
        elif len(interfaces) == 1:
            return interfaces[0]
        raise WgInterfaceDoesNotExist("Interface not found.")

    def create(self, **kwargs) -> WgInterface:
        wg_interface = WgInterface(**kwargs)
        wg_interface.save()
        return WgInterface

    def delete(self, **kwargs):
        wg_interface = self.get(**kwargs)
        wg_interface.delete()


class WgInterface:
    def __init__(
        self,
        name: str,
        ip_address: str,
        port: int,
        **kwargs
    ):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.public_key = None

        self.ifindex = kwargs.get("ifindex", None)
        self.operstate = kwargs.get("operstate", "UNKNOWN")
        self.mtu = kwargs.get("mtu", 1420)
        self.flags = kwargs.get("flags", [])

    def validate(self):
        errors = {}

        name_errors = []
        if not self.name:
            name_errors.append("This field cannot be empty.")
        else:
            if len(self.name) > 15:
                name_errors.append(
                    "Ensure this field has no more than 15 characters."
                )
            if not re.match(r'^[a-zA-Z0-9_=+.-]+$', self.name):
                name_errors.append(
                    "May contain only a-z, 0-9, _, =, +, ., -."
                )

        if not name_errors:
            if self.name in WgExecutor.get_interface_names():
                name_errors.append("Interface with this name already exists.")
        
        if name_errors:
            errors["name"] = name_errors

        try:
            parsed_ipv4interface = ipaddress.IPv4Interface(self.ip_address)
            if WgExecutor.is_ip_taken(str(parsed_ipv4interface.ip)):
                errors.setdefault("ip_address", []).append(
                    f"IP address is already assigned to another interface."
                )
        except (ipaddress.AddressValueError, ValueError):
            errors["ip_address"] = ["Invalid IPv4 address or subnet mask."]

        try:
            port_int = int(self.port)
            if not (1 <= port_int <= 65535):
                raise ValueError()
            if WgExecutor.is_port_taken(port_int):
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
        WgExecutor.init_interface(
            name=self.name,
            ip_address=self.ip_address,
            port=self.port,
            private_key=private_key
        )

    def bring_up(self):
        WgExecutor.bring_up(self.name)

    def bring_down(self):
        WgExecutor.bring_down(self.name)

    def delete(self):
        WgExecutor.delete(self.name)

    @property
    def peers(self):
        return PeerManager(self)

    @property
    def is_active(self) -> bool:
        return "UP" in self.flags


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors)


class WgInterfaceDoesNotExist(Exception):
    pass


class ManyWgInterfacesFound(Exception):
    pass
