"""System environment and hardware probing utility."""

import os
import platform
import sys
from typing import Any, Dict


def get_system_hardware_info() -> Dict[str, Any]:
    """Inspects host machine without hardcoded paths or vendor assumptions."""
    cpu_count = os.cpu_count() or 1
    info: Dict[str, Any] = {
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": cpu_count,
        "python_version": sys.version.split()[0],
        "has_cuda": False,
    }

    try:
        import psutil
        vm = psutil.virtual_memory()
        info["total_ram_gb"] = round(vm.total / (1024 ** 3), 2)
        info["available_ram_gb"] = round(vm.available / (1024 ** 3), 2)
    except ImportError:
        info["total_ram_gb"] = "unknown (psutil not installed)"
        info["available_ram_gb"] = "unknown (psutil not installed)"

    # Probe for CUDA availability without hard requirement on torch
    try:
        import torch
        info["has_cuda"] = torch.cuda.is_available()
        if info["has_cuda"]:
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_count"] = torch.cuda.device_count()
    except ImportError:
        info["has_cuda"] = False

    return info
