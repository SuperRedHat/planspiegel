import asyncio
import urllib.parse
from typing import List, Optional, Dict, Union

import httpx
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, HttpUrl, Field

from auth import verify_jwt
from lib.utils import run_async_in_sync


#region Types
class CookiesRequest(BaseModel):
    target: HttpUrl = Field(default="https://planspiegel-landing.vercel.app/")


class Category(BaseModel):
    identifier: str
    title: str
    title_de: str
    description: str
    description_de: str
    is_required: int


class AdditionalInfo(BaseModel):
    ip: str
    hostname: str
    city: str
    region: str
    country: str
    loc: str
    org: str
    postal: str
    timezone: str
    serverSoftware: Optional[str] = None


class CookieScannerResult(BaseModel):
    gdpr_compliant: bool
    images: List[str]
    status: str
    identifier: str
    target: HttpUrl
    webpageUpdateMessage: str
    scannedSites: int
    provider: Union[List, Dict]
    categories: List[Category]
    requests: List[Dict]
    additional_info: Union[List, Optional[AdditionalInfo]] = None
#endregion

#region Router
router = APIRouter()


@router.post("/cookies")
async def cookies_check(request: CookiesRequest, _: dict = Depends(verify_jwt)):
    response_data = await start_cookies_check(str(request.target))
    result = CookieScannerResult(**response_data)
    return result

#endregion

#region Check
def sync_start_cookies_check(url: str):
    return run_async_in_sync(start_cookies_check, url)


async def start_cookies_check(url: str) -> Dict:
    scan_id = await scan_cookie(url)
    response_data = await poll_cookie_scanner_result(scan_id)
    # print(response_data)

    # images
    prefix = "https://rapid-shadow-93cf.davidzhai0921.workers.dev"
    response_data["images"] = [f"{prefix}{image}" for image in response_data.get("images", [])]

    return response_data


base_url = "https://rapid-shadow-93cf.davidzhai0921.workers.dev/api/scan"
headers = {"accept": "application/json"}


async def scan_cookie(url: str):
    target = urllib.parse.quote(url, safe="")
    full_url = f"{base_url}?target={target}&limit=1"

    async with httpx.AsyncClient() as client:
        response = await client.post(full_url, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        identifier = response_data.get("identifier")
        if not identifier:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=response_data.get("error", "Failed to retrieve identifier"))
        return identifier

async def poll_cookie_scanner_result(identifier: str):
    result_url = f"{base_url}/{identifier}"

    await asyncio.sleep(20)

    for attempt in range(20):  # Up to 15 attempts
        async with httpx.AsyncClient() as client:
            response = await client.get(result_url, headers=headers)
            response.raise_for_status()
            result = response.json()
            # print(f"\n\nattempt #{attempt + 1}: {result}")
            if result.get("status") == "done":
                return result

        await asyncio.sleep(5) # seconds

    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Timeout while polling scanner result")
#endregion