#!/usr/bin/env python3
import os
import sys
import json
from typing import Optional

try:
    import requests
except Exception as e:
    print("ERROR: Missing 'requests' package. Install with: python -m pip install -r scripts/requirements.txt", file=sys.stderr)
    sys.exit(2)


def parse_args(argv) -> dict:
    args = {
        "workspace": os.environ.get("FOUNDRY_WORKSPACE") or os.environ.get("FOUNDRYWORKSPACE"),
        "spec": None,
        "image": None,
        "key": os.environ.get("FOUNDRYAPIKEY") or os.environ.get("FOUNDRY_API_KEY"),
        "url": None,
        "visibility": "private",
        "name": "hybrid-api",
    }
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--workspace":
            args["workspace"] = argv[i + 1]; i += 2; continue
        if a == "--spec":
            args["spec"] = argv[i + 1]; i += 2; continue
        if a == "--image":
            args["image"] = argv[i + 1]; i += 2; continue
        if a == "--key":
            args["key"] = argv[i + 1]; i += 2; continue
        if a == "--url":
            args["url"] = argv[i + 1]; i += 2; continue
        if a == "--name":
            args["name"] = argv[i + 1]; i += 2; continue
        if a == "--visibility":
            args["visibility"] = argv[i + 1]; i += 2; continue
        i += 1
    return args


def main() -> int:
    args = parse_args(sys.argv[1:])
    workspace = args["workspace"]
    spec_path = args["spec"]
    image = args["image"]
    key = args["key"]
    name = args["name"]
    visibility = args["visibility"]
    version = os.environ.get("GITHUB_SHA", "dev")

    if not all([workspace, spec_path, image, key]):
        print("Missing required params: --workspace, --spec, --image, --key", file=sys.stderr)
        return 1

    with open(spec_path, "r", encoding="utf-8") as f:
        api_spec = f.read()

    # NOTE: Replace the placeholder URL below with the actual Foundry publish endpoint
    url = args["url"] or f"https://foundry.azure.microsoft.com/workspaces/{workspace}/apis/publish"
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    payload = {
        "name": name,
        "image": image,
        "openapi": api_spec,
        "visibility": visibility,
        "version": version,
    }

    print("Publishing API to Foundry...")
    print(json.dumps({"url": url, "payload": {**payload, "openapi": "<omitted>"}}, indent=2))
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    print(resp.status_code, resp.text)
    resp.raise_for_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
