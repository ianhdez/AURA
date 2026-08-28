import re


class ToolParser:

    TOOL_PATTERN = re.compile(
        r"<tool>\s*(.*?)\s*</tool>",
        re.IGNORECASE | re.DOTALL
    )

    # ==================================================
    # PARSEAR
    # ==================================================

    def parse(
        self,
        text
    ):

        if not text:

            return None

        match = self.TOOL_PATTERN.search(
            str(text)
        )

        if not match:

            return None

        content = match.group(
            1
        ).strip()

        if not content:

            return None

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        if not lines:

            return None

        # ----------------------------------------------
        # Primera línea = nombre de herramienta
        # ----------------------------------------------

        name = lines[0].strip()

        # El modelo puede generar accidentalmente
        # espacios adicionales.
        name = re.sub(
            r"\s+",
            " ",
            name
        ).strip()

        parameters = {}

        # ----------------------------------------------
        # Parámetros
        # ----------------------------------------------

        for line in lines[1:]:

            if "=" not in line:

                continue

            key, value = line.split(
                "=",
                1
            )

            key = key.strip().lower()

            value = value.strip()

            if not key:

                continue

            # ------------------------------------------
            # Quitar comillas externas si el modelo
            # las añadió.
            # ------------------------------------------

            if (
                len(value) >= 2
                and (
                    (
                        value.startswith('"')
                        and value.endswith('"')
                    )
                    or
                    (
                        value.startswith("'")
                        and value.endswith("'")
                    )
                )
            ):

                value = value[1:-1]

            parameters[key] = value

        return {
            "name": name,
            "parameters": parameters
        }

    # ==================================================
    # ELIMINAR TOOL CALL
    # ==================================================

    def remove_tool_call(
        self,
        text
    ):

        if not text:

            return ""

        result = self.TOOL_PATTERN.sub(
            "",
            str(text)
        )

        return result.strip()

    # ==================================================
    # COMPROBAR SI EXISTE TOOL CALL
    # ==================================================

    def contains_tool_call(
        self,
        text
    ):

        if not text:

            return False

        return (
            self.TOOL_PATTERN.search(
                str(text)
            )
            is not None
        )