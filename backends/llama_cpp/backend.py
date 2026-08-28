from pathlib import Path
import subprocess
import time
import urllib.request
import urllib.error
import json


class LlamaCppBackend:

    def __init__(
        self,
        model_path,
        executable_path,
        host="127.0.0.1",
        port=8080,
        context_size=8192
    ):

        self.model_path = Path(
            model_path
        )

        self.executable_path = Path(
            executable_path
        )

        self.host = host
        self.port = port
        self.context_size = int(
            context_size
        )

        self.process = None

    # ==================================================
    # URL
    # ==================================================

    @property
    def url(self):

        return (
            f"http://{self.host}:{self.port}"
        )

    # ==================================================
    # CARGAR
    # ==================================================

    def load(self):

        if not self.model_path.exists():

            raise FileNotFoundError(
                f"Modelo no encontrado: "
                f"{self.model_path}"
            )

        if not self.executable_path.exists():

            raise FileNotFoundError(
                f"llama-server no encontrado: "
                f"{self.executable_path}"
            )

        if self.is_loaded():

            return

        command = [
            str(self.executable_path),

            "-m",
            str(self.model_path),

            "-ngl",
            "99",

            "-c",
            str(self.context_size),

            "--host",
            self.host,

            "--port",
            str(self.port),

            "--reasoning",
            "off"
        ]

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        self._wait_until_ready()

    # ==================================================
    # ESPERAR SERVIDOR
    # ==================================================

    def _wait_until_ready(
        self,
        timeout=120
    ):

        start_time = time.time()

        while (
            time.time() - start_time
            < timeout
        ):

            if self.process is not None:

                if self.process.poll() is not None:

                    raise RuntimeError(
                        "llama-server se cerró "
                        "durante el arranque."
                    )

            try:

                with urllib.request.urlopen(
                    f"{self.url}/health",
                    timeout=1
                ):

                    return

            except Exception:

                time.sleep(0.5)

        self.unload()

        raise RuntimeError(
            "AURA no pudo iniciar llama.cpp "
            "dentro del tiempo esperado."
        )

    # ==================================================
    # DESCARGAR
    # ==================================================

    def unload(self):

        if self.process is None:

            return

        try:

            self.process.terminate()

            self.process.wait(
                timeout=10
            )

        except subprocess.TimeoutExpired:

            self.process.kill()

            try:
                self.process.wait(
                    timeout=5
                )
            except Exception:
                pass

        except Exception:
            pass

        finally:

            self.process = None

    # ==================================================
    # GENERAR
    # ==================================================

    def generate(
        self,
        messages,
        max_tokens=300,
        temperature=0.7
    ):

        if not self.is_loaded():

            raise RuntimeError(
                "El modelo no está cargado."
            )

        data = {
            "messages": messages,
            "max_tokens": int(
                max_tokens
            ),
            "temperature": float(
                temperature
            ),
            "top_p": 0.9
        }

        request = urllib.request.Request(
            f"{self.url}/v1/chat/completions",
            data=json.dumps(
                data,
                ensure_ascii=False
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=300
            ) as response:

                result = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.HTTPError as error:

            try:

                body = error.read().decode(
                    "utf-8",
                    errors="replace"
                )

            except Exception:

                body = str(error)

            raise RuntimeError(
                "llama.cpp rechazó la solicitud "
                f"(HTTP {error.code}).\n"
                f"Detalles: {body}"
            )

        except Exception as error:

            raise RuntimeError(
                "Error al comunicarse con el modelo: "
                f"{error}"
            )

        try:

            return (
                result[
                    "choices"
                ][0][
                    "message"
                ][
                    "content"
                ]
            )

        except (
            KeyError,
            IndexError,
            TypeError
        ):

            raise RuntimeError(
                "llama.cpp devolvió una respuesta "
                "que AURA no pudo interpretar:\n"
                + json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2
                )
            )

    # ==================================================
    # ESTADO
    # ==================================================

    def is_loaded(self):

        if self.process is None:

            return False

        return (
            self.process.poll() is None
        )

    def get_status(self):

        return {
            "backend": "llama_cpp",
            "loaded": self.is_loaded(),
            "model": str(
                self.model_path
            ),
            "server": self.url,
            "context_size": (
                self.context_size
            ),
            "process_id": (
                self.process.pid
                if self.process is not None
                else None
            )
        }