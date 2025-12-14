import asyncio
import json
import os
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, HttpUrl, Field

from auth import verify_jwt
from lib.utils import is_running_in_docker, run_async_in_sync


#region Types
class LighthouseRequest(BaseModel):
    target: HttpUrl = Field(default="https://planspiegel-landing.vercel.app/")


#endregion

#region Router
router = APIRouter()


@router.post("/lighthouse")
async def lighthouse_check(request: LighthouseRequest, _: dict = Depends(verify_jwt)) -> Dict:
    return await get_lighthouse_report(str(request.target))


#endregion

#region Check
def sync_get_lighthouse_report(url: str):
    return run_async_in_sync(get_lighthouse_report, url)


async def get_lighthouse_report(url: str) -> Dict:
    domain = url.split("//")[-1].split("/")[0]
    report_name = f"report_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path = f"/tmp/{report_name}"

    try:
        base_flags = (
            f"lighthouse {url} "
            f"--output=json "
            f"--output-path={report_path} "
            f"--no-enable-error-reporting "
            f"--only-categories=performance,best-practices "
        )

        docker_flags = "--chrome-flags=\"--headless --no-sandbox --disable-dev-shm-usage --disable-gpu --single-process\""
        local_flags = "--chrome-flags=\"--headless --no-sandbox\""
        flags = docker_flags if is_running_in_docker() else local_flags
        command = (f"{base_flags}"
                   f"{flags}")

        process = await asyncio.create_subprocess_exec(
            'bash', '-c', command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(stderr.decode())

        loop = asyncio.get_event_loop()

        def read_json_file(file_path: str) -> Dict:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)

        report = await loop.run_in_executor(None, read_json_file, report_path)

        return filter_lighthouse_report(report)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Lighthouse error: {str(e)}")

    finally:
        if os.path.exists(report_path):
            os.remove(report_path)


def filter_lighthouse_report(report: dict) -> dict:
    needed_audits = [
        "is-on-https",
        "redirects-http",
        "third-party-cookies",
        "errors-in-console",
        "deprecations",
        "origin-isolation",
        "csp-xss",
        "has-hsts",
        "third-party-summary"
    ]

    filtered_audits = {
        key: report["audits"][key]
        for key in needed_audits
        if key in report["audits"]
    }

    return {"audits": filtered_audits}


def filter_lighthouse_report_for_summary(report: dict) -> dict:
    filtered_audits = {
        report["audits"][key]["title"]: {
            "score": report["audits"][key].get("score", ""),
            "items": report["audits"][key]["details"]["items"] if report["audits"][key].get("details", False) else ""
        } for key in report["audits"]
    }

    return filtered_audits

#endregion
