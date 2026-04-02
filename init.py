import os
import apt
import subprocess
import sys
import wg_manager


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
    name = wg_manager.INTERFACE_NAME
    ip = wg_manager.INTERFACE_IP_ADDRESS
    port = wg_manager.INTERFACE_PORT

    if not name:
        print(f"ENV INTERFACE_NAME is missing.")
        sys.exit(1)

    if not ip:
        print(f"ENV INTERFACE_IP_ADDRESS is missing.")
        sys.exit(1)

    try:
        if not wg_manager.is_interface_present(name):
            print(f"Creating interface {name}...")
            wg_manager.create_interface(name)
            print(f"Interface {name} created.")

            print(f"Generating keys...")
            private_key, public_key = wg_manager.generate_keys()

            print(f"Configuring {name}...")
            wg_manager.configure_interface(
                name,
                private_key,
                ip,
                port
            )
            print(f"{name} successfully configured.")

        if not wg_manager.is_interface_up(name):
            print(f"Bringing interface {name} up...")
            wg_manager.bring_up_interface(name)
            print(f"{name} brought up.")

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
        [VENV_PYTHON, "-m", "pip", "install", "flask", "python-dotenv"],
        check=True
    )
    return True


def initialize_all():
    initialize_wireguard()
    initialize_vpn_agent()
    initialize_venv()
    initialize_flask()
