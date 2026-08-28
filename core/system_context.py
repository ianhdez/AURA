import platform
import shutil
import subprocess
import ctypes


class SystemContext:

    def __init__(
        self,
        base_dir
    ):

        self.base_dir = base_dir

    # ==================================================
    # INFORMACIÓN COMPLETA
    # ==================================================

    def get(self):

        return {
            "aura": self._aura(),
            "windows": self._windows(),
            "hardware": self._hardware(),
            "storage": self._storage()
        }

    # ==================================================
    # AURA
    # ==================================================

    def _aura(self):

        return {
            "base_dir": str(
                self.base_dir
            ),
            "python": platform.python_version()
        }

    # ==================================================
    # WINDOWS
    # ==================================================

    def _windows(self):

        return {
            "system": platform.system(),
            "version": platform.version(),
            "release": platform.release(),
            "machine": platform.machine()
        }

    # ==================================================
    # HARDWARE
    # ==================================================

    def _hardware(self):

        ram = self._get_ram()

        return {
            "cpu": platform.processor(),

            "ram_gb": ram["total_gb"],

            "ram_available_gb": (
                ram["available_gb"]
            ),

            "ram_used_gb": (
                ram["used_gb"]
            ),

            "gpu": self._get_gpu()
        }

    # ==================================================
    # RAM
    # ==================================================

    def _get_ram(self):

        try:

            class MEMORYSTATUSEX(
                ctypes.Structure
            ):

                _fields_ = [
                    (
                        "dwLength",
                        ctypes.c_ulong
                    ),
                    (
                        "dwMemoryLoad",
                        ctypes.c_ulong
                    ),
                    (
                        "ullTotalPhys",
                        ctypes.c_ulonglong
                    ),
                    (
                        "ullAvailPhys",
                        ctypes.c_ulonglong
                    ),
                    (
                        "ullTotalPageFile",
                        ctypes.c_ulonglong
                    ),
                    (
                        "ullAvailPageFile",
                        ctypes.c_ulonglong
                    ),
                    (
                        "ullTotalVirtual",
                        ctypes.c_ulonglong
                    ),
                    (
                        "ullAvailVirtual",
                        ctypes.c_ulonglong
                    ),
                    (
                        "sullAvailExtendedVirtual",
                        ctypes.c_ulonglong
                    )
                ]

            memory = MEMORYSTATUSEX()

            memory.dwLength = (
                ctypes.sizeof(memory)
            )

            success = (
                ctypes.windll.kernel32
                .GlobalMemoryStatusEx(
                    ctypes.byref(memory)
                )
            )

            if not success:

                return {
                    "total_gb": 0,
                    "available_gb": 0,
                    "used_gb": 0
                }

            total = (
                memory.ullTotalPhys
            )

            available = (
                memory.ullAvailPhys
            )

            used = (
                total - available
            )

            return {
                "total_gb": round(
                    total / (1024 ** 3),
                    2
                ),

                "available_gb": round(
                    available / (1024 ** 3),
                    2
                ),

                "used_gb": round(
                    used / (1024 ** 3),
                    2
                )
            }

        except Exception:

            return {
                "total_gb": 0,
                "available_gb": 0,
                "used_gb": 0
            }

    # ==================================================
    # GPU
    # ==================================================

    def _get_gpu(self):

        try:

            result = subprocess.run(
                [
                    "nvidia-smi",

                    "--query-gpu="
                    "name,memory.total,"
                    "memory.used,temperature.gpu,"
                    "utilization.gpu",

                    "--format="
                    "csv,noheader,nounits"
                ],

                capture_output=True,

                text=True,

                encoding="utf-8",

                errors="replace",

                timeout=5
            )

            if result.returncode != 0:

                return "No disponible"

            lines = [
                line.strip()
                for line in result.stdout.splitlines()
                if line.strip()
            ]

            if not lines:

                return "No disponible"

            values = [
                value.strip()
                for value in lines[0].split(",")
            ]

            if len(values) < 5:

                return "Información no disponible"

            return {
                "name": values[0],

                "vram_total_mb": int(
                    values[1]
                ),

                "vram_used_mb": int(
                    values[2]
                ),

                "temperature_c": int(
                    values[3]
                ),

                "utilization_percent": int(
                    values[4]
                )
            }

        except Exception:

            return "No disponible"

    # ==================================================
    # ALMACENAMIENTO
    # ==================================================

    def _storage(self):

        try:

            total, used, free = (
                shutil.disk_usage(
                    self.base_dir
                )
            )

            return {
                "drive": (
                    self.base_dir.drive
                ),

                "total_gb": round(
                    total / (1024 ** 3),
                    2
                ),

                "used_gb": round(
                    used / (1024 ** 3),
                    2
                ),

                "free_gb": round(
                    free / (1024 ** 3),
                    2
                )
            }

        except Exception:

            return "No disponible"