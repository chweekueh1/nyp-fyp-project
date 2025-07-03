import os
import sys
import getpass
import subprocess


def fix_nypai_chatbot_permissions():
    """
    Ensure ~/.nypai-chatbot and its contents are owned by the current user and writable.
    Works on Linux, macOS, and Windows.
    """
    chatbot_dir = os.path.expanduser("~/.nypai-chatbot")
    if os.path.exists(chatbot_dir):
        try:
            user = getpass.getuser()
            if sys.platform == "win32":
                # Windows: Use icacls for permission management
                try:
                    subprocess.run(
                        ["icacls", chatbot_dir, "/grant", f"{user}:(OI)(CI)F", "/T"],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print(f"✅ Fixed permissions for {chatbot_dir} (Windows)")
                except subprocess.CalledProcessError:
                    print(f"⚠️  Could not fix Windows permissions for {chatbot_dir}")
            else:
                # Linux/macOS: Use sudo chown/chmod
                try:
                    subprocess.run(
                        ["sudo", "chown", "-R", f"{user}:{user}", chatbot_dir],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    subprocess.run(
                        ["sudo", "chmod", "-R", "755", chatbot_dir],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print(f"✅ Fixed permissions for {chatbot_dir} (Unix)")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Could not fix Unix permissions for {chatbot_dir}: {e}")
        except Exception as e:
            print(f"⚠️  Could not fix permissions for {chatbot_dir}: {e}")


if __name__ == "__main__":
    fix_nypai_chatbot_permissions()
