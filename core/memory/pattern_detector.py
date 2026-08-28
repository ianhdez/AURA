import json
from collections import defaultdict


class PatternDetector:

    """
    Detecta patrones recurrentes en la experiencia del usuario.

    Diferencia entre:

        observación
            ↓
        repetición
            ↓
        patrón

    Un patrón nunca se trata inicialmente como una certeza
    absoluta.

    Cada patrón conserva:

    - observaciones que lo respaldan;
    - número de evidencias;
    - confianza;
    - importancia;
    - motivo;
    - relación con sus evidencias.
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
    # DETECTAR
    # ==================================================

    def detect(
        self,
        limit=10000
    ):

        if not self.config.ENABLE_PATTERN_DETECTION:

            return []

        observations = (
            self._get_observations(
                limit
            )
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

            if not self._is_pattern_candidate(
                group
            ):

                continue

            analysis = (
                self._analyze_group(
                    group
                )
            )

            if not analysis:

                continue

            if not analysis.get(
                "valid",
                False
            ):

                continue

            result = (
                self._store_pattern(
                    group,
                    analysis
                )
            )

            if result:

                results.append(
                    result
                )

            if len(
                results
            ) >= self.config.PATTERN_MAX_RESULTS:

                break

        return results

    # ==================================================
    # OBSERVACIONES
    # ==================================================

    def _get_observations(
        self,
        limit
    ):

        memories = (
            self.store.list_memories(
                memory_type="episodic",
                status="active",
                limit=limit
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

            if metadata.get(
                "consolidated",
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

        keyed_groups = defaultdict(
            list
        )

        unkeyed = []

        for observation in observations:

            metadata = (
                observation.get(
                    "metadata",
                    {}
                )
            )

            candidate_key = None

            if isinstance(
                metadata,
                dict
            ):

                candidate_key = (
                    metadata.get(
                        "candidate_key"
                    )
                )

            if candidate_key:

                keyed_groups[
                    str(
                        candidate_key
                    )
                    .strip()
                    .lower()
                ].append(
                    observation
                )

            else:

                unkeyed.append(
                    observation
                )

        groups = [
            group
            for group in
            keyed_groups.values()
            if group
        ]

        # --------------------------------------------------
        # Las observaciones sin clave requieren
        # agrupación semántica.
        # --------------------------------------------------

        used = set()

        for observation in unkeyed:

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

                matches = (
                    self.memory.search(
                        observation.get(
                            "content",
                            ""
                        ),
                        limit=30,
                        memory_type="episodic"
                    )
                )

            except Exception:

                matches = []

            for match in matches:

                match_id = (
                    match.get(
                        "id"
                    )
                )

                if (
                    not match_id
                    or
                    match_id in used
                ):

                    continue

                metadata = (
                    match.get(
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
                        match.get(
                            "semantic_score",
                            0.0
                        )
                    ),
                    float(
                        match.get(
                            "relevance",
                            0.0
                        )
                    )
                )

                if similarity >= (
                    self.config
                    .PATTERN_SIMILARITY_THRESHOLD
                ):

                    group.append(
                        match
                    )

                    used.add(
                        match_id
                    )

                if len(
                    group
                ) >= (
                    self.config
                    .PATTERN_MAX_OBSERVATIONS
                ):

                    break

            groups.append(
                group
            )

        return groups

    # ==================================================
    # CANDIDATO
    # ==================================================

    def _is_pattern_candidate(
        self,
        group
    ):

        if len(group) >= (
            self.config
            .PATTERN_MIN_OBSERVATIONS
        ):

            return True

        if len(group) == 2:

            importance = max(
                float(
                    item.get(
                        "importance",
                        0.0
                    )
                )
                for item in group
            )

            confidence = min(
                float(
                    item.get(
                        "confidence",
                        0.0
                    )
                )
                for item in group
            )

            return (
                importance
                >=
                self.config
                .PATTERN_IMPORTANCE_THRESHOLD

                and

                confidence
                >=
                self.config
                .PATTERN_CONFIDENCE_THRESHOLD
            )

        return False

    # ==================================================
    # ANALIZAR GRUPO
    # ==================================================

    def _analyze_group(
        self,
        group
    ):

        if self.model is None:

            return (
                self._heuristic_pattern(
                    group
                )
            )

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

                "created_at":
                    item.get(
                        "created_at"
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
Eres el detector de patrones de una IA personal llamada AURA.

Analiza varias observaciones independientes sobre el usuario.

Tu función NO es describir una sola observación.

Debes determinar si las observaciones muestran un patrón
repetido de comportamiento, preferencia, interés, comunicación,
decisión o forma de trabajo.

OBSERVACIONES:

{json.dumps(
    observations,
    ensure_ascii=False,
    indent=2
)}

REGLAS:

1. No inventes información.

2. Un único acontecimiento no constituye un patrón.

3. Dos observaciones pueden ser suficientes solamente si
   ambas tienen una importancia y confianza altas.

4. Tres o más observaciones repetidas son evidencia mucho
   más fuerte.

5. No confundas coincidencia temporal con hábito.

6. No afirmes causalidad sin evidencia.

7. No exageres rasgos de personalidad.

8. Expresa el patrón de forma prudente.

9. La confianza debe corresponder a la evidencia disponible.

10. No conviertas una preferencia puntual en una característica
    permanente sin suficiente evidencia.

TIPOS:

habit
preference_pattern
workflow_pattern
communication_pattern
decision_pattern
interest_pattern
behavior_pattern
general_pattern

FORMATO OBLIGATORIO:

{{
    "valid": true,
    "key": "pattern_nombre",
    "content": "descripción clara y prudente del patrón",
    "memory_type": "pattern",
    "category": "habit|preference|workflow|communication|behavior|interest",
    "importance": 0.0,
    "confidence": 0.0,
    "reason": "explicación breve basada únicamente en las observaciones"
}}

Si no existe suficiente evidencia:

{{
    "valid": false
}}

Devuelve ÚNICAMENTE JSON válido.
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
                            "Analiza las observaciones."
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
    # HEURÍSTICA
    # ==================================================

    def _heuristic_pattern(
        self,
        group
    ):

        if len(group) < 2:

            return None

        first_metadata = (
            group[0].get(
                "metadata",
                {}
            )
        )

        if not isinstance(
            first_metadata,
            dict
        ):

            return None

        candidate_key = (
            first_metadata.get(
                "candidate_key"
            )
        )

        if not candidate_key:

            return None

        count = len(
            group
        )

        confidence = min(
            0.90,
            0.50
            +
            (
                count
                * 0.10
            )
        )

        return {
            "valid": True,

            "key":
                "pattern_"
                +
                str(
                    candidate_key
                )
                .strip()
                .lower(),

            "content":
                "Se ha observado repetidamente "
                f"el concepto asociado a "
                f"'{candidate_key}'.",

            "memory_type":
                "pattern",

            "category":
                "behavior",

            "importance":
                0.60,

            "confidence":
                confidence,

            "reason":
                "Se detectó repetición de "
                f"{count} observaciones."
        }

    # ==================================================
    # GUARDAR
    # ==================================================

    def _store_pattern(
        self,
        group,
        pattern
    ):

        key = str(
            pattern.get(
                "key",
                ""
            )
        ).strip().lower()

        content = str(
            pattern.get(
                "content",
                ""
            )
        ).strip()

        if not key or not content:

            return None

        confidence = (
            self._clamp(
                pattern.get(
                    "confidence",
                    0.5
                )
            )
        )

        importance = (
            self._clamp(
                pattern.get(
                    "importance",
                    0.5
                )
            )
        )

        if (
            confidence
            <
            self.config.PATTERN_CONFIDENCE_THRESHOLD
        ):

            return None

        if (
            importance
            <
            self.config.PATTERN_IMPORTANCE_THRESHOLD
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
            "pattern":
                True,

            "evidence_count":
                len(
                    evidence_ids
                ),

            "evidence_ids":
                evidence_ids,

            "pattern_reason":
                pattern.get(
                    "reason",
                    ""
                )
        }

        existing = (
            self.store.get_by_key(
                key
            )
        )

        if existing:

            existing_metadata = dict(
                existing.get(
                    "metadata",
                    {}
                )
                or {}
            )

            previous_count = int(
                existing_metadata.get(
                    "pattern_observed_count",
                    0
                )
            )

            merged_evidence = list(
                existing_metadata.get(
                    "evidence_ids",
                    []
                )
                or []
            )

            for evidence_id in evidence_ids:

                if (
                    evidence_id
                    not in
                    merged_evidence
                ):

                    merged_evidence.append(
                        evidence_id
                    )

            merged_evidence = (
                merged_evidence[
                    -100:
                ]
            )

            existing_metadata.update(
                metadata
            )

            existing_metadata[
                "evidence_ids"
            ] = merged_evidence

            existing_metadata[
                "pattern_observed_count"
            ] = (
                previous_count
                +
                len(evidence_ids)
            )

            result = (
                self.store.update_memory(
                    existing["id"],

                    content=content,

                    memory_type="pattern",

                    category=pattern.get(
                        "category",
                        "behavior"
                    ),

                    importance=max(
                        float(
                            existing.get(
                                "importance",
                                0.5
                            )
                        ),
                        importance
                    ),

                    confidence=max(
                        float(
                            existing.get(
                                "confidence",
                                0.5
                            )
                        ),
                        confidence
                    ),

                    metadata=existing_metadata
                )
            )

            for evidence_id in evidence_ids:

                self.store.add_relation(
                    evidence_id,
                    result["id"],
                    "supports_pattern",
                    weight=confidence
                )

            return {
                "action": "updated",
                "memory": result
            }

        memory = self.memory.remember(
            content=content,
            key=key,
            memory_type="pattern",
            category=pattern.get(
                "category",
                "behavior"
            ),
            importance=importance,
            confidence=confidence,
            source="learned",
            metadata=metadata,
            create_associations=True,
            explicit=False
        )

        if not memory:

            return None

        for evidence_id in evidence_ids:

            self.store.add_relation(
                evidence_id,
                memory["id"],
                "supports_pattern",
                weight=confidence
            )

        return {
            "action": "created",
            "memory": memory
        }

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