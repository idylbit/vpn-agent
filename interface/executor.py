import subprocess


class WgExecutor:
    @staticmethod
    def run(cmd: list):
        full_cmd = ["sudo"] + cmd
        try:
            return subprocess.check_output(full_cmd, text=True)
        except subprocess.CalledProcessError as e:
            print(f"OS Error: {e.stderr}")
            raise
