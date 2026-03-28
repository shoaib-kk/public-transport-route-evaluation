from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
API_KEY_ENV_VAR = "TFNSW_API_KEY"
DOTENV_PATH = PROJECT_ROOT / ".env"


def timestamp() -> str:
    # get the time 
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_directory(path: Path) -> Path:
    # Create the directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_dotenv(path: Path = DOTENV_PATH) -> None:
    # Load environment variables from a .env file if it exists
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def api_headers(api_key: str | None = None) -> Mapping[str, str]:
    # Load the API key from the environment if not provided, and return the headers for authentication
    load_dotenv()
    token = api_key or os.getenv(API_KEY_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Set the {API_KEY_ENV_VAR} or add it to {DOTENV_PATH}"
        )
    return {"Authorization": f"apikey {token}"}


def infer_extension(url: str, content_type: str | None, fallback: str) -> str:
    # Infer the file extension 
    lowered_type = (content_type or "").lower()
    lowered_url = url.lower()

    if "application/zip" in lowered_type or lowered_url.endswith(".zip"):
        return ".zip"
    if "application/x-protobuf" in lowered_type or "application/octet-stream" in lowered_type:
        return fallback
    if "application/json" in lowered_type or lowered_url.endswith(".json"):
        return ".json"
    return fallback


def download_to_file(
    *,
    url: str,
    destination_dir: Path,
    filename_stem: str,
    headers: Mapping[str, str] | None = None,
    params: Mapping[str, str] | None = None,
    timeout: int = 120,
    fallback_extension: str,
) -> Path:
    # Download the content from the URL and save it to a file in the destination directory
    ensure_directory(destination_dir)

    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()

    extension = infer_extension(
        url=url,
        content_type=response.headers.get("Content-Type"),
        fallback=fallback_extension,
    )
    output_path = destination_dir / f"{filename_stem}_{timestamp()}{extension}"
    output_path.write_bytes(response.content)
    return output_path


def post_to_file(
    *,
    url: str,
    destination_dir: Path,
    filename_stem: str,
    headers: Mapping[str, str],
    json_body: Mapping[str, str],
    timeout: int = 120,
    fallback_extension: str,
) -> Path:
    # Send a POST request to the URL with the given JSON body and save the response content to a file in the destination directory
    ensure_directory(destination_dir)

    response = requests.post(url, headers=headers, json=json_body, timeout=timeout)
    response.raise_for_status()

    extension = infer_extension(
        url=url,
        content_type=response.headers.get("Content-Type"),
        fallback=fallback_extension,
    )
    output_path = destination_dir / f"{filename_stem}_{timestamp()}{extension}"
    output_path.write_bytes(response.content)
    return output_path
