import os
import apt
import subprocess
import sys
from interface.executor import WgExecutor


VPN_AGENT_DIR = os.getcwd()
VENV_DIR = os.path.join(VPN_AGENT_DIR, "venv")
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python")


def is_root() -> bool:
    return os.getuid() == 0


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
    subprocess.run([
        "apt-get", "install", "-y", 
        "python3-venv", 
        "python3-pip", 
        "python3-full"
    ], check=True)

    if not os.path.exists(VENV_DIR):
        print("Creating virtual environment...")
        subprocess.run(
            [sys.executable, "-m", "venv", VENV_DIR],
            check=True
        )
    subprocess.run(
        [VENV_PYTHON, "-m", "pip", "install", "-r", "requirements.txt"],
        check=True
    )


def add_vpnagent_user():
    result = subprocess.run(
        ["useradd", "-m", "-r", "vpnagent"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Successfully created vpnagent user.")
    elif result.returncode == 9:
        print("User 'vpnagent' already exists. Skipping...")
    else:
        print(f"CRITICAL: Failed to create user. Error: {result.stderr}")
        sys.exit(1)


def configure_sudo_rules():
    commands_string = ", ".join(WgExecutor.SUDO_WHITELIST)
    sudo_rules = f"vpnagent ALL=(ALL) NOPASSWD: {commands_string}\n"
    sudoers_path = "/etc/sudoers.d/vpn-agent"
    with open(sudoers_path, "w") as f:
        f.write(sudo_rules)
    os.chmod(sudoers_path, 0o440)
    print(f"Sudo rules configured at {sudoers_path}")


def initialize_vpnagent():
    add_vpnagent_user()
    configure_sudo_rules()
    subprocess.run(
        ["chown", "-R", "vpnagent:vpnagent", VPN_AGENT_DIR],
        check=True
    )


def create_systemd_service():
    entry_point = os.path.join(VPN_AGENT_DIR, "main.py")
    service_content = f"""[Unit]
Description=WireGuard VPN Agent API
After=network.target

[Service]
User=vpnagent
WorkingDirectory={VPN_AGENT_DIR}
Environment="PATH={VENV_DIR}/bin"
ExecStart={VENV_PYTHON} {entry_point}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"""
    service_path = "/etc/systemd/system/vpnagent.service"

    with open(service_path, "w") as f:
        f.write(service_content)

    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "vpnagent.service"], check=True)
    print(f"Service created and enabled at {service_path}")


if __name__ == "__main__":
    if not is_root:
        print("Intitialize script must run as root to setup vpn agent. It will not run as root after seetup.")
        sys.exit(1)
    initialize_wireguard()
    initialize_venv()
    initialize_vpnagent()
    create_systemd_service()
    print("Starting the VPN Agent as 'vpnagent' user...")
    subprocess.run(["systemctl", "start", "vpnagent.service"], check=True)
    print("VPN Agent is now running in the background.")
