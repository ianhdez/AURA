class ToolExecutor:

    def __init__(
        self,
        tool_manager
    ):

        self.tool_manager = (
            tool_manager
        )

    # ==================================================
    # EJECUTAR
    # ==================================================

    def execute(
        self,
        tool_call
    ):

        if not tool_call:

            return {
                "success": False,
                "error": (
                    "No se recibió ninguna "
                    "herramienta."
                )
            }

        name = str(
            tool_call.get(
                "name",
                ""
            )
        ).strip()

        parameters = tool_call.get(
            "parameters",
            {}
        )

        if not isinstance(
            parameters,
            dict
        ):

            parameters = {}

        if not name:

            return {
                "success": False,
                "error": (
                    "No se especificó "
                    "el nombre de la herramienta."
                )
            }

        if name not in (
            self.tool_manager.list_tools()
        ):

            return {
                "success": False,
                "tool": name,
                "error": (
                    f"Herramienta no disponible: "
                    f"{name}"
                )
            }

        try:

            result = (
                self.tool_manager.execute(
                    name,
                    **parameters
                )
            )

            return {
                "success": True,
                "tool": name,
                "result": result
            }

        except Exception as error:

            return {
                "success": False,
                "tool": name,
                "error": str(error)
            }