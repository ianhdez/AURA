class EpisodicMemory:

    """
    Gestiona la memoria episódica de AURA.

    Una conversación representa una experiencia.

    Mantiene:

        conversación
        ├── mensajes
        ├── contexto
        ├── objetivo
        ├── decisiones
        ├── acciones
        ├── resultado
        └── aprendizaje

    El análisis detallado de la experiencia está delegado a
    EpisodeAnalyzer.
    """

    def __init__(
        self,
        store,
        config
    ):

        self.store = store

        self.config = config

        self.current_conversation_id = None

        self.analyzer = None

    # ==================================================
    # ANALIZADOR
    # ==================================================

    def attach_analyzer(
        self,
        analyzer
    ):

        self.analyzer = analyzer

    # ==================================================
    # INICIAR
    # ==================================================

    def start_conversation(
        self,
        title=None,
        metadata=None
    ):

        conversation_id = (
            self.store.create_conversation(
                title=title,
                metadata=metadata or {}
            )
        )

        self.current_conversation_id = (
            conversation_id
        )

        return conversation_id

    # ==================================================
    # FINALIZAR
    # ==================================================

    def end_conversation(
        self,
        title=None,
        summary=None,
        analyze=True
    ):

        conversation_id = (
            self.current_conversation_id
        )

        if not conversation_id:

            return None

        # --------------------------------------------------
        # Analizar antes de cerrar para que el contenido
        # completo esté disponible.
        # --------------------------------------------------

        episode = None

        if (
            analyze
            and
            self.analyzer is not None
        ):

            try:

                episode = (
                    self.analyzer
                    .analyze(
                        conversation_id
                    )
                )

                if (
                    not summary
                    and
                    episode
                ):

                    summary = (
                        episode
                        .get(
                            "episode",
                            {}
                        )
                        .get(
                            "summary"
                        )
                    )

            except Exception:

                episode = None

        self.store.end_conversation(
            conversation_id=conversation_id,
            title=title,
            summary=summary
        )

        self.current_conversation_id = None

        return {
            "conversation_id":
                conversation_id,

            "episode":
                episode
        }

    # ==================================================
    # MENSAJE
    # ==================================================

    def add_message(
        self,
        role,
        content,
        metadata=None
    ):

        conversation_id = (
            self.current_conversation_id
        )

        if not conversation_id:

            conversation_id = (
                self.start_conversation()
            )

        return self.store.add_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata or {}
        )

    # ==================================================
    # MENSAJES RECIENTES
    # ==================================================

    def recent_messages(
        self,
        limit=20
    ):

        conversation_id = (
            self.current_conversation_id
        )

        if not conversation_id:

            return []

        messages = (
            self.store
            .get_conversation_messages(
                conversation_id,
                limit=limit
            )
        )

        if len(
            messages
        ) <= limit:

            return messages

        return messages[
            -limit:
        ]

    # ==================================================
    # CONVERSACIÓN
    # ==================================================

    def get_conversation(
        self,
        conversation_id,
        limit=1000
    ):

        return self.store.get_conversation(
            conversation_id,
            limit
        )

    # ==================================================
    # CONVERSACIONES RECIENTES
    # ==================================================

    def recent_conversations(
        self,
        limit=10
    ):

        return self.store.list_conversations(
            limit
        )

    # ==================================================
    # BUSCAR
    # ==================================================

    def search(
        self,
        query,
        limit=10
    ):

        if not query:

            return []

        return self.store.search_conversations(
            query,
            limit
        )

    # ==================================================
    # BUSCAR EPISODIOS
    # ==================================================

    def search_episodes(
        self,
        query,
        limit=10
    ):

        if self.analyzer is None:

            return self.search(
                query,
                limit
            )

        return self.analyzer.search_episodes(
            query,
            limit
        )

    # ==================================================
    # EPISODIO
    # ==================================================

    def get_episode(
        self,
        conversation_id
    ):

        if self.analyzer is None:

            conversation = (
                self.get_conversation(
                    conversation_id
                )
            )

            if conversation is None:

                return None

            return {
                "conversation_id":
                    conversation_id,

                "started_at":
                    conversation.get(
                        "started_at"
                    ),

                "ended_at":
                    conversation.get(
                        "ended_at"
                    ),

                "title":
                    conversation.get(
                        "title"
                    ),

                "summary":
                    conversation.get(
                        "summary"
                    ),

                "episode":
                    {},

                "message_count":
                    len(
                        conversation.get(
                            "messages",
                            []
                        )
                    )
            }

        return self.analyzer.get_episode(
            conversation_id
        )

    # ==================================================
    # REGISTRAR EVENTO
    # ==================================================

    def record_event(
        self,
        content,
        importance=0.5,
        confidence=1.0,
        metadata=None
    ):

        event_metadata = dict(
            metadata or {}
        )

        event_metadata[
            "episodic_event"
        ] = True

        event_metadata[
            "importance"
        ] = importance

        event_metadata[
            "confidence"
        ] = confidence

        return self.add_message(
            role="event",
            content=content,
            metadata=event_metadata
        )

    # ==================================================
    # CREAR MEMORIA EPISÓDICA
    # ==================================================

    def create_episode_memory(
        self,
        conversation_id
    ):

        if self.analyzer is None:

            return None

        return self.analyzer.create_episode_memory(
            conversation_id
        )