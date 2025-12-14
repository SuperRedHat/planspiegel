import socket
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends
from pydantic import BaseModel, HttpUrl, Field

from auth import verify_jwt


#region Types
class ScanPortsRequest(BaseModel):
    target: HttpUrl = Field(default="https://planspiegel-landing.vercel.app/")


class ScanPortsResponse(BaseModel):
    open_ports: list[int]


#endregion

#region Router
router = APIRouter()


@router.post("/scan_ports", response_model=ScanPortsResponse)
def port_check(request: ScanPortsRequest, _: dict = Depends(verify_jwt)):
    results = start_check_ports(request.target.host)
    return ScanPortsResponse(open_ports=results["open_ports"])


def start_check_ports(host: str) -> dict:
    return {"open_ports": get_open_ports(host, port_range=(1, 1024), max_workers=1024)}

#endregion

#region Check
def check_port(target: str, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        result = s.connect_ex((target, port))
        if result == 0:
            return port
    # print(f" port {port} checked ")
    return None


def get_open_ports(target: str, port_range=(1, 1024), max_workers=50):
    open_ports = []
    ip_address = socket.gethostbyname(target)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(check_port, ip_address, port) for port in range(port_range[0], port_range[1] + 1)]
        for future in futures:
            port = future.result()
            if port:
                open_ports.append(port)
    return open_ports
#endregion
