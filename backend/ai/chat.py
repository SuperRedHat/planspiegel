import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from io import BytesIO
from typing import List

import requests
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas
from reportlab.platypus import Image
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import StreamingResponse, JSONResponse

from ai.agent import get_agent_response, get_agent_response_stream, get_agent_check_summary_response
from auth import verify_jwt, TokenDataFulfilled
from checks.cookies import sync_start_cookies_check
from checks.lighthouse import sync_get_lighthouse_report, filter_lighthouse_report_for_summary
from checks.network import sync_start_network_check, filter_network_report_for_summary
from checks.scan_ports import start_check_ports
from checks.technologies import sync_start_technologies_check
from lib.google_storage import upload_attachment
from lib.postgres_db import yield_db, return_db
from lib.utils import extract_hostname
from models import Checkup, CheckupDB, db_save_checkup, db_checkups_by_user_id, CheckDB, CheckType, db_save_check, \
    db_save_chat, ChatDB, db_messages_by_chat_id, db_checkup_by_id, db_save_message, MessageDB, \
    Message, SenderType, Check, db_check_by_id, CheckStatus, db_complete_check_with_results, db_append_message_content, \
    db_complete_check_with_failure, db_delete_messages_by_chat_id

router = APIRouter()


# region CHECK LOGIC
async def assure_checkup_belongs_to_user(user_id: int, checkup_id: int, db: AsyncSession) -> Checkup:
    checkup = await db_checkup_by_id(checkup_id, db=db)
    if checkup is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This check doesn't exist")

    if checkup.owner_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This check belongs to the different user")
    return checkup


async def assure_check_belongs_to_user(user_id: int, checkup_id: int, check_id: int, db: AsyncSession):
    checkup = await assure_checkup_belongs_to_user(user_id, checkup_id, db)

    found = any(check.check_id == check_id for check in checkup.checks)
    if not found:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This check belongs to the different user")


executor = ThreadPoolExecutor()

async def start_check(db: AsyncSession, checkup: Checkup, check_type: CheckType):
    # CHECK
    check_dbo = CheckDB(check_type=check_type, checkup_id=checkup.checkup_id, status=CheckStatus.RUNNING)
    check = await db_save_check(check_dbo, db=db)
    # CHAT
    chat_dbo = ChatDB(check_id=check.check_id)
    await db_save_chat(chat_dbo, db=db)
    await db.close()
    check.chat = chat_dbo

    # START CHECK IN PARALLEL
    async def update_check_callback(_future, _check_dbo):
        print("[update_check_callback] callback!", _check_dbo.check_type, _check_dbo.checkup_id, _check_dbo.check_id)
        results = _future.result()
        results_for_summary = results

        _loop = asyncio.get_event_loop()
        match _check_dbo.check_type:
            case CheckType.LIGHTHOUSE:
                results_for_summary = await _loop.run_in_executor(None, filter_lighthouse_report_for_summary,
                                                                  results_for_summary)
            case CheckType.NETWORK:
                results_for_summary = await _loop.run_in_executor(None, filter_network_report_for_summary,
                                                                  results_for_summary)
        results_description = await _loop.run_in_executor(None, get_agent_check_summary_response,
                                                          str(results_for_summary), _check_dbo.check_type)
        _db = return_db()
        async with _db:
            await db_complete_check_with_results(_check_dbo, results, results_description, db=_db)

    async def update_check_failed_callback(_future, _check_dbo, exception):
        print("[update_check_failed_callback] callback!", _check_dbo.check_type, _check_dbo.checkup_id,
              _check_dbo.check_id)
        _db = return_db()
        async with _db:
            await db_complete_check_with_failure(_check_dbo, {"exception": str(exception)}, db=_db)

    def on_complete(_future: Future[dict]):
        exception = future.exception()
        if exception:
            asyncio.create_task(update_check_failed_callback(_future, check_dbo, exception))
        else:
            asyncio.create_task(update_check_callback(_future, check_dbo))

    loop = asyncio.get_running_loop()

    match check_type:
        case CheckType.SCAN_PORTS:
            host = extract_hostname(checkup.url)
            future = loop.run_in_executor(executor, start_check_ports, host)
            future.add_done_callback(on_complete)
        case CheckType.LIGHTHOUSE:
            future = loop.run_in_executor(executor, sync_get_lighthouse_report, checkup.url)
            future.add_done_callback(on_complete)
        case CheckType.COOKIE:
            future = loop.run_in_executor(executor, sync_start_cookies_check, checkup.url)
            future.add_done_callback(on_complete)
        case CheckType.TECHNOLOGIES:
            future = loop.run_in_executor(executor, sync_start_technologies_check, checkup.url)
            future.add_done_callback(on_complete)
        case CheckType.NETWORK:
            future = loop.run_in_executor(executor, sync_start_network_check, checkup.url)
            future.add_done_callback(on_complete)
    print("[start_check] finish", checkup.checkup_id, check_type)
    return check

# endregion

# region ROUTES
class CreateCheckupRequest(BaseModel):
    url: str = Field(default="https://planspiegel-landing.vercel.app/")


@router.post("/checkups", response_model=Checkup, description="start a checkup")
async def start_checkup(request: CreateCheckupRequest, user: TokenDataFulfilled = Depends(verify_jwt),
                        db=Depends(yield_db)):
    checkup_dbo = CheckupDB(url=request.url, owner_id=user.sub)
    checkup = await db_save_checkup(checkup_dbo, db=db)

    _db_ports = return_db()
    async with _db_ports:
        check_ports = await start_check(_db_ports, checkup, CheckType.SCAN_PORTS)

    _db_lighthouse = return_db()
    async with _db_lighthouse:
        check_lighthouse = await start_check(_db_lighthouse, checkup, CheckType.LIGHTHOUSE)

    _db3 = return_db()
    async with _db3:
        check_technologies = await start_check(_db3, checkup, CheckType.TECHNOLOGIES)

    _db4 = return_db()
    async with _db4:
        check_cookie = await start_check(_db4, checkup, CheckType.COOKIE)

    _db_network = return_db()
    async with _db_network:
        check_network = await start_check(_db_network, checkup, CheckType.NETWORK)
    # if is_running_in_docker():
    #     print("uncomment CheckType.NETWORK for PROD")
    #     await start_check(db, checkup, CheckType.NETWORK)

    # To get attached checks
    checkup.checks = [check_ports, check_lighthouse, check_network, check_technologies, check_cookie]
    print("[start_checkup] RESPOND", checkup.checkup_id)
    return checkup


@router.get("/checkups", response_model=List[Checkup])
async def get_user_checkups(user: TokenDataFulfilled = Depends(verify_jwt), db=Depends(yield_db)):
    return await db_checkups_by_user_id(user_id=user.sub, db=db)


@router.get("/checkups/{checkup_id}", response_model=Checkup)
async def get_checkup_by_id(checkup_id: int, user: TokenDataFulfilled = Depends(verify_jwt), db=Depends(yield_db)):
    return await assure_checkup_belongs_to_user(user.sub, checkup_id, db)


@router.get("/checkups/{checkup_id}/checks/{check_id}", response_model=Check, description="Check status")
async def get_check_by_id(checkup_id: int, check_id: int, user: TokenDataFulfilled = Depends(verify_jwt),
                          db=Depends(yield_db)):
    await assure_check_belongs_to_user(user.sub, checkup_id, check_id, db=db)
    return await db_check_by_id(check_id, db=db)


@router.get("/checkups/{checkup_id}/checks/{check_id}/chats/{chat_id}/messages", response_model=List[Message])
async def get_messages(checkup_id: int, check_id: int, chat_id: int, user: TokenDataFulfilled = Depends(verify_jwt),
                       db=Depends(yield_db)):
    await assure_check_belongs_to_user(user.sub, checkup_id, check_id, db=db)
    return await db_messages_by_chat_id(chat_id, db=db)


@router.post("/checkups/{checkup_id}/checks/{check_id}/chats/{chat_id}/messages",
             description="Send message to AI agent")
async def send_message(checkup_id: int, check_id: int, chat_id: int,
                       question: str = Form("Which ports are open?"),
                       use_stream: bool = Form(False),
                       file: UploadFile | None | str = None,
                       user=Depends(verify_jwt), db=Depends(yield_db)):
    # CHECK
    await assure_check_belongs_to_user(user.sub, checkup_id, check_id, db=db)
    check = await db_check_by_id(check_id, db=db)
    if check.results is None or check.status != CheckStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"There is no check results, check.status: {check.status}")
    results = str(check.results)

    if len(question) > 500:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The question size is unacceptable: {len(question)}")

    # ATTACHMENTS
    attachment_url = None
    if file and not isinstance(file, str):
        # base64_encoded_file = await get_base64_from_upload(file)
        # if base64_encoded_file:
        #     attachment_url = base64_encoded_file
        #     print("attachment_url", attachment_url)
        file_content = await file.read()
        if file_content:
            attachment_url = upload_attachment(file.filename, file.content_type, file_content)
            print("attachment_url", attachment_url)

    # MESSAGES
    messages = await db_messages_by_chat_id(chat_id, db=db)
    print("messages", [message.content for message in messages])

    user_message_dbo = MessageDB(content=question, chat_id=chat_id, attachment_url=attachment_url)
    await db_save_message(user_message_dbo, db=db)

    if use_stream:
        ai_message_dbo = MessageDB(content="", chat_id=chat_id, sender_type=SenderType.ASSISTANT)
        await db_save_message(ai_message_dbo, db=db)

        async def stream_response():
            for part in get_agent_response_stream(check.check_type, results, messages, question, attachment_url):
                await db_append_message_content(ai_message_dbo, part, db=db)
                yield part

        return StreamingResponse(stream_response(), media_type="text/event-stream")
    else:
        ai_answer = get_agent_response(check.check_type, results, messages, question, attachment_url)
        ai_message_dbo = MessageDB(content=ai_answer, chat_id=chat_id, sender_type=SenderType.ASSISTANT)
        await db_save_message(ai_message_dbo, db=db)
        return JSONResponse({"ai_answer": ai_answer})

@router.delete("/checkups/{checkup_id}/checks/{check_id}/chats/{chat_id}/messages",
               status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat_history(checkup_id: int, check_id: int, chat_id: int,
                             user: TokenDataFulfilled = Depends(verify_jwt),
                             db=Depends(yield_db)):
    await assure_check_belongs_to_user(user.sub, checkup_id, check_id, db=db)
    await db_delete_messages_by_chat_id(chat_id, db=db)
    return JSONResponse(content={"message": "Resource deleted successfully"})

# endregion

# region PDF Report

def draw_section_header(c, title, x, y):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, title)
    c.setFont("Helvetica", 10)


def draw_text(c, text, x, y):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, text)
    c.setFont("Helvetica", 10)


def wrap_and_draw_text(c, text, x, y, line_width=500):
    lines = simpleSplit(text, 'Helvetica', 10, line_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= 15
    return y


def add_image_to_pdf(c, img_url, x, y, max_width=500):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            img = Image(BytesIO(response.content))
            img_width, img_height = img.wrap(max_width, 0)
            img.drawOn(c, x, y - img_height)
            return y - img_height - 50
    except Exception as e:
        c.drawString(x, y, f"Failed to load image from {img_url}. Error: {str(e)}")
    return y


def add_logo(c, logo_path, x, y, width=80, height=40):
    """
    Draw the logo on the canvas...
    """
    try:
        c.drawImage(logo_path, x, y, width, height)
    except Exception as e:
        c.drawString(x, y + 20, f"Error loading logo: {str(e)}")


def common_network_data(c, y_position, check_data, title):
    # Audit Details
    report_data = check_data.get("results", {}).get(title, {})
    if report_data:
        # Dynamic Title for Each Report Type
        draw_section_header(c, f"{title.capitalize()} Report", 50, y_position)
        y_position -= 30
        command = report_data.get("command", "Unknown")
        status = report_data.get("status", "Unknown")
        command_argument = report_data.get("data", {}).get("CommandArgument", "Unknown")
        y_position = wrap_and_draw_text(c, f"Command: {command}", 50, y_position)
        y_position = wrap_and_draw_text(c, f"Status: {status}", 50, y_position)
        y_position = wrap_and_draw_text(c, f"Command Argument: {command_argument}", 50, y_position)
        y_position -= 20

        # Failed Checks Section
        failed_checks = report_data.get("data", {}).get("Failed", [])
        total_failed = len(failed_checks)
        if failed_checks:
            draw_section_header(c, f"Failed Checks (Total: {total_failed})", 50, y_position)
            y_position -= 20
            for check in failed_checks:
                check_name = check.get("Name", "Unknown")
                check_url = check.get("Url", "No URL")
                y_position = wrap_and_draw_text(c, f"{check_name}: {check_url}", 50, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        # Warnings Checks Section
        warnings_checks = report_data.get("data", {}).get("Warnings", [])
        total_warnings = len(warnings_checks)
        if warnings_checks:
            draw_section_header(c, f"Warnings Checks (Total: {total_warnings})", 50, y_position)
            y_position -= 20
            for check in warnings_checks:
                check_name = check.get("Name", "Unknown")
                check_info = check.get("Info", "No Info")
                check_url = check.get("Url", "No URL")
                additional_info = ", ".join(check.get("AdditionalInfo", []))
                y_position = wrap_and_draw_text(c, f"{check_name} ({check_info}): {check_url}", 50, y_position)
                y_position = wrap_and_draw_text(c, f"Additional Info: {additional_info}", 70, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        # Passed Checks Section
        passed_checks = report_data.get("data", {}).get("Passed", [])
        total_passed = len(passed_checks)
        if passed_checks:
            draw_section_header(c, f"Passed Checks (Total: {total_passed})", 50, y_position)
            y_position -= 20
            for check in passed_checks:
                check_name = check.get("Name", "Unknown")
                check_info = check.get("Info", "No Info")
                check_url = check.get("Url", "No URL")
                additional_info = ", ".join(check.get("AdditionalInfo", []))
                y_position = wrap_and_draw_text(c, f"{check_name} ({check_info}): {check_url}", 50, y_position)
                y_position = wrap_and_draw_text(c, f"Additional Info: {additional_info}", 70, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        # Information Section
        information_lookups = report_data.get("data", {}).get("Information", [])
        if information_lookups:
            y_position -= 30
            draw_section_header(c, "Information Lookups", 50, y_position)
            y_position -= 20
            for information in information_lookups:
                d_type = information.get("Type", "Unknown")
                d_result = information.get("Domain Name", "No Domain name")
                result = information.get("IP Address", "No IP address")
                y_position = wrap_and_draw_text(c, f"{d_type} ({d_result}): {result}  ", 50, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        # Transcript Section
        transcript_lookups = report_data.get("data", {}).get("Transcript", [])
        if transcript_lookups:
            y_position -= 30
            draw_section_header(c, "Transcript Lookups", 50, y_position)
            y_position -= 20
            for transcript in transcript_lookups:
                server_name = transcript.get("ServerName", "Unknown")
                result = transcript.get("Result", "No result")
                transcript_result = transcript.get("Transcript", "No result")
                y_position = wrap_and_draw_text(c, f"{server_name}: {result}", 50, y_position)
                y_position = wrap_and_draw_text(c, f"Transcript Info: {transcript_result}", 70, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        # Related Lookups Section
        related_lookups = report_data.get("data", {}).get("RelatedLookups", [])
        if related_lookups:
            y_position -= 30
            draw_section_header(c, "Related DNS Lookups", 50, y_position)
            y_position -= 20
            for lookup in related_lookups:
                lookup_name = lookup.get("Name", "Unknown")
                lookup_url = lookup.get("URL", "No URL")
                y_position = wrap_and_draw_text(c, f"{lookup_name}: {lookup_url}", 50, y_position)
                if y_position < 50:
                    c.showPage()
                    y_position = 750

        c.showPage()


def create_report(c, check_data, y_position):
    logo_path = "/assets/Planspiegel.png"
    add_logo(c, logo_path, 50, 740)

    # Header Section
    draw_section_header(c, f"Scan Report for '{check_data.get('url', 'Unknown URL')}' ", 50, y_position)
    y_position -= 30

    # Check Information
    draw_text(c, f"Check ID: {check_data.get('check_id')}", 50, y_position)
    y_position -= 15
    draw_text(c, f"Check Type: {check_data.get('check_type').replace('CheckType', '')}", 50, y_position)
    y_position -= 15
    draw_text(c, f"Status: {check_data.get('status').replace('CheckStatus', '')}", 50, y_position)
    y_position -= 30

    results = check_data.get("results", {})
    if results:
        # Header Section
        if (str(check_data.get('check_type')) == "CheckType.TECHNOLOGIES"):

            draw_section_header(c, "Technology Scan Report", 50, y_position)
            y_position -= 30

            # Scripts Section
            draw_section_header(c, "Scripts", 50, y_position)
            y_position -= 20
            scripts = check_data.get("results", {}).get("scripts", [])
            if scripts:
                for script in scripts:
                    y_position = wrap_and_draw_text(c, f"Script URL: {script}", 50, y_position)
                    if y_position < 50:
                        c.showPage()
                        y_position = 750

            # Technologies Section
            y_position -= 30
            draw_section_header(c, "Technologies Detected", 50, y_position)
            y_position -= 20
            technologies = check_data.get("results", {}).get("technologies", {})
            if technologies:
                for tech_name, tech_details in technologies.items():
                    versions = ", ".join(tech_details.get("versions", ["N/A"]))
                    categories = ", ".join(tech_details.get("categories", ["N/A"]))
                    draw_text(c, f"{tech_name}: Versions - {versions}, Categories - {categories}", 50, y_position)
                    y_position -= 15
                    if y_position < 50:
                        c.showPage()
                        y_position = 750

            # Vulnerability Analysis
            y_position -= 30
            draw_section_header(c, "Retire.js Analysis", 50, y_position)
            y_position -= 20

            retire_analysis = check_data.get("results", {}).get("retire_analysis", [])
            if retire_analysis:
                for resource in retire_analysis:
                    for resource_url, vulnerabilities in resource.items():
                        draw_text(c, f"Resource: {resource_url}", 50, y_position)
                        y_position -= 15
                        for vuln in vulnerabilities:
                            component = vuln.get("component", "Unknown")
                            version = vuln.get("version", "Unknown")
                            detection = vuln.get("detection", "Unknown")
                            draw_text(c, f"- {component} v{version}, Detected via: {detection}", 60, y_position)
                            y_position -= 15
                            if y_position < 50:
                                c.showPage()
                                y_position = 750

        # Results Section - scan_ports
        if (str(check_data.get('check_type')) == "CheckType.SCAN_PORTS"):
            open_ports = check_data.get("results", {}).get("open_ports", [])
            if open_ports:
                draw_section_header(c, "Scan Results", 50, y_position)
                y_position -= 20
                for port in open_ports:
                    status_text = "Secure (Standard Web Traffic)" if port in [80, 443] else "Insecure"
                    draw_text(c, f"Port {port}: {status_text}", 50, y_position)
                    y_position -= 15
            y_position -= 30
        # cookie
        # Header Section
        if (str(check_data.get('check_type')) == "CheckType.COOKIE"):
            draw_section_header(c, "GDPR Compliance and Website Analysis Report", 50, y_position)
            y_position -= 30

            # Target Information
            draw_section_header(c, "Target Information", 50, y_position)
            y_position -= 20
            target = check_data.get("results", {}).get("target", "Unknown")
            status = check_data.get("results", {}).get("status", "Unknown")
            gdpr_compliant = "Yes" if check_data.get("results", {}).get("gdpr_compliant", False) else "No"
            y_position = wrap_and_draw_text(c, f"Target: {target}", 50, y_position)
            y_position = wrap_and_draw_text(c, f"Status: {status}", 50, y_position)
            y_position = wrap_and_draw_text(c, f"GDPR Compliant: {gdpr_compliant}", 50, y_position)
            y_position -= 20

            # Images Section

            images = check_data.get("results", {}).get("images", [])
            if images:
                draw_section_header(c, "Images", 50, y_position)
                y_position -= 20
                for img_url in images:
                    y_position = add_image_to_pdf(c, img_url, 50, y_position)
                    if y_position < 50:
                        c.showPage()
                        y_position = 750

            # Cookie Categories Section
            y_position -= 30
            draw_section_header(c, "Cookie Categories", 50, y_position)
            y_position -= 20
            categories = check_data.get("results", {}).get("categories", [])
            if categories:
                for category in categories:
                    title = category.get("title", "Unknown")
                    description = category.get("description", "No description available")
                    is_required = "Required" if category.get("is_required", 0) == 1 else "Optional"
                    y_position = wrap_and_draw_text(c, f"{title} ({is_required}): {description}", 50, y_position)
                    if y_position < 50:
                        c.showPage()
                        y_position = 750

            # Additional Information Section
            y_position -= 30
            draw_section_header(c, "Additional Information", 50, y_position)
            y_position -= 20
            additional_info = check_data.get("results", {}).get("additional_info", {})
            if additional_info:
                for key, value in additional_info.items():
                    y_position = wrap_and_draw_text(c, f"{key}: {value}", 50, y_position)
                    if y_position < 50:
                        c.showPage()
                        y_position = 750

        # Header Section - lighthouse
        if (str(check_data.get('check_type')) == "CheckType.LIGHTHOUSE"):
            draw_section_header(c, "Security Audit Report", 50, y_position)
            y_position -= 30

            # Audit Details
            audits = check_data.get("results", {}).get("audits", {})
            if audits:
                for audit_id, audit_details in audits.items():
                    title = audit_details.get("title", "Unknown")
                    description = audit_details.get("description", "No description available.")
                    score = audit_details.get("score", "N/A")
                    severity_items = audit_details.get("details", {}).get("items", [])

                    # Section Header for Each Audit
                    draw_section_header(c, title, 50, y_position)
                    y_position -= 20
                    y_position = wrap_and_draw_text(c, f"Description: {description}", 50, y_position)
                    y_position = wrap_and_draw_text(c, f"Score: {score}", 50, y_position)

                    # Severity Items for Audit
                    if severity_items:
                        y_position -= 10
                        draw_section_header(c, "Severity Details:", 50, y_position)
                        y_position -= 20
                        for item in severity_items:
                            directive = item.get("directive", "N/A")
                            issue_description = item.get("description", "No description available.")
                            severity = item.get("severity", "N/A")
                            y_position = wrap_and_draw_text(c, f"Directive: {directive}", 50, y_position)
                            y_position = wrap_and_draw_text(c, f"Issue: {issue_description}", 50, y_position)
                            y_position = wrap_and_draw_text(c, f"Severity: {severity}", 50, y_position)
                            y_position -= 10

            # Page Break if content overflows
            if y_position < 50:
                c.showPage()
                y_position = 750

        # Network
        if (str(check_data.get('check_type')) == "CheckType.NETWORK"):

            report_types = ['blacklist', 'smtp', 'mx', 'spf', 'a', 'txt', 'seo', 'tcp', 'ping', 'trace', 'dns']
            results = check_data.get("results", {})

            for report_type in report_types:
                report_data = {"results": results.get(report_type, {})}
                common_network_data(c, y_position, report_data, report_type)

    # Results Description
    y_position -= 15
    draw_section_header(c, "Results Description", 50, y_position)
    y_position -= 20
    description = check_data.get("results_description", "No description available.")
    lines = description.split(". ")
    for line in lines:
        wrapped_lines = simpleSplit(line.strip(), 'Helvetica', 10, 500)
        for wrapped_line in wrapped_lines:
            c.drawString(50, y_position, wrapped_line)
            y_position -= 15
            if y_position < 50:
                c.showPage()
                y_position = 750


@router.get("/checkups/{checkup_id}/pdf_report", description="creates a PDF representation")
async def pdf_report(checkup_id: int, user: TokenDataFulfilled = Depends(verify_jwt), db=Depends(yield_db)):
    checkup = await assure_checkup_belongs_to_user(user.sub, checkup_id, db=db)
    # return checkup

    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    y_position = 750
    for check in checkup.checks:
        pdf_content = ""
        if check.status == CheckStatus.FAILED:
            pdf_content = f"error with exception: {str(check.results)}"
        if check.status == CheckStatus.RUNNING:
            pdf_content = f"status: is running"
        else:
            pdf_content = check.results_description

        check_data = {
            "url": checkup.url,
            "check_id": check.check_id,
            "check_type": check.check_type,
            "status": check.status,
            "results": check.results,
            "results_description": pdf_content,
        }
        create_report(c, check_data, y_position)
        c.showPage()

    c.save()
    pdf_buffer.seek(0)
    host = extract_hostname(checkup.url)
    # return checkup
    return StreamingResponse(pdf_buffer, media_type="application/pdf",
                             headers={"Content-Disposition": f"attachment; filename={host}_report.pdf"})

# endregion
