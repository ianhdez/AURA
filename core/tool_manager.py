class ToolManager:

    def __init__(self):

        self.tools = {}

    # ==================================================
    # REGISTRAR
    # ==================================================

    def register(
        self,
        name,
        tool
    ):

        name = str(
            name
        ).strip()

        if not name:

            raise ValueError(
                "El nombre de la herramienta "
                "no puede estar vacío."
            )

        self.tools[name] = tool

    # ==================================================
    # OBTENER
    # ==================================================

    def get(
        self,
        name
    ):

        return self.tools.get(
            name
        )

    # ==================================================
    # LISTAR
    # ==================================================

    def list_tools(self):

        return list(
            self.tools.keys()
        )

    # ==================================================
    # DESCRIPCIONES
    # ==================================================

    def get_descriptions(self):

        descriptions = []

        for name, tool in (
            self.tools.items()
        ):

            description = {
                "name": name,

                "description": (
                    getattr(
                        tool,
                        "description",
                        ""
                    )
                )
            }

            if hasattr(
                tool,
                "parameters"
            ):

                description["parameters"] = (
                    tool.parameters
                )

            descriptions.append(
                description
            )

        return descriptions

    # ==================================================
    # EJECUTAR
    # ==================================================

    def execute(
        self,
        name,
        **kwargs
    ):

        tool = self.get(
            name
        )

        if tool is None:

            raise ValueError(
                f"Herramienta no encontrada: "
                f"{name}"
            )

        return tool.execute(
            **kwargs
        )