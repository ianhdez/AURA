import json


class MemoryConsolidator:

    """
    Consolida observaciones en memoria estable.

    Una observación no se convierte automáticamente en una
    verdad permanente.

    Primero se acumula evidencia.

    Después se evalúa si existe suficiente coherencia para
    consolidarla.
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

        self.store = (
            memory_manager.store
        )

        self.config = (
            memory_manager.config
        )

    # ==================================================
    # CONSOLIDAR
    # ==================================================

    def consolidate(
        self,
        candidates=None
    ):

        results = []

        if candidates:

            for candidate in candidates:

                result = (
                    self._process_candidate(
                        candidate
                    )
                )

                if result:

                    results.append(
                        result
                    )

        if (
            self.config.ENABLE_CONSOLIDATION
        ):

            results.extend(
                self._consolidate_observations()
            )

        return {
            "memories": results
        }

    # ==================================================
    # CANDIDATO
    # ==================================================

    def _process_candidate(
        self,
        candidate
    ):

        action = str(
            candidate.get(
                "action",
                "ignore"
            )
        ).lower()

        if action == "ignore":

            return None

        if action == "observe":

            return (
                self._store_observation(
                    candidate
                )
            )

        if candidate.get(
            "temporary",
            False
        ):

            return (
                self._store_observation(
                    candidate
                )
            )

        content = str(
            candidate.get(
                "content",
                ""
            )
        ).strip()

        if not content:

            return None

        result = (
            self.memory.conflicts.resolve(
                content=content,

                key=candidate.get(
                    "key"
                ),

                memory_type=candidate.get(
                    "memory_type",
                    "general"
                ),

                category=candidate.get(
                    "category",
                    "general"
                ),

                importance=candidate.get(
                    "importance",
                    0.5
                ),

                confidence=candidate.get(
                    "confidence",
                    0.7
                ),

                source="conversation",

                metadata={
                    "learned_by":
                        "memory_consolidator",

                    "tags":
                        candidate.get(
                            "tags",
                            []
                        )
                },

                explicit=bool(
                    candidate.get(
                        "explicit",
                        False
                    )
                )
            )
        )

        return result

    # ==================================================
    # OBSERVACIÓN
    # ==================================================

    def _store_observation(
        self,
        candidate
    ):

        content = str(
            candidate.get(
                "content",
                ""
            )
        ).strip()

        if not content:

            return None

        metadata = {
            "temporary":
                True,

            "observation":
                True,

            "candidate_key":
                candidate.get(
                    "key"
                ),

            "candidate_type":
                candidate.get(
                    "memory_type",
                    "general"
                ),

            "candidate_category":
                candidate.get(
                    "category",
                    "general"
                ),

            "explicit":
                bool(
                    candidate.get(
                        "explicit",
                        False
                    )
                ),

            "tags":
                candidate.get(
                    "tags",
                    []
                )
        }

        memory = self.memory.remember(
            content=content,

            key=None,

            memory_type="episodic",

            category="observation",

            importance=min(
                0.75,
                float(
                    candidate.get(
                        "importance",
                        0.4
                    )
                )
            ),

            confidence=float(
                candidate.get(
                    "confidence",
                    0.7
                )
            ),

            source="observed",

            metadata=metadata,

            create_associations=False,

            explicit=False
        )

        return {
            "action": "observed",
            "memory": memory
        }

    # ==================================================
    # CONSOLIDAR OBSERVACIONES
    # ==================================================

    def _consolidate_observations(
        self
    ):

        observations = (
            self._get_observations()
        )

        if not observations:

            return []

        groups = (
            self._group_observations(
                observations
            )
        )

        results = []

        for group in groups:

            if not self._group_ready(
                group
            ):

                continue

            decision = (
                self._evaluate_group(
                    group
                )
            )

            if not decision:

                continue

            if decision.get(
                "action"
            ) != "consolidate":

                continue

            result = (
                self._consolidate_group(
                    group,
                    decision
                )
            )

            if result:

                results.append(
                    result
                )

        return results

    # ==================================================
    # OBTENER OBSERVACIONES
    # ==================================================

    def _get_observations(
        self
    ):

        memories = (
            self.store.list_memories(
                memory_type="episodic",
                status="active",
                limit=10000
            )
        )

        observations = []

        for memory in memories:

            metadata = (
                memory.get(
                    "metadata",
                    {}
                )
            )

            if not isinstance(
                metadata,
                dict
            ):

                continue

            if not metadata.get(
                "observation",
                False
            ):

                continue

            if not metadata.get(
                "temporary",
                False
            ):

                continue

            observations.append(
                memory
            )

        return observations

    # ==================================================
    # AGRUPAR
    # ==================================================

    def _group_observations(
        self,
        observations
    ):

        groups = []

        used = set()

        for observation in observations:

            observation_id = (
                observation.get(
                    "id"
                )
            )

            if (
                not observation_id
                or
                observation_id in used
            ):

                continue

            group = [
                observation
            ]

            used.add(
                observation_id
            )

            try:

                candidates = (
                    self.memory.search(
                        observation.get(
                            "content",
                            ""
                        ),
                        limit=20,
                        memory_type="episodic"
                    )
                )

            except Exception:

                candidates = []

            for candidate in candidates:

                candidate_id = (
                    candidate.get(
                        "id"
                    )
                )

                if (
                    not candidate_id
                    or
                    candidate_id in used
                ):

                    continue

                metadata = (
                    candidate.get(
                        "metadata",
                        {}
                    )
                )

                if not isinstance(
                    metadata,
                    dict
                ):

                    continue

                if not metadata.get(
                    "observation",
                    False
                ):

                    continue

                similarity = max(
                    float(
                        candidate.get(
                            "semantic_score",
                            0.0
                        )
                    ),
                    float(
                        candidate.get(
                            "relevance",
                            0.0
                        )
                    )
                )

                if (
                    similarity
                    >=
                    self.config
                    .CONSOLIDATION_SIMILARITY_THRESHOLD
                ):

                    group.append(
                        candidate
                    )

                    used.add(
                        candidate_id
                    )

                if len(
                    group
                ) >= 10:

                    break

            groups.append(
                group
            )

        return groups

    # ==================================================
    # ¿LISTO?
    # ==================================================

    def _group_ready(
        self,
        group
    ):

        if not group:

            return False

        if len(group) >= (
            self.config
            .CONSOLIDATION_MIN_OBSERVATIONS
        ):

            return True

        first = group[0]

        return (
            float(
                first.get(
                    "importance",
                    0.0
                )
            )
            >= 0.90

            and

            float(
                first.get(
                    "confidence",
                    0.0
                )
            )
            >= 0.95
        )

    # ==================================================
    # EVALUAR
    # ==================================================

    def _evaluate_group(
        self,
        group
    ):

        if self.model is None:

            return None

        observations = []

        for item in group:

            observations.append({
                "id":
                    item.get(
                        "id"
                    ),

                "content":
                    item.get(
                        "content"
                    ),

                "importance":
                    item.get(
                        "importance"
                    ),

                "confidence":
                    item.get(
                        "confidence"
                    )
            })

        prompt = f"""
Eres el sistema de consolidación de memoria de AURA.

Analiza estas observaciones y determina si existe evidencia
suficiente para crear una memoria estable.

OBSERVACIONES:

{json.dumps(
    observations,
    ensure_ascii=False,
    indent=2
)}

REGLAS:

- No inventes información.
- Una repetición coherente aumenta la confianza.
- Las contradicciones no son confirmaciones.
- Una preferencia estable puede consolidarse.
- Un hábito repetido puede consolidarse.
- Una característica personal puede consolidarse.
- Un proyecto puede consolidarse si sigue vigente.
- Una información puramente temporal no debe convertirse
  automáticamente en memoria estable.
- No combines conceptos diferentes.

Devuelve exclusivamente:

{{
    "action": "consolidate|keep_observations",
    "key": "clave_del_concepto",
    "content": "representación estable de la información",
    "memory_type": "personal|preference|habit|skill|knowledge|project|semantic|general",
    "category": "categoria",
    "importance": 0.0,
    "confidence": 0.0,
    "reason": "motivo"
}}
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
                            "Evalúa estas observaciones."
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
    # CONSOLIDAR GRUPO
    # ==================================================

    def _consolidate_group(
        self,
        group,
        decision
    ):

        key = decision.get(
            "key"
        )

        content = decision.get(
            "content"
        )

        if not key or not content:

            return None

        confidence = (
            self._clamp(
                decision.get(
                    "confidence",
                    0.7
                )
            )
        )

        importance = (
            self._clamp(
                decision.get(
                    "importance",
                    0.5
                )
            )
        )

        if (
            confidence
            <
            self.config
            .CONSOLIDATION_CONFIDENCE_THRESHOLD
        ):

            return None

        evidence_ids = [
            item.get(
                "id"
            )
            for item in group
            if item.get(
                "id"
            )
        ]

        metadata = {
            "consolidated":
                True,

            "evidence_count":
                len(
                    evidence_ids
                ),

            "evidence_ids":
                evidence_ids,

            "consolidation_reason":
                decision.get(
                    "reason",
                    ""
                )
        }

        result = (
            self.memory.conflicts.resolve(
                content=content,
                key=key,
                memory_type=decision.get(
                    "memory_type",
                    "general"
                ),
                category=decision.get(
                    "category",
                    "general"
                ),
                importance=importance,
                confidence=confidence,
                source="learned",
                metadata=metadata,
                explicit=False
            )
        )

        memory = result.get(
            "memory"
        )

        if memory:

            memory_id = memory.get(
                "id"
            )

            for observation in group:

                observation_id = (
                    observation.get(
                        "id"
                    )
                )

                if not observation_id:

                    continue

                observation_metadata = dict(
                    observation.get(
                        "metadata",
                        {}
                    )
                    or
                    {}
                )

                observation_metadata[
                    "temporary"
                ] = False

                observation_metadata[
                    "consolidated"
                ] = True

                observation_metadata[
                    "consolidated_into"
                ] = memory_id

                try:

                    self.store.update_memory(
                        observation_id,
                        status="archived",
                        metadata=observation_metadata
                    )

                    self.store.add_relation(
                        observation_id,
                        memory_id,
                        "supports",
                        weight=1.0
                    )

                except Exception:

                    continue

        return result

    # ==================================================
    # JSON
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

            return json.loads(
                text
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

            return json.loads(
                text[
                    start:
                    end + 1
                ]
            )

        except Exception:

            return None

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