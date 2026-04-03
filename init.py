import os
import apt
import subprocess
import sys
import wg_manager
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
        if not wg_manager.is_interface_present(INTERFACE_NAME):
            print(f"Creating interface {INTERFACE_NAME}...")
            wg_manager.create_interface(INTERFACE_NAME)
            print(f"Interface {INTERFACE_NAME} created.")

            print(f"Generating keys...")
            private_key, public_key = wg_manager.generate_keys()

            print(f"Configuring {name}...")
            wg_manager.configure_interface(
                INTERFACE_NAME,
                private_key,
                INTERFACE_IP_ADDRESS,
                INTERFACE_PORT
            )
            print(f"{INTERFACE_NAME} successfully configured.")

        if not wg_manager.is_interface_up(INTERFACE_NAME):
            print(f"Bringing interface {INTERFACE_NAME} up...")
            wg_manager.bring_up_interface(INTERFACE_NAME)
            print(f"{INTERFACE_NAME} brought up.")

    except Exception as e:
        print(f"Something went wrong: {e}")


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


def initialize_flask():
    subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "Flask", "python-dotenv"],
        check=True
    )
    return True


def initialize_all():
    initialize_wireguard()
    initialize_vpn_agent()
    initialize_venv()
    initialize_flask()
