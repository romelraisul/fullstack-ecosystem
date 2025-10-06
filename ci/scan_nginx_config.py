import re
import sys
from pathlib import Path


def main():
    """
    Scans the Nginx configuration for forbidden directives.
    """
    config_path = Path(__file__).parent.parent / "docker" / "gateway"
    nginx_conf = config_path / "nginx.conf"

    forbidden = [
        "auth_basic",
    ]

    found_forbidden = []

    with open(nginx_conf) as f:
        content = f.read()
        for directive in forbidden:
            if re.search(directive, content, re.IGNORECASE):
                found_forbidden.append(directive)

    if found_forbidden:
        print(f"Error: Found forbidden directives in nginx.conf: {found_forbidden}")
        sys.exit(1)

    print("Nginx configuration scan passed.")


if __name__ == "__main__":
    main()
