from core.memory.memory_manager import MemoryManager


class MemoryTool:

    name = "memory"

    description = (
        "Gestiona la memoria persistente de AURA. "
        "Permite guardar, consultar, buscar, actualizar, "
        "eliminar y listar recuerdos. También permite "
        "consultar experiencias anteriores, patrones, "
        "predicciones y habilidades aprendidas. "
        "Toda la información se almacena localmente "
        "en la memoria central de AURA."
    )

    parameters = {
        "action": {
            "type": "string",
            "description": (
                "Acción a realizar: "
                "save, get, search, update, delete, "
                "list, episodes, episode, patterns, "
                "predictions, skills o skill."
            )
        },
        "key": {
            "type": "string",
            "description": (
                "Clave de la memoria."
            )
        },
        "value": {
            "type": "string",
            "description": (
                "Contenido de la memoria."
            )
        },
        "query": {
            "type": "string",
            "description": (
                "Texto que se desea buscar."
            )
        },
        "category": {
            "type": "string",
            "description": (
                "Categoría de la memoria."
            )
        },
        "memory_type": {
            "type": "string",
            "description": (
                "Tipo de memoria."
            )
        },
        "importance": {
            "type": "number",
            "description": (
                "Importancia entre 0 y 1."
            )
        },
        "confidence": {
            "type": "number",
            "description": (
                "Confianza entre 0 y 1."
            )
        },
        "limit": {
            "type": "integer",
            "description": (
                "Número máximo de resultados."
            )
        }
    }

    # ==================================================
    # INICIALIZACIÓN
    # ==================================================

    def __init__(
        self,
        memory
    ):

        # ==================================================
        # UTILIZAR MEMORY MANAGER EXISTENTE
        # ==================================================

        if isinstance(
            memory,
            MemoryManager
        ):

            self.memory = memory

            return

        # ==================================================
        # COMPATIBILIDAD CON RUTA
        # ==================================================

        self.memory = MemoryManager(
            memory
        )

    # ==================================================
    # EJECUTAR
    # ==================================================

    def execute(
        self,
        action="list",
        key=None,
        value=None,
        query=None,
        category=None,
        memory_type=None,
        importance=None,
        confidence=None,
        limit=None,
        **kwargs
    ):

        action = (
            str(
                action
                or "list"
            )
            .strip()
            .lower()
        )

        # ==================================================
        # NORMALIZAR VALORES
        # ==================================================

        importance = (
            self._number_or_none(
                importance
            )
        )

        confidence = (
            self._number_or_none(
                confidence
            )
        )

        if limit is None:

            limit = 20

        else:

            limit = self._integer(
                limit,
                20
            )

        # ==================================================
        # SAVE
        # ==================================================

        if action == "save":

            if key is None:

                return {
                    "saved": False,
                    "error":
                        "Se necesita 'key'."
                }

            if value is None:

                return {
                    "saved": False,
                    "error":
                        "Se necesita 'value'."
                }

            memory = (
                self.memory.remember(
                    content=value,
                    key=key,
                    memory_type=(
                        memory_type
                        or "general"
                    ),
                    category=(
                        category
                        or "general"
                    ),
                    importance=(
                        importance
                    ),
                    confidence=(
                        confidence
                    ),
                    source="user_explicit",
                    explicit=True
                )
            )

            if memory is None:

                return {
                    "saved": False
                }

            return {
                "saved": True,
                "memory": memory
            }

        # ==================================================
        # GET / RECALL
        # ==================================================

        if action in {
            "get",
            "recall"
        }:

            if key is None:

                return {
                    "found": False,
                    "error":
                        "Se necesita 'key'."
                }

            memory = (
                self.memory
                .recall(
                    key
                )
            )

            if memory is None:

                return {
                    "found": False,
                    "key": key
                }

            return {
                "found": True,
                "memory": memory
            }

        # ==================================================
        # SEARCH
        # ==================================================

        if action == "search":

            if query is None:

                return {
                    "found": False,
                    "results": []
                }

            results = (
                self.memory
                .search(
                    query=query,
                    limit=limit,
                    memory_type=memory_type
                )
            )

            return {
                "found": bool(
                    results
                ),
                "query": query,
                "results": results
            }

        # ==================================================
        # UPDATE
        # ==================================================

        if action == "update":

            if key is None:

                return {
                    "updated": False,
                    "error":
                        "Se necesita 'key'."
                }

            result = (
                self.memory
                .update(
                    key=key,
                    content=value,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence
                )
            )

            return result

        # ==================================================
        # DELETE / FORGET
        # ==================================================

        if action in {
            "delete",
            "forget"
        }:

            if key is None:

                return {
                    "deleted": False,
                    "error":
                        "Se necesita 'key'."
                }

            return (
                self.memory
                .forget(
                    key
                )
            )

        # ==================================================
        # LIST
        # ==================================================

        if action == "list":

            memories = (
                self.memory
                .list(
                    memory_type=memory_type,
                    limit=limit
                )
            )

            return {
                "count": len(
                    memories
                ),
                "memories":
                    memories
            }

        # ==================================================
        # EPISODIOS
        # ==================================================

        if action in {
            "episodes",
            "search_episodes"
        }:

            if query is None:

                episodes = (
                    self.memory
                    .recent_conversations(
                        limit=limit
                    )
                )

            else:

                episodes = (
                    self.memory
                    .search_episodes(
                        query,
                        limit=limit
                    )
                )

            return {
                "count": len(
                    episodes
                ),
                "episodes":
                    episodes
            }

        # ==================================================
        # EPISODIO
        # ==================================================

        if action in {
            "episode",
            "get_episode"
        }:

            if key is None:

                return {
                    "found": False,
                    "error":
                        "Se necesita el ID "
                        "de la conversación."
                }

            episode = (
                self.memory
                .get_episode(
                    key
                )
            )

            return {
                "found":
                    episode is not None,

                "episode":
                    episode
            }

        # ==================================================
        # PATRONES
        # ==================================================

        if action in {
            "patterns",
            "list_patterns"
        }:

            patterns = (
                self.memory
                .list_patterns(
                    limit=limit
                )
            )

            return {
                "count": len(
                    patterns
                ),
                "patterns":
                    patterns
            }

        # ==================================================
        # PREDICCIONES
        # ==================================================

        if action in {
            "predictions",
            "list_predictions"
        }:

            predictions = (
                self.memory
                .active_predictions(
                    limit=limit
                )
            )

            return {
                "count": len(
                    predictions
                ),
                "predictions":
                    predictions
            }

        # ==================================================
        # PREDECIR
        # ==================================================

        if action == "predict":

            predictions = (
                self.memory
                .predict(
                    query=query,
                    limit=limit
                )
            )

            return {
                "count": len(
                    predictions
                ),
                "predictions":
                    predictions
            }

        # ==================================================
        # HABILIDADES
        # ==================================================

        if action in {
            "skills",
            "list_skills"
        }:

            skills = (
                self.memory
                .list_skills(
                    limit=limit,
                    category=category
                )
            )

            return {
                "count": len(
                    skills
                ),
                "skills":
                    skills
            }

        # ==================================================
        # HABILIDAD
        # ==================================================

        if action in {
            "skill",
            "get_skill"
        }:

            if key is None:

                return {
                    "found": False,
                    "error":
                        "Se necesita "
                        "'key'."
                }

            skill = (
                self.memory
                .get_skill(
                    key
                )
            )

            return {
                "found":
                    skill is not None,

                "skill":
                    skill
            }

        # ==================================================
        # ESTADO
        # ==================================================

        if action in {
            "status",
            "state"
        }:

            return (
                self.memory
                .get_status()
            )

        # ==================================================
        # ESTADÍSTICAS
        # ==================================================

        if action in {
            "statistics",
            "stats"
        }:

            return {
                "profile":
                    self.memory
                    .get_profile_statistics(),

                "predictions":
                    self.memory
                    .prediction_statistics(),

                "procedural":
                    self.memory
                    .procedural_statistics()
            }

        # ==================================================
        # ACCIÓN DESCONOCIDA
        # ==================================================

        return {
            "success": False,
            "error":
                (
                    "Acción de memoria desconocida: "
                    +
                    action
                )
        }

    # ==================================================
    # CONVERSIÓN NUMÉRICA
    # ==================================================

    @staticmethod
    def _number_or_none(
        value
    ):

        if value is None:

            return None

        if isinstance(
            value,
            bool
        ):

            return None

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return None

    @staticmethod
    def _integer(
        value,
        default
    ):

        try:

            return max(
                1,
                int(
                    value
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return default