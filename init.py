import os
import apt
import subprocess
import sys
from interface.wg import WgInterface
from dotenv import load_dotenv


load_dotenv()

VENV_DIR = os.path.join(os.getcwd(), "venv")
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")


if os.getuid() != 0:
    print "Please run this script as root."
    sys.exit(1)


def is_wireguard_installed():
    cache = apt.Cache()
    wg = cache.get("wireguard")
    return wg and wg.is_installed


def install_wireguard():
    cache = apt.Cache()
    cache.update()
    cache.open()
    wg = cache.get("wireguard")
    if wg:
        wg.mark_install()
        cache.commit()


def initialize_wireguard():
    if not is_wireguard_installed():
        print("Installing wireguard...")
        install_wireguard()
        print("Wireguard installed successfully.")


def initialize_venv():
    try:
        import venv
    except ImportError:
        print("python3-venv is missing. Installing...")
        subprocess.run(
            ["apt-get", "install", "-y", "python3-venv"],
            check=True
        )

    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.run(
            ["python3", "-m", "venv", VENV_DIR],
            check=True
        )


def initialize_vpn_interface():
    INTERFACE_NAME=os.getenv("INTERFACE_NAME")
    INTERFACE_IP_ADDRESS=os.getenv("INTERFACE_IP_ADDRESS")
    INTERFACE_PORT=os.getenv("INTERFACE_PORT", 51820)

    if not INTERFACE_NAME:
        print(f"ENV INTERFACE_NAME is missing.")
        sys.exit(1)

    if not INTERFACE_IP_ADDRESS:
        print(f"ENV INTERFACE_IP_ADDRESS is missing.")
        sys.exit(1)

    try:
        wg_interface = WgInterface(
            name=INTERFACE_NAME,
            ip_address=INTERFACE_IP_ADDRESS,
            port=INTERFACE_PORT
        )
        if not wg_interface.exists():
            print(f"Creating interface...")
            wg_interface.validate()
            wg_interface.save()
            print(f"Interface {wg_interface.name} created.")

        if not wg_interface.is_up():
            print(f"Bringing interface up...")
            wg_interface.bring_up()
            print(f"Interface brought up.")

    except ValidationError as e:
        print(f"{e}")
    except Exception as e:
        print(f"Something went wrong: {e}")


def initialize_flask():
    subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "Flask", "python-dotenv"],
        check=True
    )
    return True


def initialize_all():
    initialize_wireguard()
    initialize_venv()
    initialize_vpn_agent()
    initialize_flask()
