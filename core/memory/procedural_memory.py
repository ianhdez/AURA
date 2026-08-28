import json
import re


class ProceduralMemory:

    """
    Memoria procedimental de AURA.

    Representa habilidades reutilizables como:

        nombre
        descripción
        precondiciones
        pasos
        resultados esperados
        pistas ante fallos
        historial de ejecuciones
        fiabilidad
        confianza
        versión

    Una habilidad puede evolucionar con el tiempo.
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
    # APRENDER
    # ==================================================

    def learn(
        self,
        user_message,
        assistant_response,
        conversation_context=None
    ):

        if not self.config.ENABLE_PROCEDURAL_LEARNING:

            return []

        if self.model is None:

            return []

        prompt = self._build_learning_prompt(
            user_message=user_message,
            assistant_response=assistant_response,
            conversation_context=(
                conversation_context
                or []
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

        except Exception:

            return []

        procedures = self._parse(
            response
        )

        results = []

        for procedure in procedures:

            result = (
                self.learn_procedure(
                    procedure
                )
            )

            if result:

                results.append(
                    result
                )

        return results

    # ==================================================
    # PROMPT DE APRENDIZAJE
    # ==================================================

    def _build_learning_prompt(
        self,
        user_message,
        assistant_response,
        conversation_context
    ):

        lines = []

        for message in conversation_context[-10:]:

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
Eres el sistema de aprendizaje procedimental de AURA.

Tu función es detectar si en la interacción se ha aprendido
CÓMO realizar una tarea de forma reutilizable.

No debes responder al usuario.

Solo extrae un procedimiento cuando exista evidencia real
de que se ha aprendido una secuencia, método, técnica o forma
de resolver una tarea.

Ejemplos válidos:

- configuración de un programa;
- reparación de un problema;
- procedimiento para modificar archivos;
- pasos para realizar una tarea técnica;
- método de trabajo repetible;
- procedimiento que el usuario ya ha aprendido;
- secuencia que AURA ha utilizado correctamente.

No guardes como habilidad:

- una opinión;
- un dato;
- una preferencia;
- una simple explicación teórica;
- una acción aislada sin procedimiento;
- información que no pueda reutilizarse.

Una habilidad debe poder representarse como una secuencia.

CONTEXTO:

{context}

MENSAJE DEL USUARIO:

{user_message}

RESPUESTA DE AURA:

{assistant_response}

Devuelve exclusivamente JSON:

{{
    "procedures": [
        {{
            "skill_key": "clave_estable",
            "name": "nombre",
            "description": "qué permite hacer",
            "category": "general|computer|files|software|workflow|technical|communication",
            "confidence": 0.0,
            "importance": 0.0,
            "preconditions": [
                "condición"
            ],
            "steps": [
                {{
                    "instruction": "paso",
                    "expected_result": "resultado",
                    "failure_hint": "qué hacer si falla",
                    "optional": false
                }}
            ]
        }}
    ]
}}

Reglas:

- No inventes pasos.
- No añadas pasos que no aparezcan o no puedan inferirse
  con seguridad de la interacción.
- No inventes herramientas utilizadas.
- Mantén el procedimiento concreto.
- Máximo 50 pasos.
- Las precondiciones deben ser reales.
- La confianza refleja la evidencia disponible.

Si no se aprendió ningún procedimiento:

{{
    "procedures": []
}}

Devuelve únicamente JSON válido.
"""

    # ==================================================
    # GUARDAR PROCEDIMIENTO
    # ==================================================

    def learn_procedure(
        self,
        procedure
    ):

        if not isinstance(
            procedure,
            dict
        ):

            return None

        skill_key = self._normalize_key(
            procedure.get(
                "skill_key"
            )
        )

        name = str(
            procedure.get(
                "name",
                ""
            )
        ).strip()

        description = str(
            procedure.get(
                "description",
                ""
            )
        ).strip()

        if not skill_key:

            return None

        if not name:

            return None

        if not description:

            return None

        steps = procedure.get(
            "steps",
            []
        )

        if not isinstance(
            steps,
            list
        ):

            return None

        steps = steps[
            :self.config.PROCEDURAL_MAX_STEPS
        ]

        cleaned_steps = []

        for step in steps:

            if not isinstance(
                step,
                dict
            ):

                continue

            instruction = str(
                step.get(
                    "instruction",
                    ""
                )
            ).strip()

            if not instruction:

                continue

            cleaned_steps.append({
                "instruction":
                    instruction,

                "expected_result":
                    str(
                        step.get(
                            "expected_result",
                            ""
                        )
                    ).strip(),

                "failure_hint":
                    str(
                        step.get(
                            "failure_hint",
                            ""
                        )
                    ).strip(),

                "optional":
                    bool(
                        step.get(
                            "optional",
                            False
                        )
                    )
            })

        if not cleaned_steps:

            return None

        confidence = self._clamp(
            procedure.get(
                "confidence",
                0.6
            )
        )

        importance = self._clamp(
            procedure.get(
                "importance",
                0.5
            )
        )

        if confidence < (
            self.config
            .PROCEDURAL_MIN_CONFIDENCE
        ):

            return None

        if importance < (
            self.config
            .PROCEDURAL_MIN_IMPORTANCE
        ):

            return None

        category = str(
            procedure.get(
                "category",
                "general"
            )
        ).strip().lower()

        existing = (
            self.store.get_skill_by_key(
                skill_key
            )
        )

        if existing:

            return self._update_existing_skill(
                existing=existing,
                name=name,
                description=description,
                category=category,
                confidence=confidence,
                importance=importance,
                preconditions=(
                    procedure.get(
                        "preconditions",
                        []
                    )
                ),
                steps=cleaned_steps
            )

        memory = self.memory.remember(
            content=description,
            key=skill_key,
            memory_type="procedural",
            category="skill",
            importance=importance,
            confidence=confidence,
            source="learned",
            metadata={
                "procedural":
                    True,

                "skill_key":
                    skill_key,

                "skill_name":
                    name
            },
            create_associations=True,
            explicit=False
        )

        if not memory:

            return None

        skill = self.store.create_skill(
            skill_key=skill_key,
            name=name,
            description=description,
            category=category,
            memory_id=memory.get(
                "id"
            ),
            confidence=confidence,
            metadata={
                "importance":
                    importance
            }
        )

        if not skill:

            return None

        self.store.replace_skill_steps(
            skill["id"],
            cleaned_steps
        )

        self.store.replace_skill_preconditions(
            skill["id"],
            [
                str(
                    item
                ).strip()
                for item in (
                    procedure.get(
                        "preconditions",
                        []
                    )
                    if isinstance(
                        procedure.get(
                            "preconditions",
                            []
                        ),
                        list
                    )
                    else []
                )
                if str(
                    item
                ).strip()
            ][
                :self.config
                .PROCEDURAL_MAX_PRECONDITIONS
            ]
        )

        return self.get_skill(
            skill_key
        )

    # ==================================================
    # ACTUALIZAR
    # ==================================================

    def _update_existing_skill(
        self,
        existing,
        name,
        description,
        category,
        confidence,
        importance,
        preconditions,
        steps
    ):

        current_version = int(
            existing.get(
                "version",
                1
            )
        )

        previous_confidence = float(
            existing.get(
                "confidence",
                0.5
            )
        )

        new_confidence = max(
            previous_confidence,
            confidence
        )

        metadata = dict(
            existing.get(
                "metadata",
                {}
            )
            or {}
        )

        metadata[
            "last_learning_event"
        ] = self._now()

        updated = (
            self.store.update_skill(
                existing["id"],
                name=name,
                description=description,
                category=category,
                confidence=new_confidence,
                version=current_version + 1,
                metadata=metadata
            )
        )

        if not updated:

            return None

        self.store.replace_skill_steps(
            existing["id"],
            steps
        )

        self.store.replace_skill_preconditions(
            existing["id"],
            [
                str(
                    item
                ).strip()
                for item in (
                    preconditions
                    if isinstance(
                        preconditions,
                        list
                    )
                    else []
                )
                if str(
                    item
                ).strip()
            ][
                :self.config
                .PROCEDURAL_MAX_PRECONDITIONS
            ]
        )

        # Actualizamos también la memoria asociada.

        memory_id = (
            existing.get(
                "memory_id"
            )
        )

        if memory_id:

            try:

                memory = self.store.update_memory(
                    memory_id,
                    content=description,
                    category="skill",
                    memory_type="procedural",
                    importance=max(
                        importance,
                        0.5
                    ),
                    confidence=new_confidence
                )

                self.memory._update_embedding(
                    memory
                )

            except Exception:

                pass

        return self.get_skill(
            existing[
                "skill_key"
            ]
        )

    # ==================================================
    # OBTENER
    # ==================================================

    def get_skill(
        self,
        skill_key
    ):

        skill = (
            self.store.get_skill_by_key(
                skill_key
            )
        )

        if not skill:

            return None

        skill[
            "steps"
        ] = (
            self.store.get_skill_steps(
                skill["id"]
            )
        )

        skill[
            "preconditions"
        ] = (
            self.store
            .get_skill_preconditions(
                skill["id"]
            )
        )

        return skill

    # ==================================================
    # BUSCAR
    # ==================================================

    def find_skill(
        self,
        query,
        limit=5
    ):

        if not query:

            return []

        results = (
            self.memory.search(
                query,
                limit=20,
                memory_type="procedural"
            )
        )

        skills = []

        for result in results:

            skill_key = (
                result.get(
                    "memory_key"
                )
            )

            if not skill_key:

                continue

            skill = self.get_skill(
                skill_key
            )

            if not skill:

                continue

            if float(
                skill.get(
                    "confidence",
                    0.0
                )
            ) < (
                self.config
                .PROCEDURAL_MIN_REUSE_CONFIDENCE
            ):

                continue

            similarity = max(
                float(
                    result.get(
                        "semantic_score",
                        0.0
                    )
                ),
                float(
                    result.get(
                        "relevance",
                        0.0
                    )
                )
            )

            if (
                similarity
                >=
                self.config
                .PROCEDURAL_SIMILARITY_THRESHOLD
            ):

                skill[
                    "retrieval_score"
                ] = similarity

                skills.append(
                    skill
                )

        skills.sort(
            key=lambda item: (
                item.get(
                    "retrieval_score",
                    0.0
                ),
                item.get(
                    "reliability",
                    0.0
                ),
                item.get(
                    "confidence",
                    0.0
                )
            ),
            reverse=True
        )

        return skills[
            :limit
        ]

    # ==================================================
    # EJECUCIÓN
    # ==================================================

    def start_run(
        self,
        skill_key,
        metadata=None
    ):

        skill = self.get_skill(
            skill_key
        )

        if not skill:

            return None

        return self.store.start_skill_run(
            skill["id"],
            metadata=metadata
        )

    def add_step_result(
        self,
        run_id,
        step_number,
        outcome,
        notes=None
    ):

        return self.store.add_skill_step_result(
            run_id=run_id,
            step_number=step_number,
            outcome=outcome,
            notes=notes
        )

    def finish_run(
        self,
        run_id,
        outcome,
        notes=None
    ):

        result = (
            self.store.finish_skill_run(
                run_id=run_id,
                outcome=outcome,
                notes=notes
            )
        )

        return result

    # ==================================================
    # ESTADÍSTICAS
    # ==================================================

    def statistics(
        self
    ):

        skills = (
            self.store.list_skills(
                limit=(
                    self.config
                    .PROCEDURAL_MAX_ACTIVE
                )
            )
        )

        total_runs = 0

        total_success = 0

        total_failure = 0

        total_partial = 0

        for skill in skills:

            total_runs += int(
                skill.get(
                    "use_count",
                    0
                )
            )

            total_success += int(
                skill.get(
                    "success_count",
                    0
                )
            )

            total_failure += int(
                skill.get(
                    "failure_count",
                    0
                )
            )

            total_partial += int(
                skill.get(
                    "partial_count",
                    0
                )
            )

        evaluated = (
            total_success
            +
            total_failure
            +
            total_partial
        )

        reliability = (
            (
                total_success
                +
                total_partial * 0.5
            )
            /
            evaluated
            if evaluated > 0
            else 0.0
        )

        return {
            "skills":
                len(skills),

            "runs":
                total_runs,

            "success":
                total_success,

            "failure":
                total_failure,

            "partial":
                total_partial,

            "reliability":
                reliability
        }

    # ==================================================
    # PARSER
    # ==================================================

    @staticmethod
    def _parse(
        response
    ):

        if not response:

            return []

        text = str(
            response
        ).strip()

        data = (
            ProceduralMemory
            ._parse_json(
                text
            )
        )

        if not isinstance(
            data,
            dict
        ):

            return []

        procedures = data.get(
            "procedures",
            []
        )

        if not isinstance(
            procedures,
            list
        ):

            return []

        return [
            item
            for item in procedures
            if isinstance(
                item,
                dict
            )
        ]

    @staticmethod
    def _parse_json(
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

    # ==================================================
    # KEY
    # ==================================================

    @staticmethod
    def _normalize_key(
        value
    ):

        if value is None:

            return None

        value = str(
            value
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9_]+",
            "_",
            value
        )

        value = re.sub(
            r"_+",
            "_",
            value
        )

        return value.strip(
            "_"
        )[:100]

    # ==================================================
    # CLAMP
    # ==================================================

    @staticmethod
    def _clamp(
        value
    ):

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            value = 0.5

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    @staticmethod
    def _now():

        from datetime import datetime

        return datetime.now().isoformat(
            timespec="seconds"
        )