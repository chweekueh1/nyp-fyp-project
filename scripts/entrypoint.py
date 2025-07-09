#!/usr/bin/env python3
import os
import sys
from infra_utils import get_docker_venv_path

# Set timezone environment variable for Singapore (UTC+8)
os.environ.setdefault("TZ", "Asia/Singapore")


# Determine if running as root (Unix)
def is_root() -> bool:
    """
    Check if the current process is running as root (Unix only).

    :return: True if running as root, False otherwise.
    :rtype: bool
    """
    if hasattr(os, "geteuid"):
        return os.geteuid() == 0
    return False


# Drop privileges to appuser if running as root
if os.name != "nt" and is_root():
    try:
        import pwd

        pw_record = pwd.getpwnam("appuser")
        os.setgid(pw_record.pw_gid)
        os.setuid(pw_record.pw_uid)
    except Exception as e:
        print(f"Warning: Could not drop privileges to appuser: {e}")
        sys.exit(1)

# Set venv_bin to the correct venv for this container
docker_mode = os.environ.get("DOCKER_MODE", "prod")
venv_path = os.environ.get("VENV_PATH", get_docker_venv_path(docker_mode))
if os.name == "nt":
    venv_bin = os.path.expanduser(os.path.join(venv_path, "Scripts"))
    os.environ["PATH"] = venv_bin + os.pathsep + os.environ.get("PATH", "")
else:
    venv_bin = os.path.join(venv_path, "bin")
    os.environ["PATH"] = venv_bin + ":" + os.environ.get("PATH", "")

# Exec the command
if len(sys.argv) > 1:
    if sys.argv[1] == "python":
        venv_python = os.path.join(venv_bin, "python")
        cmd = [venv_python] + sys.argv[2:]
    else:
        cmd = sys.argv[1:]
    print(f"[entrypoint.py] Executing: {cmd}")
    print(f"[entrypoint.py] PATH: {os.environ.get('PATH')}")
    try:
        os.execvp(cmd[0], cmd)
    except FileNotFoundError:
        print(
            f"[entrypoint.py] FileNotFoundError: Could not find executable '{cmd[0]}' in PATH: {os.environ.get('PATH')}"
        )
        print(f"[entrypoint.py] Full command attempted: {cmd}")
        sys.exit(1)
else:
    print("No command provided to entrypoint.")
    sys.exit(1)
