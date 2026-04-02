import subprocess
from dotenv import load_dotenv


load_dotenv()

INTERFACE_NAME=os.getenv("INTERFACE_NAME")
INTERFACE_IP_ADDRESS=os.getenv("INTERFACE_IP_ADDRESS")
INTERFACE_PORT=os.getenv("INTERFACE_PORT", 51820)


def is_interface_present(name):
    result = subprocess.run(
        ["wg", "show", "interfaces"],
        capture_output=True,
        check=True,
        text=True
    )
    return name in result.stdout.split("\n")


def is_interface_up(name):
    try:
        result = subprocess.run(
            ["ip", "link", "show", name],
            capture_output=True,
            check=True,
            text=True
        )
        return "UP" in result.stdout
    except subprocess.CalledProcessError:
        return False


def check_handshake(iface_name="idylwg"):
    try:
        output = subprocess.check_output(
            ["wg", "show", iface_name, "latest-handshakes"],
            text=True
        )
        return (
            any(line.split()[1] != '0'
            for line in output.strip().split('\n')
        )
    except Exception:
        return False


def generate_keys():
    privkey = subprocess.check_output(
        ["wg", "genkey"]
    ).decode("utf-8").strip()
    
    process = subprocess.Popen(
        ["wg", "pubkey"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    pubkey, _ = process.communicate(input=privkey.encode())
    
    return privkey, pubkey.decode("utf-8").strip()


def create_interface(name):
    subprocess.run(
        [
            "ip",
            "link",
            "add",
            f"{name}",
            "type",
            "wireguard"
        ],
        check=True
    )


def configure_interface(name, private_key, ip_address, port):
    subprocess.run(
        [
            "ip", "addr", "add", ip_address,
            "dev", name
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


def bring_up_interface(name):
    subprocess.run(
        ["ip", "link", "set", name, "up"],
        check=True
    )


def bring_down_interface(name):
    subprocess.run(
        ["ip", "link", "set", name, "down"],
        check=True
    )


def remove_interface(name):
    subprocess.run(
        ["ip", "link", "delete", "dev", name],
        check=True
    )


def add_peer(interface_name, public_key, allowed_ips, endpoint):
    subprocess.run(
        [
            "wg", "set", interface_name,
            "peer", public_key,
            "allowed-ips", allowed_ips,
            "endpoint", endpoint
        ]
    )
