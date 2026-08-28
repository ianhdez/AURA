from datetime import datetime


class UserProfile:

    """
    Construye un perfil dinámico del usuario a partir de las
    memorias persistentes y de la memoria de trabajo.

    El perfil NO sustituye a las memorias.

    Las memorias son la fuente de verdad.

    El perfil es una representación resumida y estructurada
    que facilita que AURA comprenda rápidamente:

    - preferencias
    - información personal
    - hábitos
    - intereses
    - habilidades
    - conocimientos
    - proyectos
    - objetivos
    - patrones
    - contexto actual

    No contiene datos inventados.

    No guarda una copia independiente de las memorias.
    """

    PROFILE_TYPES = {
        "personal": "personal",
        "preference": "preferences",
        "habit": "habits",
        "skill": "skills",
        "knowledge": "knowledge",
        "project": "projects",
        "pattern": "patterns",
        "prediction": "predictions",
        "semantic": "knowledge",
        "general": "general",
        "contextual": "context"
    }

    def __init__(
        self,
        memory_manager
    ):

        self.memory = (
            memory_manager
        )

        self.config = (
            memory_manager.config
        )

    # ==================================================
    # CONSTRUIR
    # ==================================================

    def build(
        self,
        include_predictions=False,
        include_patterns=True
    ):

        memories = (
            self.memory.list(
                limit=10000
            )
        )

        profile = {
            "personal": [],
            "preferences": [],
            "habits": [],
            "skills": [],
            "knowledge": [],
            "projects": [],
            "patterns": [],
            "predictions": [],
            "general": [],
            "context": []
        }

        for memory in memories:

            memory_type = str(
                memory.get(
                    "memory_type",
                    "general"
                )
            ).lower()

            if (
                memory_type == "prediction"
                and
                not include_predictions
            ):

                continue

            if (
                memory_type == "pattern"
                and
                not include_patterns
            ):

                continue

            target = (
                self.PROFILE_TYPES.get(
                    memory_type,
                    "general"
                )
            )

            item = self._clean_memory(
                memory
            )

            if item:

                profile[
                    target
                ].append(
                    item
                )

        # --------------------------------------------------
        # Memoria de trabajo actual
        # --------------------------------------------------

        profile["context"] = (
            self._build_current_context()
        )

        # --------------------------------------------------
        # Ordenar por importancia / confianza
        # --------------------------------------------------

        for category, items in profile.items():

            if not isinstance(
                items,
                list
            ):

                continue

            items.sort(
                key=lambda item: (
                    item.get(
                        "importance",
                        0.0
                    ),
                    item.get(
                        "confidence",
                        0.0
                    ),
                    item.get(
                        "updated_at",
                        ""
                    )
                ),
                reverse=True
            )

        return profile

    # ==================================================
    # CONTEXTO ACTUAL
    # ==================================================

    def _build_current_context(
        self
    ):

        state = (
            self.memory
            .get_working_memory()
        )

        if not state:

            return []

        result = []

        if state.get(
            "topic"
        ):

            result.append({
                "type": "topic",
                "content": state[
                    "topic"
                ]
            })

        if state.get(
            "goal"
        ):

            result.append({
                "type": "goal",
                "content": state[
                    "goal"
                ]
            })

        if state.get(
            "task"
        ):

            result.append({
                "type": "task",
                "content": state[
                    "task"
                ],
                "state": state.get(
                    "task_state"
                )
            })

        return result

    # ==================================================
    # LIMPIAR MEMORIA
    # ==================================================

    @staticmethod
    def _clean_memory(
        memory
    ):

        if not memory:

            return None

        status = memory.get(
            "status",
            "active"
        )

        if status != "active":

            return None

        content = str(
            memory.get(
                "content",
                ""
            )
        ).strip()

        if not content:

            return None

        return {
            "id": memory.get(
                "id"
            ),

            "key": (
                memory.get(
                    "memory_key"
                )
                or
                memory.get(
                    "key"
                )
            ),

            "content": content,

            "memory_type":
                memory.get(
                    "memory_type",
                    "general"
                ),

            "category":
                memory.get(
                    "category",
                    "general"
                ),

            "importance":
                float(
                    memory.get(
                        "importance",
                        0.5
                    )
                ),

            "confidence":
                float(
                    memory.get(
                        "confidence",
                        1.0
                    )
                ),

            "updated_at":
                memory.get(
                    "updated_at",
                    ""
                )
        }

    # ==================================================
    # RESUMEN PARA AURA
    # ==================================================

    def build_context(
        self,
        max_chars=5000,
        include_predictions=False,
        include_patterns=True
    ):

        profile = self.build(
            include_predictions=(
                include_predictions
            ),
            include_patterns=(
                include_patterns
            )
        )

        lines = []

        lines.append(
            "PERFIL DINÁMICO DEL USUARIO"
        )

        lines.append(
            "============================"
        )

        self._append_section(
            lines,
            "INFORMACIÓN PERSONAL",
            profile["personal"]
        )

        self._append_section(
            lines,
            "PREFERENCIAS",
            profile["preferences"]
        )

        self._append_section(
            lines,
            "HÁBITOS",
            profile["habits"]
        )

        self._append_section(
            lines,
            "HABILIDADES",
            profile["skills"]
        )

        self._append_section(
            lines,
            "CONOCIMIENTOS",
            profile["knowledge"]
        )

        self._append_section(
            lines,
            "PROYECTOS",
            profile["projects"]
        )

        self._append_section(
            lines,
            "PATRONES",
            profile["patterns"]
        )

        if include_predictions:

            self._append_section(
                lines,
                "PREDICCIONES",
                profile["predictions"]
            )

        self._append_section(
            lines,
            "INFORMACIÓN GENERAL",
            profile["general"]
        )

        # --------------------------------------------------
        # Contexto actual
        # --------------------------------------------------

        if profile["context"]:

            lines.append(
                ""
            )

            lines.append(
                "CONTEXTO ACTUAL"
            )

            for item in profile["context"]:

                content = item.get(
                    "content",
                    ""
                )

                if item.get(
                    "state"
                ):

                    content += (
                        " "
                        "Estado: "
                        +
                        str(
                            item["state"]
                        )
                    )

                lines.append(
                    "- "
                    + content
                )

        context = "\n".join(
            lines
        )

        if len(
            context
        ) <= max_chars:

            return context

        return (
            context[
                :max_chars
            ]
            +
            "\n\n[PERFIL RECORTADO]"
        )

    # ==================================================
    # SECCIÓN
    # ==================================================

    @staticmethod
    def _append_section(
        lines,
        title,
        items
    ):

        if not items:

            return

        lines.append(
            ""
        )

        lines.append(
            title
        )

        for item in items:

            key = item.get(
                "key"
            )

            content = item.get(
                "content",
                ""
            )

            if key:

                text = (
                    f"{key}: "
                    f"{content}"
                )

            else:

                text = content

            confidence = item.get(
                "confidence",
                1.0
            )

            if confidence < 0.70:

                text += (
                    " "
                    f"(confianza "
                    f"{confidence:.2f})"
                )

            lines.append(
                "- "
                + text
            )

    # ==================================================
    # CONSULTAS RÁPIDAS
    # ==================================================

    def preferences(
        self
    ):

        profile = self.build()

        return profile[
            "preferences"
        ]

    def projects(
        self
    ):

        profile = self.build()

        return profile[
            "projects"
        ]

    def habits(
        self
    ):

        profile = self.build()

        return profile[
            "habits"
        ]

    def skills(
        self
    ):

        profile = self.build()

        return profile[
            "skills"
        ]

    def knowledge(
        self
    ):

        profile = self.build()

        return profile[
            "knowledge"
        ]

    # ==================================================
    # ESTADÍSTICAS
    # ==================================================

    def statistics(
        self
    ):

        profile = self.build(
            include_predictions=True
        )

        return {
            key: len(
                value
            )
            for key, value in profile.items()
        }

    # ==================================================
    # EXPORTAR
    # ==================================================

    def to_dict(
        self
    ):

        return self.build(
            include_predictions=True
        )