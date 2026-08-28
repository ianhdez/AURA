from pathlib import Path
import json

from backends.llama_cpp.backend import LlamaCppBackend


class ModelManager:

    def __init__(self):

        self.base_dir = (
            Path(__file__).resolve().parent.parent
        )

        self.config = self._load_config()

        self.backend = None

        self.system_prompt = (
            self._load_system_prompt()
        )

    # ==================================================
    # CONFIGURACIÓN
    # ==================================================

    def _load_config(self):

        config_path = (
            self.base_dir
            / "config"
            / "model.json"
        )

        if not config_path.exists():

            raise FileNotFoundError(
                f"Configuración no encontrada: "
                f"{config_path}"
            )

        with open(
            config_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    # ==================================================
    # SYSTEM PROMPT
    # ==================================================

    def _load_system_prompt(self):

        prompt_path = (
            self.base_dir
            / "config"
            / "system_prompt.txt"
        )

        if not prompt_path.exists():

            raise FileNotFoundError(
                f"System prompt no encontrado: "
                f"{prompt_path}"
            )

        return prompt_path.read_text(
            encoding="utf-8"
        ).strip()

    # ==================================================
    # CARGAR
    # ==================================================

    def load(self):

        backend_name = self.config[
            "backend"
        ]

        if backend_name != "llama_cpp":

            raise ValueError(
                f"Backend no compatible: "
                f"{backend_name}"
            )

        model_path = (
            self.base_dir
            / "models"
            / self.config["model"]
            / "Qwen3-8B-Q4_K_M.gguf"
        )

        executable_path = (
            self.base_dir
            / "backends"
            / "llama_cpp"
            / "bin"
            / "llama-server.exe"
        )

        self.backend = LlamaCppBackend(
            model_path=model_path,
            executable_path=executable_path,
            context_size=self.config.get(
                "context_size",
                8192
            )
        )

        self.backend.load()

    # ==================================================
    # DESCARGAR
    # ==================================================

    def unload(self):

        if self.backend is not None:

            self.backend.unload()

            self.backend = None

    # ==================================================
    # GENERAR
    # ==================================================

    def generate(
        self,
        messages,
        max_tokens=None,
        temperature=None,
        tools=None
    ):

        if self.backend is None:

            raise RuntimeError(
                "No hay ningún modelo cargado."
            )

        full_messages = [
            {
                "role": "system",
                "content": self.system_prompt
            }
        ]

        if tools:

            tool_prompt = (
                self._build_tool_prompt(
                    tools
                )
            )

            full_messages.append({
                "role": "system",
                "content": tool_prompt
            })

        full_messages.extend(
            messages
        )

        if max_tokens is None:

            max_tokens = self.config.get(
                "max_tokens",
                300
            )

        if temperature is None:

            temperature = self.config.get(
                "temperature",
                0.65
            )

        return self.backend.generate(
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

    # ==================================================
    # PROMPT DE HERRAMIENTAS
    # ==================================================

    def _build_tool_prompt(
        self,
        tools
    ):

        lines = [
            "HERRAMIENTAS DISPONIBLES:",
            "",
            "Las herramientas son capacidades reales "
            "de AURA.",
            "",
            "Una herramienta no debe utilizarse "
            "simplemente porque una palabra del mensaje "
            "parezca relacionada.",
            "",
            "Primero interpreta la intención del usuario.",
            "",
            "REGLAS FUNDAMENTALES:",
            "",
            "1. Conversa normalmente cuando no sea "
            "necesaria una herramienta.",
            "",
            "2. Utiliza una herramienta solamente cuando "
            "la acción o consulta corresponda realmente "
            "a lo que el usuario quiere.",
            "",
            "3. No inventes resultados.",
            "",
            "4. No ejecutes código.",
            "",
            "5. Solo puedes utilizar las herramientas "
            "disponibles.",
            "",
            "6. Si la intención del usuario es ambigua, "
            "no ejecutes una acción irreversible. "
            "Primero conversa y aclara.",
            "",
            "7. Especialmente con memory: una afirmación "
            "sobre un cambio de opinión no significa "
            "automáticamente que debas modificar o "
            "eliminar una memoria.",
            "",
            "8. Si el usuario simplemente dice que algo "
            "ya no le gusta, no borres automáticamente "
            "el recuerdo. Comprende primero qué quiere "
            "hacer con él.",
            "",
            "9. Si el usuario confirma claramente que "
            "quiere guardar, actualizar o eliminar "
            "información, entonces utiliza memory.",
            "",
            "10. Después de recibir un TOOL RESULT, "
            "utiliza únicamente sus datos.",
            "",
            "11. Responde como AURA, no como una herramienta.",
            "",
            "12. No muestres etiquetas internas.",
            "",
            "13. Mantén una conversación natural y "
            "coherente.",
            "",
            "14. Evita respuestas prefabricadas y repetitivas.",
            "",
            "FORMATO PARA UTILIZAR UNA HERRAMIENTA:",
            "",
            "<tool>",
            "nombre_de_herramienta",
            "parametro=valor",
            "</tool>",
            "",
            "Si no necesitas ninguna herramienta, "
            "responde directamente."
        ]

        for tool in tools:

            lines.append(
                f"- {tool['name']}: "
                f"{tool['description']}"
            )

        return "\n".join(
            lines
        )

    # ==================================================
    # ESTADO
    # ==================================================

    def get_status(self):

        if self.backend is None:

            return {
                "loaded": False
            }

        return self.backend.get_status()