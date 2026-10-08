"""Read an API key from the macOS Keychain.

Store one with:

    security add-generic-password -U -s autoschemakg -a XAI_API_KEY -w

-s is the service name. -a is the account, which matches the env var name
(XAI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY). -U updates an existing item.
The password is read from the prompt, so it does not land in shell history.
"""

import shutil
import subprocess

SERVICE = "autoschemakg"


def get_secret(account: str, service: str = SERVICE) -> str | None:
    security = shutil.which("security")
    if security is None:
        return None
    result = subprocess.run(
        [security, "find-generic-password", "-s", service, "-a", account, "-w"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    secret = result.stdout.strip()
    return secret or None
