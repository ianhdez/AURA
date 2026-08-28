import json


class EpisodeAnalyzer:

    """
    Analiza conversaciones completas para convertirlas en
    experiencias episódicas estructuradas.

    Una conversación puede contener:

        contexto
        objetivo
        problema
        decisiones
        acciones
        resultado
        errores
        solución
        aprendizaje
        consecuencias

    El resultado se guarda como metadatos de la conversación
    y también puede utilizarse para crear una memoria episódica
    resumida.

    No sustituye a la conversación original.
    """

    def __init__(
        self,
        memory_manager,
        model=None
    ):

        self.memory = (
            memory_manager
        )

        self.store = (
            memory_manager.store
        )

        self.config = (
            memory_manager.config
        )

        self.model = model

    # ==================================================
    # ANALIZAR
    # ==================================================

    def analyze(
        self,
        conversation_id,
        force=False
    ):

        conversation = (
            self.store.get_conversation(
                conversation_id,
                limit=(
                    self.config
                    .EPISODIC_MAX_MESSAGES_PER_EPISODE
                )
            )
        )

        if not conversation:

            return None

        metadata = dict(
            conversation.get(
                "metadata",
                {}
            )
            or {}
        )

        if (
            metadata.get(
                "episode_analyzed",
                False
            )
            and
            not force
        ):

            return {
                "conversation_id":
                    conversation_id,

                "episode":
                    metadata.get(
                        "episode",
                        {}
                    )
            }

        messages = conversation.get(
            "messages",
            []
        )

        if not messages:

            return None

        if self.model is None:

            episode = (
                self._heuristic_analysis(
                    messages
                )
            )

        else:

            episode = (
                self._model_analysis(
                    messages
                )
            )

        if not episode:

            return None

        metadata[
            "episode_analyzed"
        ] = True

        metadata[
            "episode"
        ] = episode

        metadata[
            "episode_version"
        ] = 1

        self.store.update_conversation(
            conversation_id,
            metadata=metadata,
            summary=episode.get(
                "summary"
            )
        )

        return {
            "conversation_id":
                conversation_id,

            "episode":
                episode
        }

    # ==================================================
    # ANÁLISIS CON MODELO
    # ==================================================

    def _model_analysis(
        self,
        messages
    ):

        compact = []

        for message in messages:

            role = str(
                message.get(
                    "role",
                    ""
                )
            )

            content = str(
                message.get(
                    "content",
                    ""
                )
            ).strip()

            if not content:

                continue

            # Los resultados internos de herramientas no son
            # experiencia conversacional directa.
            if content.startswith(
                "TOOL RESULT"
            ):

                continue

            compact.append(
                {
                    "role":
                        role,

                    "content":
                        content
                }
            )

        if not compact:

            return None

        prompt = f"""
Eres el analizador de memoria episódica de AURA.

Debes reconstruir una EXPERIENCIA completa a partir de una
conversación.

No debes responder al usuario.

No debes inventar acontecimientos.

La conversación puede contener conversaciones normales,
problemas técnicos, proyectos, decisiones y tareas.

Debes distinguir entre:

- lo que el usuario quería conseguir;
- lo que realmente ocurrió;
- lo que se intentó;
- lo que funcionó;
- lo que falló;
- qué decisiones se tomaron;
- qué resultado se obtuvo;
- qué aprendizaje puede reutilizarse.

CONVERSACIÓN:

{json.dumps(
    compact,
    ensure_ascii=False,
    indent=2
)}

FORMATO:

{{
    "summary": "resumen breve de la experiencia",
    "context": "contexto relevante",
    "goal": "objetivo principal",
    "problem": "problema o necesidad inicial",
    "decisions": [
        "decisión"
    ],
    "actions": [
        "acción realizada"
    ],
    "tools": [
        "herramienta, programa o recurso utilizado"
    ],
    "changes": [
        "cambio realizado"
    ],
    "errors": [
        "error o intento fallido"
    ],
    "solution": "solución alcanzada",
    "outcome": "resultado final",
    "lessons": [
        "aprendizaje reutilizable"
    ],
    "consequences": [
        "consecuencia posterior conocida"
    ],
    "entities": [
        {{
            "name": "entidad",
            "type": "project|software|file|concept|task|other"
        }}
    ]
}}

REGLAS:

- No inventes resultados.
- Si no existe un objetivo claro, utiliza una cadena vacía.
- Si no hubo errores, devuelve [].
- Si no hubo solución, no inventes una.
- "lesson" debe ser algo reutilizable, no una simple repetición.
- Las consecuencias solo deben incluirse cuando estén respaldadas.
- No conviertas una posibilidad en un hecho.
- Mantén el resumen compacto.

Devuelve únicamente JSON válido.
"""

        try:

            response = self.model.generate(
                [
                    {
                        "role": "system",
                        "content": prompt
                    },
                    {
                        "role": "user",
                        "content":
                            "Analiza esta experiencia."
                    }
                ],
                tools=[]
            )

        except Exception:

            return None

        return self._parse_json(
            response
        )

    # ==================================================
    # ANÁLISIS SIN MODELO
    # ==================================================

    def _heuristic_analysis(
        self,
        messages
    ):

        user_messages = []

        assistant_messages = []

        for message in messages:

            role = str(
                message.get(
                    "role",
                    ""
                )
            )

            content = str(
                message.get(
                    "content",
                    ""
                )
            ).strip()

            if not content:

                continue

            if role == "user":

                user_messages.append(
                    content
                )

            elif role == "assistant":

                if not content.startswith(
                    "TOOL RESULT"
                ):

                    assistant_messages.append(
                        content
                    )

        if not user_messages:

            return {
                "summary": "",
                "context": "",
                "goal": "",
                "problem": "",
                "decisions": [],
                "actions": [],
                "tools": [],
                "changes": [],
                "errors": [],
                "solution": "",
                "outcome": "",
                "lessons": [],
                "consequences": [],
                "entities": []
            }

        summary = (
            user_messages[0][:500]
        )

        return {
            "summary":
                summary,

            "context":
                "",

            "goal":
                user_messages[0][:500],

            "problem":
                "",

            "decisions":
                [],

            "actions":
                [],

            "tools":
                [],

            "changes":
                [],

            "errors":
                [],

            "solution":
                "",

            "outcome":
                assistant_messages[-1][:500]
                if assistant_messages
                else "",

            "lessons":
                [],

            "consequences":
                [],

            "entities":
                []
        }

    # ==================================================
    # CREAR MEMORIA EPISÓDICA
    # ==================================================

    def create_episode_memory(
        self,
        conversation_id
    ):

        analysis = self.analyze(
            conversation_id
        )

        if not analysis:

            return None

        episode = analysis.get(
            "episode",
            {}
        )

        summary = str(
            episode.get(
                "summary",
                ""
            )
        ).strip()

        if not summary:

            return None

        metadata = {
            "episodic_memory":
                True,

            "conversation_id":
                conversation_id,

            "episode":
                episode
        }

        memory = (
            self.memory.remember(
                content=summary,
                key=None,
                memory_type="episodic",
                category="episode",
                importance=0.65,
                confidence=0.90,
                source="conversation",
                metadata=metadata,
                create_associations=False,
                explicit=False
            )
        )

        if not memory:

            return None

        # Relacionamos el episodio con entidades que ya existan.

        for entity in episode.get(
            "entities",
            []
        ):

            if not isinstance(
                entity,
                dict
            ):

                continue

            name = str(
                entity.get(
                    "name",
                    ""
                )
            ).strip()

            if not name:

                continue

            try:

                matches = (
                    self.memory.search(
                        name,
                        limit=3
                    )
                )

            except Exception:

                matches = []

            for match in matches:

                target_id = (
                    match.get(
                        "id"
                    )
                )

                if not target_id:

                    continue

                if target_id == memory.get(
                    "id"
                ):

                    continue

                try:

                    self.store.add_relation(
                        memory["id"],
                        target_id,
                        "episode_mentions",
                        weight=0.65
                    )

                except Exception:

                    pass

                break

        return memory

    # ==================================================
    # OBTENER EXPERIENCIA
    # ==================================================

    def get_episode(
        self,
        conversation_id
    ):

        conversation = (
            self.store.get_conversation(
                conversation_id,
                limit=(
                    self.config
                    .EPISODIC_MAX_MESSAGES_PER_EPISODE
                )
            )
        )

        if not conversation:

            return None

        metadata = dict(
            conversation.get(
                "metadata",
                {}
            )
            or {}
        )

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
                metadata.get(
                    "episode",
                    {}
                ),

            "message_count":
                len(
                    conversation.get(
                        "messages",
                        []
                    )
                )
        }

    # ==================================================
    # EXPERIENCIAS RELEVANTES
    # ==================================================

    def search_episodes(
        self,
        query,
        limit=10
    ):

        if not query:

            return []

        results = (
            self.memory.search_conversations(
                query,
                limit=(
                    max(
                        limit * 3,
                        20
                    )
                )
            )
        )

        unique = {}

        for result in results:

            conversation_id = (
                result.get(
                    "conversation_id"
                )
            )

            if not conversation_id:

                continue

            if conversation_id in unique:

                continue

            episode = (
                self.get_episode(
                    conversation_id
                )
            )

            if episode is None:

                continue

            unique[
                conversation_id
            ] = episode

            if len(
                unique
            ) >= limit:

                break

        return list(
            unique.values()
        )

    # ==================================================
    # PARSE
    # ==================================================

    @staticmethod
    def _parse_json(
        response
    ):

        if not response:

            return None

        text = str(
            response
        ).strip()

        try:

            data = json.loads(
                text
            )

            return (
                data
                if isinstance(
                    data,
                    dict
                )
                else None
            )

        except Exception:

            pass

        start = text.find(
            "{"
        )

        end = text.rfind(
            "}"
        )

        if (
            start < 0
            or
            end <= start
        ):

            return None

        try:

            data = json.loads(
                text[
                    start:
                    end + 1
                ]
            )

            return (
                data
                if isinstance(
                    data,
                    dict
                )
                else None
            )

        except Exception:

            return None