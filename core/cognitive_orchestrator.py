from dataclasses import dataclass, field


@dataclass
class CognitivePlan:

    query: str

    use_working_memory: bool = True

    use_profile: bool = False

    search_memories: bool = True

    search_episodes: bool = False

    search_skills: bool = False

    use_patterns: bool = False

    use_predictions: bool = False

    max_memories: int = 5

    max_episodes: int = 3

    max_skills: int = 2

    max_predictions: int = 2

    reasons: list = field(
        default_factory=list
    )


class CognitiveOrchestrator:

    """
    Capa de decisión rápida de AURA.

    Su función es decidir qué sistemas de memoria deben
    intervenir en una consulta concreta.

    Principio:

        recuperar solamente lo necesario
        ↓
        construir contexto compacto
        ↓
        enviar a Qwen
    """

    def __init__(
        self,
        memory_manager,
        memory_learner=None
    ):

        self.memory = memory_manager

        self.learner = memory_learner

        self.config = (
            memory_manager.config
        )

        self.turn_count = 0

    # ==================================================
    # PLAN
    # ==================================================

    def plan(
        self,
        query
    ):

        query = str(
            query or ""
        ).strip()

        text = query.lower()

        plan = CognitivePlan(
            query=query
        )

        if not query:

            return plan

        # ==================================================
        # CONSULTAS SIMPLES
        # ==================================================

        if self._is_simple_query(
            text
        ):

            plan.search_memories = False

            plan.use_working_memory = False

            plan.use_profile = False

            plan.search_episodes = False

            plan.search_skills = False

            plan.use_patterns = False

            plan.use_predictions = False

            plan.max_memories = 0

            plan.max_episodes = 0

            plan.max_skills = 0

            plan.max_predictions = 0

            plan.reasons.append(
                "Consulta simple."
            )

            return plan

        # ==================================================
        # IDENTIDAD / INFORMACIÓN PERSONAL
        # ==================================================

        if self._contains_any(
            text,
            (
                "quien soy",
                "quién soy",
                "como me llamo",
                "cómo me llamo",
                "mi nombre",
                "que sabes de mi",
                "qué sabes de mí",
                "que recuerdas de mi",
                "qué recuerdas de mí",
                "mis preferencias",
                "mis gustos",
                "mi proyecto",
                "mis proyectos",
                "mis habitos",
                "mis hábitos"
            )
        ):

            plan.use_profile = True

            plan.max_memories = 6

            plan.reasons.append(
                "Consulta sobre el usuario."
            )

        # ==================================================
        # EXPERIENCIAS ANTERIORES
        # ==================================================

        if self._contains_any(
            text,
            (
                "la otra vez",
                "otra vez",
                "anteriormente",
                "recuerdas cuando",
                "recuerdas que",
                "te acuerdas de",
                "qué hicimos",
                "que hicimos",
                "lo que hicimos",
                "aquella vez",
                "en aquella conversación",
                "la conversación anterior",
                "cuando hicimos"
            )
        ):

            plan.search_episodes = True

            plan.max_episodes = 5

            plan.reasons.append(
                "Referencia a experiencia anterior."
            )

        # ==================================================
        # HABILIDADES
        # ==================================================

        if self._contains_any(
            text,
            (
                "como hago",
                "cómo hago",
                "como se hace",
                "cómo se hace",
                "como puedo",
                "cómo puedo",
                "que pasos",
                "qué pasos",
                "pasos para",
                "enséñame a",
                "enseñame a",
                "cómo configurar",
                "como configurar",
                "cómo instalar",
                "como instalar",
                "cómo solucionar",
                "como solucionar",
                "cómo modificar",
                "como modificar"
            )
        ):

            plan.search_skills = True

            plan.max_skills = 3

            plan.reasons.append(
                "Consulta procedimental."
            )

        # ==================================================
        # PATRONES
        # ==================================================

        if self._contains_any(
            text,
            (
                "suelo",
                "normalmente",
                "habitualmente",
                "siempre",
                "prefiero",
                "me gusta",
                "qué prefiero",
                "que prefiero",
                "qué suelo",
                "que suelo",
                "mi forma de"
            )
        ):

            plan.use_patterns = True

            plan.use_profile = True

            plan.reasons.append(
                "Consulta relacionada con patrones."
            )

        # ==================================================
        # PREDICCIONES
        # ==================================================

        if self._contains_any(
            text,
            (
                "qué necesitaré",
                "que necesitare",
                "qué voy a necesitar",
                "que voy a necesitar",
                "qué podría necesitar",
                "que podria necesitar",
                "qué debería hacer después",
                "que deberia hacer despues",
                "qué haré después",
                "que hare despues",
                "qué es probable que",
                "que es probable que"
            )
        ):

            plan.use_predictions = True

            plan.max_predictions = 2

            plan.use_patterns = True

            plan.use_profile = True

            plan.reasons.append(
                "La consulta solicita una predicción."
            )

        # ==================================================
        # TAREAS OPERATIVAS
        # ==================================================

        if self._contains_any(
            text,
            (
                "crear",
                "crea",
                "instalar",
                "instala",
                "configurar",
                "configura",
                "modificar",
                "modifica",
                "solucionar",
                "soluciona",
                "arreglar",
                "arregla",
                "ejecutar",
                "ejecuta",
                "borrar",
                "borra",
                "copiar",
                "copia",
                "mover",
                "mueve"
            )
        ):

            plan.search_memories = True

            if not plan.search_skills:

                if self._contains_any(
                    text,
                    (
                        "cómo",
                        "como",
                        "pasos",
                        "procedimiento"
                    )
                ):

                    plan.search_skills = True

                    plan.max_skills = 2

            plan.reasons.append(
                "Consulta operativa."
            )

        return plan

    # ==================================================
    # CONTEXTO
    # ==================================================

    def build_context(
        self,
        plan
    ):

        if plan is None:

            return ""

        sections = []

        # ==================================================
        # MEMORIA DE TRABAJO
        # ==================================================

        if plan.use_working_memory:

            try:

                working = (
                    self.memory
                    .build_working_context(
                        max_chars=2500
                    )
                )

            except Exception:

                working = ""

            if working:

                sections.append(
                    (
                        "CONTEXTO ACTUAL\n"
                        "===============\n"
                        +
                        working
                    )
                )

        # ==================================================
        # PERFIL
        # ==================================================

        if plan.use_profile:

            try:

                profile = (
                    self.memory
                    .build_profile_context(
                        max_chars=3000,
                        include_predictions=False,
                        include_patterns=(
                            plan.use_patterns
                        )
                    )
                )

            except Exception:

                profile = ""

            if profile:

                sections.append(
                    profile
                )

        # ==================================================
        # MEMORIA GENERAL
        # ==================================================

        if plan.search_memories:

            try:

                memories = (
                    self.memory
                    .search(
                        query=plan.query,
                        limit=plan.max_memories
                    )
                )

            except Exception:

                memories = []

            if memories:

                lines = [
                    "MEMORIAS RELEVANTES",
                    "==================="
                ]

                for memory in memories:

                    content = str(
                        memory.get(
                            "content",
                            ""
                        )
                    ).strip()

                    if not content:

                        continue

                    memory_type = (
                        memory.get(
                            "memory_type",
                            "general"
                        )
                    )

                    confidence = float(
                        memory.get(
                            "confidence",
                            1.0
                        )
                    )

                    lines.append(
                        f"- [{memory_type}] "
                        f"{content} "
                        f"(confianza {confidence:.2f})"
                    )

                if len(
                    lines
                ) > 2:

                    sections.append(
                        "\n".join(
                            lines
                        )
                    )

        # ==================================================
        # EPISODIOS
        # ==================================================

        if (
            plan.search_episodes
            and
            plan.max_episodes > 0
        ):

            try:

                episodes = (
                    self.memory
                    .search_episodes(
                        plan.query,
                        limit=plan.max_episodes
                    )
                )

            except Exception:

                episodes = []

            if episodes:

                lines = [
                    "EXPERIENCIAS ANTERIORES",
                    "======================="
                ]

                for episode in episodes:

                    summary = str(
                        episode.get(
                            "summary",
                            ""
                        )
                    ).strip()

                    if not summary:

                        episode_data = (
                            episode.get(
                                "episode",
                                {}
                            )
                        )

                        if isinstance(
                            episode_data,
                            dict
                        ):

                            summary = str(
                                episode_data.get(
                                    "summary",
                                    ""
                                )
                            ).strip()

                    if not summary:

                        continue

                    lines.append(
                        "- "
                        +
                        summary
                    )

                if len(
                    lines
                ) > 2:

                    sections.append(
                        "\n".join(
                            lines
                        )
                    )

        # ==================================================
        # HABILIDADES
        # ==================================================

        if (
            plan.search_skills
            and
            plan.max_skills > 0
        ):

            try:

                skills = (
                    self.memory
                    .find_skill(
                        plan.query,
                        limit=plan.max_skills
                    )
                )

            except Exception:

                skills = []

            if skills:

                lines = [
                    "HABILIDADES APRENDIDAS",
                    "======================"
                ]

                for skill in skills:

                    name = str(
                        skill.get(
                            "name",
                            ""
                        )
                    ).strip()

                    description = str(
                        skill.get(
                            "description",
                            ""
                        )
                    ).strip()

                    if not name:

                        continue

                    confidence = float(
                        skill.get(
                            "confidence",
                            0.0
                        )
                    )

                    reliability = float(
                        skill.get(
                            "reliability",
                            0.0
                        )
                    )

                    lines.append(
                        f"- {name}: "
                        f"{description} "
                        f"(confianza {confidence:.2f}, "
                        f"fiabilidad {reliability:.2f})"
                    )

                    steps = skill.get(
                        "steps",
                        []
                    )

                    if isinstance(
                        steps,
                        list
                    ):

                        for step in steps[:8]:

                            instruction = str(
                                step.get(
                                    "instruction",
                                    ""
                                )
                            ).strip()

                            if instruction:

                                lines.append(
                                    f"  "
                                    f"{step.get('step_number', '')}. "
                                    f"{instruction}"
                                )

                if len(
                    lines
                ) > 2:

                    sections.append(
                        "\n".join(
                            lines
                        )
                    )

        # ==================================================
        # PREDICCIONES
        # ==================================================

        if plan.use_predictions:

            try:

                predictions = (
                    self.memory
                    .predict(
                        query=plan.query,
                        limit=plan.max_predictions
                    )
                )

            except Exception:

                predictions = []

            if predictions:

                lines = [
                    "HIPÓTESIS PREDICTIVAS",
                    "====================="
                ]

                for prediction in predictions:

                    memory = prediction

                    if "memory" in prediction:

                        memory = (
                            prediction[
                                "memory"
                            ]
                        )

                    content = str(
                        memory.get(
                            "content",
                            ""
                        )
                    ).strip()

                    confidence = float(
                        memory.get(
                            "confidence",
                            0.0
                        )
                    )

                    if not content:

                        continue

                    lines.append(
                        f"- {content} "
                        f"(hipótesis, confianza "
                        f"{confidence:.2f})"
                    )

                if len(
                    lines
                ) > 2:

                    sections.append(
                        "\n".join(
                            lines
                        )
                    )

        # ==================================================
        # RESULTADO
        # ==================================================

        return "\n\n".join(
            sections
        )

    # ==================================================
    # APRENDIZAJE
    # ==================================================

    def learn(
        self,
        user_message,
        assistant_response
    ):

        if self.learner is None:

            return {
                "success": False,
                "learned": False
            }

        try:

            context = (
                self.memory
                .recent_messages(
                    limit=10
                )
            )

        except Exception:

            context = []

        try:

            return self.learner.learn(
                user_message=user_message,
                assistant_response=assistant_response,
                conversation_context=context
            )

        except Exception:

            return {
                "success": False,
                "learned": False
            }

    # ==================================================
    # EVALUAR PREDICCIONES
    # ==================================================

    def evaluate_predictions(
        self,
        user_message
    ):

        try:

            return (
                self.memory
                .evaluate_predictions_from_message(
                    user_message
                )
            )

        except Exception:

            return []

    # ==================================================
    # MANTENIMIENTO
    # ==================================================

    def maintain(
        self,
        force=False
    ):

        self.turn_count += 1

        try:

            self.memory.expire_predictions()

        except Exception:

            pass

        interval = max(
            1,
            int(
                self.config
                .CONSOLIDATION_INTERVAL
            )
        )

        if (
            not force
            and
            self.turn_count % interval != 0
        ):

            return None

        try:

            return (
                self.memory
                .consolidate()
            )

        except Exception:

            return None

    # ==================================================
    # CONSULTA SIMPLE
    # ==================================================

    @staticmethod
    def _is_simple_query(
        text
    ):

        normalized = (
            str(text)
            .strip()
            .lower()
        )

        if not normalized:

            return True

        simple_exact = {
            "hola",
            "buenas",
            "hey",
            "ok",
            "vale",
            "perfecto",
            "gracias",
            "adios",
            "adiós"
        }

        if normalized in simple_exact:

            return True

        if normalized in {
            "qué hora es",
            "que hora es",
            "qué día es",
            "que dia es"
        }:

            return True

        return False

    # ==================================================
    # CONTIENE ALGUNO
    # ==================================================

    @staticmethod
    def _contains_any(
        text,
        values
    ):

        return any(
            value in text
            for value in values
        )