import asyncio
import json
import os
from datetime import datetime
from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field

from auth import verify_jwt
from constants import MXTOOLBOX_KEY
from lib.utils import extract_hostname, run_async_in_sync


#region Types
class NetworkRequest(BaseModel):
    target: HttpUrl = Field(default="https://planspiegel-landing.vercel.app/")
#endregion

#region Check
def filter_network_report_for_summary(report: dict) -> dict:
    # print(f"Initial length: ", len(json.dumps(report)))
    minimized_results = []
    for check_name, check_result in report["results"].items():
        if check_result["status"] != "success":
            minimized_results.append({
                "CheckName": check_name,
                "Status": check_result["status"],
                "Error": check_result["error"]
            })
            continue

        failed_check_items = {
            check_item.get("Name", ""): check_item.get("Info", "")
            for check_item in check_result["data"].get("Failed", [])}

        warnings_check_items = {
            check_item.get("Name", ""): check_item.get("Info", "")
            for check_item in check_result["data"].get("Warnings", [])}

        passed_check_items = [
            check_item.get("Name", "")
            for check_item in check_result["data"].get("Passed", [])]

        timeouts_check_items = [
            check_item.get("Name", "")
            for check_item in check_result["data"].get("Timeouts", [])]

        minimized_check_report = {
            "CheckName": check_name,
            "Status": check_result["status"],
        }
        if len(failed_check_items) > 0:
            minimized_check_report["Failed"] = failed_check_items
        if len(warnings_check_items) > 0:
            minimized_check_report["Warnings"] = warnings_check_items
        if len(passed_check_items) > 0:
            minimized_check_report["Passed"] = passed_check_items
        if len(timeouts_check_items) > 0:
            minimized_check_report["Timeouts"] = timeouts_check_items

        minimized_results.append(minimized_check_report)

    lightweight_report = {
        "timestamp": report["timestamp"],
        "target": report["target"],
        "results": minimized_results
    }
    # print(f"Lightweight length: ", len(json.dumps(lightweight_report)))

    current_file_path = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file_path)
    project_root = os.path.abspath(os.path.join(current_dir, '..'))
    file_path = os.path.join(project_root, 'checks', 'network_check_example_lightweight.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(lightweight_report, f, indent=4)

    return lightweight_report


class MXToolboxClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.mxtoolbox.com/api/v1"
        self.headers = {
            "Authorization": api_key,
            "Content-Type": "application/json"
        }
        current_file_path = os.path.abspath(__file__)
        current_dir = os.path.dirname(current_file_path)
        project_root = os.path.abspath(os.path.join(current_dir, '..'))
        file_path = os.path.join(project_root, 'checks', 'network_check_example.json')
        with open(file_path, "r", encoding="utf-8") as f:
            self.results = json.load(f)

    async def lookup(self, command: str, target: str) -> Dict:
        hostname = extract_hostname(target)
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/lookup/{command}/?argument={hostname}"
            try:
                response = await client.get(url, headers=self.headers, timeout=60.0)
                response.raise_for_status()
                return {
                    "command": command,
                    "status": "success",
                    "data": response.json()
                }
            except httpx.HTTPError as e:
                return {
                    "command": command,
                    "status": "error",
                    "error": str(e)
                }

    async def parallel_lookup(self, target: str) -> Dict:
        commands = [
            "blacklist", "smtp", "mx", "a", "spf", "txt", "ptr", "cname",
            "whois", "arin", "soa", "tcp", "https", "ping", "trace", "dns"
        ]
        tasks = [self.lookup(cmd, target) for cmd in commands]
        results = await asyncio.gather(*tasks)

        return {
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "results": {result["command"]: result for result in results}
        }

    async def mock_parallel_lookup(self, target: str) -> Dict:
        await asyncio.sleep(10)
        return self.results


mxtoolbox = MXToolboxClient(api_key=MXTOOLBOX_KEY)


def sync_start_network_check(url: str):
    return run_async_in_sync(mxtoolbox.mock_parallel_lookup, url)


#endregion

#region Router
router = APIRouter()


@router.post("/network")
async def network_check(request: NetworkRequest, _: dict = Depends(verify_jwt)):
    target = str(request.target)

    if not target:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Target is required")

    try:
        results = await mxtoolbox.mock_parallel_lookup(target)
        return JSONResponse(content=results)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
#endregion