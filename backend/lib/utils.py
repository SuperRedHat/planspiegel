import asyncio
import base64
import os
from urllib.parse import urljoin, urlparse

from fastapi import UploadFile
from pydantic import HttpUrl, ValidationError

from constants import RUNNING_IN_DOCKER


def is_running_in_docker() -> bool:
    # Check if Docker environment file exists
    if os.path.exists('/.dockerenv'):
        return True

    # Check if cgroup file contains "docker"
    if os.path.exists('/proc/self/cgroup'):
        with open('/proc/self/cgroup', 'r') as f:
            if 'docker' in f.read():
                return True

    # Check an environment variable as a fallback
    return RUNNING_IN_DOCKER == "true"


def fix_script_urls(base_url, scripts):
    fixed_scripts = []
    for script in scripts:
        if script.startswith(("http://", "https://")):
            fixed_scripts.append(script)
        elif script.startswith("//"):
            fixed_scripts.append(f"https:{script}")
        else:
            fixed_scripts.append(urljoin(base_url, script))
    return fixed_scripts


def get_base_url(url):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


def extract_hostname(url: str) -> str | None:
    try:
        return HttpUrl(url).host
    except ValidationError:
        return None


def run_async_in_sync(coro, *args, **kwargs):
    return asyncio.run(coro(*args, **kwargs))


async def get_base64_from_upload(file: UploadFile):
    file_content = await file.read()
    if file_content:
        base64_string = base64.b64encode(file_content).decode("utf-8")
        return f"data:{file.content_type};base64,{base64_string}"
    return None
