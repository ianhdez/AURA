class ConversationManager:

    def __init__(
        self,
        max_messages=10,
        memory_manager=None
    ):

        self.messages = []

        self.max_messages = (
            max_messages
        )

        self.memory_manager = (
            memory_manager
        )

        self.conversation_id = None

    # ==================================================
    # INICIAR
    # ==================================================

    def start(
        self,
        title=None,
        metadata=None
    ):

        self.messages.clear()

        self.conversation_id = None

        if self.memory_manager is not None:

            self.conversation_id = (
                self.memory_manager
                .start_conversation(
                    title=title,
                    metadata=metadata
                )
            )

        return self.conversation_id

    # ==================================================
    # USUARIO
    # ==================================================

    def add_user_message(
        self,
        content
    ):

        content = str(
            content
        )

        self.messages.append({
            "role": "user",
            "content": content
        })

        self._persist(
            "user",
            content
        )

    # ==================================================
    # AURA
    # ==================================================

    def add_assistant_message(
        self,
        content
    ):

        content = str(
            content
        )

        self.messages.append({
            "role": "assistant",
            "content": content
        })

        self._persist(
            "assistant",
            content
        )

    # ==================================================
    # PERSISTENCIA
    # ==================================================

    def _persist(
        self,
        role,
        content
    ):

        if self.memory_manager is None:

            return

        try:

            self.memory_manager.add_conversation_message(
                role,
                content
            )

        except Exception:

            pass

    # ==================================================
    # CONTEXTO ACTUAL
    # ==================================================

    def get_messages(
        self
    ):

        if len(
            self.messages
        ) <= self.max_messages:

            return self.messages.copy()

        return self.messages[
            -self.max_messages:
        ].copy()

    # ==================================================
    # HISTORIAL DE SESIÓN
    # ==================================================

    def get_all_messages(
        self
    ):

        return self.messages.copy()

    # ==================================================
    # ÚLTIMO USUARIO
    # ==================================================

    def get_last_user_message(
        self,
        exclude_current=True
    ):

        messages = self.messages

        if exclude_current:

            messages = messages[:-1]

        for message in reversed(
            messages
        ):

            if message["role"] == "user":

                return message["content"]

        return None

    # ==================================================
    # ÚLTIMO AURA
    # ==================================================

    def get_last_assistant_message(
        self
    ):

        for message in reversed(
            self.messages
        ):

            if message["role"] == "assistant":

                return message["content"]

        return None

    # ==================================================
    # ÚLTIMO MENSAJE
    # ==================================================

    def get_last_message(
        self
    ):

        if not self.messages:

            return None

        return self.messages[
            -1
        ].copy()

    # ==================================================
    # FINALIZAR
    # ==================================================

    def end(
        self,
        title=None,
        summary=None
    ):

        if self.memory_manager is not None:

            try:

                self.memory_manager.end_conversation(
                    title=title,
                    summary=summary
                )

            except Exception:

                pass

        self.conversation_id = None

    # ==================================================
    # LIMPIAR CONTEXTO
    # ==================================================

    def clear(
        self
    ):

        self.messages.clear()

    # ==================================================
    # INFORMACIÓN
    # ==================================================

    def count(
        self
    ):

        return len(
            self.messages
        )

    def get_conversation_id(
        self
    ):

        return self.conversation_id