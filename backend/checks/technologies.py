import warnings

import requests
import retirejs
import urllib3
from Wappalyzer import Wappalyzer, WebPage
from bs4 import BeautifulSoup
from fastapi import APIRouter
from pydantic import BaseModel, HttpUrl, Field

from lib.utils import fix_script_urls, get_base_url, run_async_in_sync


#region Types
class TechnologiesRequest(BaseModel):
    target: HttpUrl = Field(default="https://planspiegel-landing.vercel.app/")


#endregion

#region Router
router = APIRouter()


@router.post("/technologies")
async def technologies_check(request: TechnologiesRequest):
    return await start_technologies_check(str(request.target))


# endregion

# region Check

def sync_start_technologies_check(url: str):
    return run_async_in_sync(start_technologies_check, url)


async def start_technologies_check(url: str):
    # loop = asyncio.get_event_loop()
    warnings.filterwarnings("ignore", category=UserWarning, module="Wappalyzer")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # technologies = await loop.run_in_executor(None, get_dependencies, url)
    # fixed_scripts = await loop.run_in_executor(None, fix_script_urls, get_base_url(url), scripts)
    # vulnerabilities = await loop.run_in_executor(None, analyze_scripts_with_retirejs, fixed_scripts)
    # scripts = await loop.run_in_executor(None, get_scripts, url)
    technologies = get_dependencies(url)
    scripts = get_scripts(url)
    fixed_scripts = fix_script_urls(get_base_url(url), scripts)
    vulnerabilities = analyze_scripts_with_retirejs(fixed_scripts)
    warnings.simplefilter('default', urllib3.exceptions.InsecureRequestWarning)

    return {
        "scripts": scripts,
        "technologies": technologies,
        "retire_analysis": vulnerabilities
    }


def get_scripts(url):
    # parsed_url = urlparse(url)
    # verify_ssl = parsed_url.scheme == "https"
    # response = requests.get(url, verify=verify_ssl)
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    scripts = [script.get("src") for script in soup.find_all("script") if script.get("src")]
    # print("JS Files Found:")
    # for script in scripts:
    #     print(script)
    return scripts


def get_dependencies(url):
    webpage = WebPage.new_from_url(url)
    wappalyzer = Wappalyzer.latest()
    technologies = wappalyzer.analyze_with_versions_and_categories(webpage)

    if not isinstance(technologies, dict):
        raise TypeError("Wappalyzer returned an unexpected type. Expected dict, got: " + str(type(technologies)))

    # print("\nDetected Technologies:")
    # for tech, info in technologies.items():
    #     print(f"{tech}: {info}")

    return technologies


def analyze_scripts_with_retirejs(scripts):
    # print("\nAnalyzing JS Files with Retire.js:")
    results = []
    for script in scripts:
        try:
            result = retirejs.scan_endpoint(script)
            # print(f"result: {script} {result}")
            results.append({script: result})
        except Exception as e:
            print(f"Failed to scan {script}: {e}")
    return results
#endregion
