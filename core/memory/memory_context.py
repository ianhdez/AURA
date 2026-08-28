import json


class MemoryContextBuilder:

    """
    Construye un contexto compacto y útil para el modelo.

    No envía toda la base de datos al LLM.

    Solamente incluye la información relevante para la
    conversación actual.
    """

    def __init__(
        self,
        config
    ):

        self.config = config

    # ==================================================
    # CONSTRUIR
    # ==================================================

    def build(
        self,
        memories=None,
        episodes=None,
        relations=None,
        conversations=None
    ):

        memories = memories or []
        episodes = episodes or []
        relations = relations or []
        conversations = conversations or []

        sections = []

        # --------------------------------------------------
        # MEMORIA PERSONAL
        # --------------------------------------------------

        if memories:

            sections.append(
                self._memory_section(
                    memories
                )
            )

        # --------------------------------------------------
        # EPISODIOS
        # --------------------------------------------------

        if episodes:

            sections.append(
                self._episode_section(
                    episodes
                )
            )

        # --------------------------------------------------
        # CONVERSACIONES
        # --------------------------------------------------

        if conversations:

            sections.append(
                self._conversation_section(
                    conversations
                )
            )

        # --------------------------------------------------
        # RELACIONES
        # --------------------------------------------------

        if relations:

            sections.append(
                self._relation_section(
                    relations
                )
            )

        if not sections:

            return ""

        return (
            "MEMORIA RELEVANTE DE AURA\n"
            "==========================\n\n"
            +
            "\n\n".join(
                sections
            )
            +
            "\n\nFIN DE MEMORIA RELEVANTE"
        )

    # ==================================================
    # MEMORIAS
    # ==================================================

    def _memory_section(
        self,
        memories
    ):

        lines = [
            "RECUERDOS:"
        ]

        for memory in memories[
            :self.config.MAX_MEMORY_CONTEXT_ITEMS
        ]:

            key = (
                memory.get(
                    "memory_key"
                )
                or
                memory.get(
                    "key"
                )
                or
                "sin_clave"
            )

            content = memory.get(
                "content",
                ""
            )

            memory_type = memory.get(
                "memory_type",
                "general"
            )

            confidence = memory.get(
                "confidence",
                1.0
            )

            lines.append(
                "- "
                f"[{memory_type}] "
                f"{key}: "
                f"{content} "
                f"(confianza: "
                f"{float(confidence):.2f})"
            )

        return "\n".join(
            lines
        )

    # ==================================================
    # EPISODIOS
    # ==================================================

    def _episode_section(
        self,
        episodes
    ):

        lines = [
            "EXPERIENCIAS / EPISODIOS:"
        ]

        for episode in episodes[
            :self.config.MAX_EPISODIC_CONTEXT_ITEMS
        ]:

            content = episode.get(
                "content",
                ""
            )

            timestamp = (
                episode.get(
                    "created_at"
                )
                or
                episode.get(
                    "timestamp"
                )
                or
                ""
            )

            if timestamp:

                lines.append(
                    f"- {timestamp}: "
                    f"{content}"
                )

            else:

                lines.append(
                    f"- {content}"
                )

        return "\n".join(
            lines
        )

    # ==================================================
    # CONVERSACIONES
    # ==================================================

    def _conversation_section(
        self,
        conversations
    ):

        lines = [
            "CONVERSACIONES ANTERIORES:"
        ]

        for item in conversations[
            :self.config.MAX_CONVERSATION_CONTEXT_ITEMS
        ]:

            role = item.get(
                "role",
                ""
            )

            content = item.get(
                "content",
                ""
            )

            timestamp = item.get(
                "created_at",
                ""
            )

            prefix = (
                f"{timestamp} "
                if timestamp
                else ""
            )

            lines.append(
                f"- {prefix}"
                f"{role}: "
                f"{content}"
            )

        return "\n".join(
            lines
        )

    # ==================================================
    # RELACIONES
    # ==================================================

    def _relation_section(
        self,
        relations
    ):

        lines = [
            "RELACIONES ENTRE RECUERDOS:"
        ]

        for relation in relations[
            :self.config.MAX_RELATED_MEMORY_ITEMS
        ]:

            source = relation.get(
                "source_id",
                ""
            )

            target = relation.get(
                "target_id",
                ""
            )

            relation_type = relation.get(
                "relation",
                "related"
            )

            weight = relation.get(
                "weight",
                1.0
            )

            lines.append(
                "- "
                f"{source} "
                f"--{relation_type}--> "
                f"{target} "
                f"(peso: {float(weight):.2f})"
            )

        return "\n".join(
            lines
        )