import json
import subprocess
import time
import urllib.error
import urllib.request

from pathlib import Path


class EmbeddingEngine:

    """
    Motor local de embeddings para AURA.

    Utiliza un llama-server independiente del servidor
    conversacional de Qwen.

    Arquitectura:

        AURA
          |
          +-- Qwen / llama-server :8080
          |
          +-- BGE-M3 / llama-server :8081

    El servidor de embeddings se inicia de forma diferida:
    solamente cuando AURA necesita generar un embedding.
    """

    def __init__(
        self,
        base_dir,
        config
    ):

        self.base_dir = Path(
            base_dir
        ).resolve()

        self.config = config

        self.host = (
            config.EMBEDDING_HOST
        )

        self.port = (
            config.EMBEDDING_PORT
        )

        self.process = None

        self.model_path = (
            config.embedding_model_path(
                self.base_dir
            )
        )

        self.executable_path = (
            config.embedding_executable_path(
                self.base_dir
            )
        )

        self._dimension = (
            config.EMBEDDING_DIMENSIONS
        )

    # ==================================================
    # URL
    # ==================================================

    @property
    def url(self):

        return (
            f"http://"
            f"{self.host}:"
            f"{self.port}"
        )

    # ==================================================
    # DIMENSIÓN
    # ==================================================

    @property
    def dimension(self):

        return self._dimension

    # ==================================================
    # DISPONIBILIDAD
    # ==================================================

    def available(self):

        if self.process is None:

            return False

        return (
            self.process.poll() is None
        )

    # ==================================================
    # CARGAR SERVIDOR
    # ==================================================

    def load(self):

        if self.available():

            return

        if not self.model_path.exists():

            raise FileNotFoundError(
                "Modelo de embeddings no encontrado:\n"
                f"{self.model_path}\n\n"
                "Coloca un modelo BGE-M3 compatible "
                "con llama.cpp en esa ruta."
            )

        if not self.executable_path.exists():

            raise FileNotFoundError(
                "llama-server no encontrado:\n"
                f"{self.executable_path}"
            )

        command = [
            str(
                self.executable_path
            ),

            "-m",
            str(
                self.model_path
            ),

            "--embedding",

            "--pooling",
            "mean",

            "--host",
            self.host,

            "--port",
            str(
                self.port
            ),

            "--ctx-size",
            str(
                self.config.EMBEDDING_CONTEXT_SIZE
            ),

            "--no-webui"
        ]

        self.process = subprocess.Popen(
            command,

            stdout=subprocess.DEVNULL,

            stderr=subprocess.DEVNULL
        )

        self._wait_until_ready()

    # ==================================================
    # ESPERAR
    # ==================================================

    def _wait_until_ready(
        self,
        timeout=120
    ):

        start = time.time()

        while (
            time.time() - start
            < timeout
        ):

            if self.process is not None:

                if (
                    self.process.poll()
                    is not None
                ):

                    self.process = None

                    raise RuntimeError(
                        "El servidor de embeddings "
                        "se cerró durante el arranque."
                    )

            try:

                request = urllib.request.Request(
                    f"{self.url}/health",
                    method="GET"
                )

                with urllib.request.urlopen(
                    request,
                    timeout=1
                ):

                    return

            except Exception:

                time.sleep(
                    0.5
                )

        self.unload()

        raise RuntimeError(
            "El servidor de embeddings no "
            "estuvo disponible a tiempo."
        )

    # ==================================================
    # EMBEDDING
    # ==================================================

    def encode(
        self,
        text
    ):

        if text is None:

            return []

        text = str(
            text
        ).strip()

        if not text:

            return []

        self.load()

        payload = {
            "input": text,

            "model": (
                self.config.EMBEDDING_MODEL_NAME
            ),

            "encoding_format": "float"
        }

        request = urllib.request.Request(
            f"{self.url}/v1/embeddings",

            data=json.dumps(
                payload,
                ensure_ascii=False
            ).encode(
                "utf-8"
            ),

            headers={
                "Content-Type":
                    "application/json"
            },

            method="POST"
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=120
            ) as response:

                result = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

        except urllib.error.HTTPError as error:

            try:

                details = (
                    error.read()
                    .decode(
                        "utf-8",
                        errors="replace"
                    )
                )

            except Exception:

                details = str(
                    error
                )

            raise RuntimeError(
                "Error del servidor de embeddings "
                f"(HTTP {error.code}): "
                f"{details}"
            )

        except Exception as error:

            raise RuntimeError(
                "No se pudo generar el embedding: "
                f"{error}"
            )

        embedding = self._extract_embedding(
            result
        )

        if not embedding:

            raise RuntimeError(
                "El servidor de embeddings "
                "devolvió un vector vacío."
            )

        # --------------------------------------------------
        # La primera ejecución permite descubrir
        # automáticamente la dimensión real del modelo.
        # --------------------------------------------------

        if self._dimension is None:

            self._dimension = len(
                embedding
            )

        elif len(
            embedding
        ) != self._dimension:

            raise RuntimeError(
                "Dimensión de embedding inesperada. "
                f"Esperada: {self._dimension}. "
                f"Recibida: {len(embedding)}."
            )

        return embedding

    # ==================================================
    # BATCH
    # ==================================================

    def encode_batch(
        self,
        texts
    ):

        if not texts:

            return []

        self.load()

        cleaned = [
            str(text).strip()
            for text in texts
            if text is not None
            and str(text).strip()
        ]

        if not cleaned:

            return []

        payload = {
            "input": cleaned,

            "model": (
                self.config.EMBEDDING_MODEL_NAME
            ),

            "encoding_format": "float"
        }

        request = urllib.request.Request(
            f"{self.url}/v1/embeddings",

            data=json.dumps(
                payload,
                ensure_ascii=False
            ).encode(
                "utf-8"
            ),

            headers={
                "Content-Type":
                    "application/json"
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

        except Exception as error:

            raise RuntimeError(
                "No se pudieron generar los "
                f"embeddings: {error}"
            )

        data = result.get(
            "data",
            []
        )

        embeddings = [
            item.get(
                "embedding",
                []
            )
            for item in data
        ]

        if not embeddings:

            raise RuntimeError(
                "No se recibieron embeddings."
            )

        dimension = len(
            embeddings[0]
        )

        if self._dimension is None:

            self._dimension = dimension

        if dimension != self._dimension:

            raise RuntimeError(
                "Dimensión de embeddings "
                "incompatible."
            )

        return embeddings

    # ==================================================
    # EXTRAER VECTOR
    # ==================================================

    @staticmethod
    def _extract_embedding(
        result
    ):

        data = result.get(
            "data",
            []
        )

        if not data:

            return []

        return data[0].get(
            "embedding",
            []
        )

    # ==================================================
    # DESCARGAR SERVIDOR
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

            try:

                self.process.kill()

                self.process.wait(
                    timeout=5
                )

            except Exception:

                pass

        except Exception:

            pass

        finally:

            self.process = None