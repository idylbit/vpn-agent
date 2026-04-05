import subprocess
import json
from typing import TypedDict


class Interface(TypedDict):
    ifindex: int
    ifname: str
    flags: list[str]
    mtu: int
    qdisc: str
    operstate: str
    linkmode: str
    group: str
    txqlen: int
    link_type: str


class InterfacePeer(TypedDict):
    public_key: str
    preshared_key: str
    endpoint: str | None
    allowed_ips: str
    latest_handshake: int
    transfer_rx: int
    transfer_tx: int


class WgExecutor:
    SUDO_WHITELIST = [
        "/usr/sbin/ip link add * type wireguard",
        "/usr/sbin/ip addr add * dev *",
        "/usr/bin/wg set * listen-port * private-key * /dev/stdin",
        "/usr/sbin/ip link set * up",
        "/usr/sbin/ip link set * down",
        "/usr/sbin/ip link delete *",
        "/usr/sbin/wg show * dump",
        "/usr/bin/wg set * peer * remove *",
        "/usr/bin/wg set * peer * allowed-ips *"
    ]

    @classmethod
    def _run(cls, cmd: list, **kwargs) -> str:
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                check=True, 
                **kwargs
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"OS Error: {e.stderr}")
            raise

    @classmethod
    def _sudo_run(cls, cmd: list, **kwargs) -> str:
        return cls._run(["sudo"]+cmd, **kwargs)

    @classmethod
    def get_private_key(cls) -> str:
        return cls._run(["wg", "genkey"]).strip()

    @classmethod
    def get_public_key(cls, private_key: str) -> str:
        return cls._run(
            ["wg", "pubkey"],
            input=private_key
        ).strip()

    @classmethod
    def create_link(cls, name: str):
        cls._sudo_run([
            "ip", "link", "add", name,
            "type", "wireguard"
        ])

    @classmethod
    def delete_link(cls, name: str):
        cls._sudo_run(["ip", "link", "delete", name])

    @classmethod
    def set_ip(cls, name: str, ip_address: str):
        cls._sudo_run([
            "ip", "addr", "add", ip_address,
            "dev", name
        ])

    @classmethod
    def apply_config(cls, name: str, port: int, private_key: str):
        cls._sudo_run(
            [
                "wg", "set", name,
                "listen-port", str(port),
                "private-key", "/dev/stdin"
            ],
            input=private_key
        )

    @classmethod
    def bring_up(cls, name: str):
        cls._sudo_run(["ip", "link", "up", name])

    @classmethod
    def bring_down(cls, name: str):
        cls._sudo_run(["ip", "link", "down", name])

    @classmethod
    def init_interface(
        cls,
        name: str,
        ip_address: str,
        port: str,
        private_key: str | None=None
    ):
        try:
            if not private_key:
                private_key = cls.get_private_key()
            cls.create_link(name)
            cls.set_ip(name, ip_address)
            cls.apply_config(name, port, private_key)
            cls.bring_up(name)
            return cls.get_public_key(private_key)
        except Exception:
            cls.delete_link(name)
            raise

    @classmethod
    def get_interfaces(cls) -> list[Interface]:
        result = cls._run(["ip", "-j", "link", "show", "type", "wireguard"])
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return []

    @classmethod
    def get_interface_names(cls) ->list[str]:
        interfaces = cls.get_interfaces()
        return [interface["ifname"] for interface in interfaces]

    @classmethod
    def get_active_interfaces(cls) -> list[str]:
        interfaces = cls.get_interfaces()
        return [
            iface["ifname"] for iface in interfaces 
            if "UP" in iface["flags"]
        ]
    
    @classmethod
    def is_ip_taken(cls, ip_address: str) -> bool:
        results = cls._run(["ip", "-o", "addr", "show"])
        return ip_address in results

    @classmethod
    def is_port_taken(cls, port: int) -> bool:
        result = cls._run(["ss", "-uln"])
        return f":{port} " in result

    @classmethod
    def get_interface_peers(cls, name) -> list[InterfacePeer]:
        results = cls._sudo_run(["wg", "show", name, "dump"])
        try:
            lines = results.strip().split('\n')
            results = []
            for line in lines[1:]:
                parts = line.split('\t')
                results.append(
                    InterfacePeer(
                        public_key=parts[0],
                        preshared_key=parts[1],
                        endpoint=parts[2] if parts[2] != '(none)' else None,
                        allowed_ips=parts[3],
                        latest_handshake=int(parts[4]),
                        transfer_rx=int(parts[5]),
                        transfer_tx=int(parts[6])
                    )
                )
            return results
        except IndexError:
            return []

    @classmethod
    def add_interface_peer(
        cls,
        name: str,
        public_key: str,
        allowed_ips: str,
        endpoint: str | None = None,
        preshared_key: str | None = None
    ):
        cmd = [
            "wg", "set", name,
            "peer", public_key,
            "allowed-ips", allowed_ips
        ]
        if endpoint:
            cmd.extend(["endpoint", endpoint])
        if preshared_key:
            cmd.extend(["preshared-key", "/dev/stdin"])
            cls._sudo_run(cmd, input=preshared_key)
        else:
            cls._sudo_run(cmd)

    @classmethod
    def remove_interface_peer(cls, name: str, public_key: str):
        cls._sudo_run([
            "wg", "set", name, 
            "peer", public_key, "remove"
        ])
