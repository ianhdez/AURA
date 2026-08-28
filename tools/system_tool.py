class SystemTool:

    name = "system"

    description = (
        "Consulta información real y actual del "
        "ordenador del usuario. Utiliza esta "
        "herramienta cuando necesites conocer "
        "hardware, Windows, almacenamiento o "
        "información actual del sistema."
    )

    parameters = {

        "componente": {

            "type": "string",

            "description": (
                "Información que se quiere consultar."
            ),

            "allowed_values": [
                "windows",
                "cpu",
                "ram",
                "gpu",
                "vram",
                "storage",
                "all"
            ]
        }
    }

    def __init__(
        self,
        system_context
    ):

        self.system_context = (
            system_context
        )

    # ==================================================
    # EJECUTAR
    # ==================================================

    def execute(
        self,
        componente="all",
        **kwargs
    ):

        componente = str(
            componente
        ).lower().strip()

        data = self.system_context.get()

        if componente == "all":

            return data

        if componente == "windows":

            return data[
                "windows"
            ]

        if componente == "cpu":

            return {
                "cpu": data[
                    "hardware"
                ][
                    "cpu"
                ]
            }

        if componente == "ram":

            return {
                "ram_gb": data[
                    "hardware"
                ][
                    "ram_gb"
                ]
            }

        if componente == "gpu":

            gpu = data[
                "hardware"
            ][
                "gpu"
            ]

            if isinstance(
                gpu,
                dict
            ):

                return {
                    "name": gpu.get(
                        "name"
                    )
                }

            return {
                "gpu": gpu
            }

        if componente == "vram":

            gpu = data[
                "hardware"
            ][
                "gpu"
            ]

            if isinstance(
                gpu,
                dict
            ):

                return {
                    "total_mb": gpu.get(
                        "vram_total_mb"
                    ),
                    "used_mb": gpu.get(
                        "vram_used_mb"
                    )
                }

            return {
                "vram": "No disponible"
            }

        if componente == "storage":

            return data[
                "storage"
            ]

        raise ValueError(
            f"Componente desconocido: "
            f"{componente}"
        )