import json
import re


class MemoryLearner:

    """
    Sistema de aprendizaje general de AURA.

    Extrae:

    - hechos;
    - preferencias;
    - hábitos;
    - proyectos;
    - conocimiento;
    - patrones potenciales;
    - observaciones.

    La memoria procedimental se procesa por separado para
    detectar habilidades reutilizables.
    """

    def __init__(
        self,
        model,
        memory_manager
    ):

        self.model = model

        self.memory = (
            memory_manager
        )

        self.consolidator = (
            memory_manager.consolidator
        )

    # ==================================================
    # APRENDER
    # ==================================================

    def learn(
        self,
        user_message,
        assistant_response,
        conversation_context=None
    ):

        if not user_message:

            return {
                "success": False,
                "learned": False,
                "memories": [],
                "procedures": []
            }

        conversation_context = (
            conversation_context
            or []
        )

        candidates = []

        if (
            self.memory.config.ENABLE_MEMORY_EXTRACTION
            and
            self.model is not None
        ):

            prompt = (
                self._build_prompt(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    conversation_context=conversation_context
                )
            )

            try:

                response = self.model.generate(
                    [
                        {
                            "role": "system",
                            "content": prompt
                        },
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ],
                    tools=[]
                )

                candidates = (
                    self._parse_response(
                        response
                    )
                )

            except Exception:

                candidates = []

        memory_results = []

        if candidates:

            try:

                result = (
                    self.consolidator
                    .consolidate(
                        candidates
                    )
                )

                memory_results = (
                    result.get(
                        "memories",
                        []
                    )
                )

            except Exception:

                memory_results = []

        # --------------------------------------------------
        # APRENDIZAJE PROCEDIMENTAL
        # --------------------------------------------------

        procedures = []

        if (
            self.memory
            .config
            .ENABLE_PROCEDURAL_LEARNING
        ):

            try:

                procedures = (
                    self.memory
                    .learn_procedure(
                        user_message=user_message,
                        assistant_response=assistant_response,
                        conversation_context=conversation_context
                    )
                )

            except Exception:

                procedures = []

        return {
            "success": True,

            "learned": bool(
                memory_results
                or
                procedures
            ),

            "memories":
                memory_results,

            "procedures":
                procedures
        }

    # ==================================================
    # PROMPT
    # ==================================================

    def _build_prompt(
        self,
        user_message,
        assistant_response,
        conversation_context
    ):

        lines = []

        for message in conversation_context[-8:]:

            if not isinstance(
                message,
                dict
            ):

                continue

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
            )

            if not content:

                continue

            if content.startswith(
                "TOOL RESULT"
            ):

                continue

            lines.append(
                f"{role}: {content}"
            )

        context = "\n".join(
            lines
        )

        return f"""
Eres el sistema de aprendizaje de una IA personal llamada AURA.

No debes responder al usuario.

Analiza la interacción y extrae únicamente información
que pueda ser útil a largo plazo.

Distingue:

- preferencia
- hecho personal
- hábito
- objetivo
- proyecto
- conocimiento
- experiencia
- decisión
- observación

No extraigas procedimientos aquí. Los procedimientos los
procesará un módulo especializado.

REGLAS:

1. No inventes información.

2. No guardes preguntas como hechos.

3. No guardes información trivial.

4. Una inferencia tiene menos confianza que una afirmación
   explícita.

5. Si el usuario pide recordar algo explícitamente:
   explicit = true.

6. Si algo es temporal:
   temporary = true.

7. Si existe información nueva que cambia una anterior,
   deja que el sistema de conflictos la gestione.

FORMATO:

{{
    "memories": [
        {{
            "action": "observe|create|update|ignore",
            "key": "concepto",
            "content": "informacion",
            "memory_type": "personal|preference|habit|knowledge|project|general",
            "category": "categoria",
            "importance": 0.0,
            "confidence": 0.0,
            "temporary": false,
            "explicit": false,
            "tags": []
        }}
    ]
}}

Si no hay información útil:

{{
    "memories": []
}}

CONTEXTO:

{context}

RESPUESTA DE AURA:

{assistant_response}

MENSAJE:

{user_message}

Devuelve únicamente JSON válido.
"""

    # ==================================================
    # PARSER
    # ==================================================

    def _parse_response(
        self,
        response
    ):

        if not response:

            return []

        text = self._clean(
            str(response).strip()
        )

        data = self._extract_json(
            text
        )

        if not isinstance(
            data,
            dict
        ):

            return []

        memories = data.get(
            "memories",
            []
        )

        if not isinstance(
            memories,
            list
        ):

            return []

        result = []

        for item in memories:

            if not isinstance(
                item,
                dict
            ):

                continue

            action = str(
                item.get(
                    "action",
                    "ignore"
                )
            ).strip().lower()

            if action not in {
                "observe",
                "create",
                "update",
                "ignore"
            }:

                action = "ignore"

            if action == "ignore":

                continue

            content = str(
                item.get(
                    "content",
                    ""
                )
            ).strip()

            if not content:

                continue

            key = item.get(
                "key"
            )

            if key is not None:

                key = (
                    str(key)
                    .strip()
                    .lower()
                    or None
                )

            result.append({
                "action":
                    action,

                "key":
                    key,

                "content":
                    content,

                "memory_type":
                    str(
                        item.get(
                            "memory_type",
                            "general"
                        )
                    ).strip().lower(),

                "category":
                    str(
                        item.get(
                            "category",
                            "general"
                        )
                    ).strip().lower(),

                "importance":
                    self._number(
                        item.get(
                            "importance",
                            0.5
                        ),
                        0.5
                    ),

                "confidence":
                    self._number(
                        item.get(
                            "confidence",
                            0.7
                        ),
                        0.7
                    ),

                "temporary":
                    bool(
                        item.get(
                            "temporary",
                            False
                        )
                    ),

                "explicit":
                    bool(
                        item.get(
                            "explicit",
                            False
                        )
                    ),

                "tags":
                    (
                        item.get(
                            "tags",
                            []
                        )
                        if isinstance(
                            item.get(
                                "tags",
                                []
                            ),
                            list
                        )
                        else []
                    )
            })

        return result

    @staticmethod
    def _extract_json(
        text
    ):

        try:

            return json.loads(
                text
            )

        except Exception:

            pass

        match = re.search(
            r"\{.*\}",
            text,
            re.DOTALL
        )

        if not match:

            return None

        try:

            return json.loads(
                match.group(
                    0
                )
            )

        except Exception:

            return None

    @staticmethod
    def _clean(
        text
    ):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text,
            flags=re.IGNORECASE
        )

        text = re.sub(
            r"```$",
            "",
            text
        )

        return text.strip()

    @staticmethod
    def _number(
        value,
        default
    ):

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            value = default

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )