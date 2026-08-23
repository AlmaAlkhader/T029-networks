import platform
import subprocess
import time

COMMAND_MAP = {
    "PING": {
        "linux": ["ping", "-c", "4"],
        "windows": ["ping", "-n", "4"]
    },
    "TRACERT": {
        "linux": ["traceroute"],
        "windows": ["tracert"]
    },
    "NSLOOKUP": {
        "linux": ["nslookup"],
        "windows": ["nslookup"]
    },
    "IPCONFIG": {
        "linux": ["ip", "addr", "show"],
        "windows": ["ipconfig", "/all"]
    },
    "ROUTE": {
        "linux": ["ip", "route"],
        "windows": ["route", "print"]
    },
    "ARP": {
        "linux": ["ip", "neigh"],
        "windows": ["arp", "-a"]
    },
    "NETSTAT": {
        "linux": ["ss", "-tunap"],
        "windows": ["netstat", "-an"]
    },
}

def execute(command, parameter, timeout=10):
    os_name = "windows" if platform.system() == "Windows" else "linux"
    
    if command not in COMMAND_MAP:
        return {
            "status": "Failed",
            "error": f"Unknown command: {command}"
        }
    
    base_cmd = COMMAND_MAP[command][os_name]
    
    if command in ("PING", "TRACERT", "NSLOOKUP"):
        full_cmd = base_cmd + [parameter]
    else:
        full_cmd = base_cmd
    
   

    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout 
        )
        execution_time = time.perf_counter() - start_time
        
        output = result.stdout + result.stderr
        status = "Success" if result.returncode == 0 else "Failed"
        if command == "NSLOOKUP":
            output_lower = output.lower()
            failure_phrases = (
                "can't find",
                "nxdomain",
                "non-existent domain",
                "server failed",
            )
            if any(phrase in output_lower for phrase in failure_phrases):
                status = "Failed"

        return {
            "status": status,
            "output": output,
            "execution_time": round(execution_time, 3)
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "Failed",
            "error": f"Command timed out after {timeout} seconds"
        } 
    except FileNotFoundError:
        return {
            "status": "Failed",
            "error": f"Command not found on this system: {full_cmd[0]}"
        } 
