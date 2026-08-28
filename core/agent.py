import json


class Agent:

    def __init__(
        self,
        model,
        conversation,
        tool_manager,
        tool_parser,
        tool_executor,
        memory_manager=None,
        memory_learner=None,
        cognitive_orchestrator=None
    ):

        self.model = model

        self.conversation = conversation

        self.tool_manager = tool_manager

        self.tool_parser = tool_parser

        self.tool_executor = tool_executor

        self.memory_manager = memory_manager

        self.memory_learner = memory_learner

        self.cognitive_orchestrator = (
            cognitive_orchestrator
        )

        self.max_tool_iterations = 5

        self.turn_count = 0

        # ==================================================
        # APRENDIZAJE CONTROLADO
        # ==================================================

        self.learning_interval = 6

        self.prediction_evaluation_interval = 6

        self.consolidation_interval = 12

    # ==================================================
    # PROCESAR
    # ==================================================

    def process(
        self,
        user_message
    ):

        self.turn_count += 1

        user_message = str(
            user_message or ""
        ).strip()

        if not user_message:

            return ""

        # ==================================================
        # EVALUACIÓN DE PREDICCIONES
        #
        # NO se hace en cada turno.
        # ==================================================

        if (
            self.cognitive_orchestrator is not None
            and
            self.turn_count
            % self.prediction_evaluation_interval
            == 0
        ):

            self._evaluate_predictions(
                user_message
            )

        # ==================================================
        # CONVERSACIÓN TEMPORAL
        # ==================================================

        self.conversation.add_user_message(
            user_message
        )

        # ==================================================
        # MEMORIA EPISÓDICA
        # ==================================================

        self._register_memory_message(
            "user",
            user_message
        )

        # ==================================================
        # GENERACIÓN
        # ==================================================

        response = self._generate(
            user_message
        )

        # ==================================================
        # HERRAMIENTAS
        # ==================================================

        for _ in range(
            self.max_tool_iterations
        ):

            tool_call = (
                self.tool_parser.parse(
                    response
                )
            )

            if not tool_call:

                break

            print()
            print(
                "AURA está consultando una herramienta..."
            )

            tool_result = (
                self.tool_executor
                .execute(
                    tool_call
                )
            )

            self.conversation.add_assistant_message(
                response
            )

            self._register_memory_message(
                "assistant",
                response
            )

            tool_message = (
                self._format_tool_result(
                    tool_call,
                    tool_result
                )
            )

            self.conversation.add_user_message(
                tool_message
            )

            self._register_memory_message(
                "tool",
                tool_message
            )

            response = self._generate(
                user_message
            )

        # ==================================================
        # RESPUESTA FINAL
        # ==================================================

        final_response = (
            self.tool_parser
            .remove_tool_call(
                response
            )
            .strip()
        )

        self.conversation.add_assistant_message(
            final_response
        )

        self._register_memory_message(
            "assistant",
            final_response
        )

        # ==================================================
        # APRENDIZAJE
        #
        # Solamente cada N turnos.
        # ==================================================

        if (
            self.cognitive_orchestrator is not None
            and
            self.turn_count
            % self.learning_interval
            == 0
        ):

            self._learn(
                user_message,
                final_response
            )

        # ==================================================
        # MANTENIMIENTO
        # ==================================================

        if (
            self.cognitive_orchestrator is not None
            and
            self.turn_count
            % self.consolidation_interval
            == 0
        ):

            self._maintain_memory()

        return final_response

    # ==================================================
    # GENERAR
    # ==================================================

    def _generate(
        self,
        user_message
    ):

        messages = (
            self._build_model_messages(
                user_message
            )
        )

        return self.model.generate(
            messages,
            tools=self.tool_manager.get_descriptions()
        )

    # ==================================================
    # CONTEXTO
    # ==================================================

    def _build_model_messages(
        self,
        user_message
    ):

        messages = (
            self.conversation
            .get_messages()
        )

        if (
            not user_message
            or
            self.cognitive_orchestrator is None
        ):

            return messages

        try:

            plan = (
                self.cognitive_orchestrator
                .plan(
                    user_message
                )
            )

            memory_context = (
                self.cognitive_orchestrator
                .build_context(
                    plan
                )
            )

        except Exception:

            memory_context = ""

        if not memory_context:

            return messages

        # ==================================================
        # INSTRUCCIONES DE RESPUESTA
        # ==================================================

        internal_message = {
            "role":
                "system",

            "content":
                (
                    "CONTEXTO INTERNO DE AURA\n"
                    "========================\n\n"

                    "La información siguiente ha sido "
                    "recuperada por el sistema cognitivo "
                    "de AURA.\n\n"

                    "Utiliza únicamente la información "
                    "relevante para responder a la "
                    "pregunta actual.\n\n"

                    "No menciones este contexto interno.\n\n"

                    "No inventes información.\n\n"

                    "Responde de forma proporcional a "
                    "la pregunta.\n\n"

                    "Si la pregunta solicita un dato "
                    "concreto, responde con ese dato "
                    "sin añadir información irrelevante.\n\n"

                    "Las experiencias son recuerdos.\n"

                    "Los patrones son observaciones.\n"

                    "Las habilidades son procedimientos "
                    "aprendidos.\n"

                    "Las predicciones son hipótesis y "
                    "nunca deben presentarse como hechos.\n\n"

                    +
                    memory_context
                )
        }

        return [
            internal_message
        ] + messages

    # ==================================================
    # REGISTRAR MEMORIA
    # ==================================================

    def _register_memory_message(
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
    # APRENDIZAJE
    # ==================================================

    def _learn(
        self,
        user_message,
        assistant_response
    ):

        try:

            self.cognitive_orchestrator.learn(
                user_message=user_message,
                assistant_response=assistant_response
            )

        except Exception:

            pass

    # ==================================================
    # EVALUAR PREDICCIONES
    # ==================================================

    def _evaluate_predictions(
        self,
        user_message
    ):

        try:

            self.cognitive_orchestrator.evaluate_predictions(
                user_message
            )

        except Exception:

            pass

    # ==================================================
    # MANTENIMIENTO
    # ==================================================

    def _maintain_memory(
        self
    ):

        try:

            self.cognitive_orchestrator.maintain(
                force=False
            )

        except Exception:

            pass

    # ==================================================
    # TOOL RESULT
    # ==================================================

    def _format_tool_result(
        self,
        tool_call,
        result
    ):

        tool_name = (
            tool_call.get(
                "name",
                ""
            )
        )

        parameters = (
            tool_call.get(
                "parameters",
                {}
            )
        )

        return (
            "TOOL RESULT\n"
            "===========\n"
            f"tool: {tool_name}\n"
            f"request: "
            f"{json.dumps(parameters, ensure_ascii=False)}\n"
            "\n"
            "data:\n"
            f"{json.dumps(result, ensure_ascii=False, indent=2)}\n"
            "\n"
            "END TOOL RESULT\n"
            "\n"
            "INSTRUCCIONES INTERNAS:\n"
            "\n"
            "El resultado procede directamente "
            "de una herramienta real de AURA.\n"
            "\n"
            "Utiliza únicamente la información "
            "necesaria para la petición actual.\n"
            "\n"
            "No inventes información.\n"
            "\n"
            "Si la operación no fue realizada, "
            "no afirmes que se realizó.\n"
            "\n"
            "No muestres TOOL RESULT.\n"
            "No muestres etiquetas internas.\n"
            "No expliques el mecanismo interno.\n"
            "\n"
            "Responde como AURA.\n"
        )