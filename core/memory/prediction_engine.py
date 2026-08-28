import json
from datetime import datetime, timedelta


class PredictionEngine:

    """
    Motor de predicción de AURA.

    Las predicciones son hipótesis probabilísticas.

    Nunca se consideran equivalentes a hechos.
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
    # GENERAR
    # ==================================================

    def predict(
        self,
        query=None,
        limit=5
    ):

        if not self.config.ENABLE_PREDICTION:

            return []

        context = (
            self._build_context(
                query
            )
        )

        if not context:

            return []

        if self.model is None:

            return []

        prompt = (
            self._build_prompt(
                context
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
                        "content":
                            "Genera predicciones."
                    }
                ],
                tools=[]
            )

        except Exception:

            return []

        predictions = (
            self._parse_predictions(
                response
            )
        )

        results = []

        for prediction in predictions[:limit]:

            created = (
                self._store_prediction(
                    prediction
                )
            )

            if created:

                results.append(
                    created
                )

        return results

    # ==================================================
    # CONTEXTO
    # ==================================================

    def _build_context(
        self,
        query=None
    ):

        parts = []

        working = (
            self.memory
            .build_working_context(
                max_chars=3500
            )
        )

        if working:

            parts.append(
                "MEMORIA DE TRABAJO\n"
                "==================\n"
                +
                working
            )

        profile = (
            self.memory
            .build_profile_context(
                max_chars=4000,
                include_patterns=True,
                include_predictions=False
            )
        )

        if profile:

            parts.append(
                profile
            )

        patterns = (
            self.memory
            .list_patterns(
                limit=10
            )
        )

        if patterns:

            lines = [
                "PATRONES ACTIVOS",
                "================"
            ]

            for pattern in patterns:

                confidence = float(
                    pattern.get(
                        "confidence",
                        0.0
                    )
                )

                if confidence < 0.60:

                    continue

                lines.append(
                    "- "
                    +
                    str(
                        pattern.get(
                            "content",
                            ""
                        )
                    )
                    +
                    f" "
                    f"(confianza {confidence:.2f})"
                )

            if len(lines) > 2:

                parts.append(
                    "\n".join(
                        lines
                    )
                )

        if query:

            try:

                memories = (
                    self.memory.search(
                        query,
                        limit=10
                    )
                )

            except Exception:

                memories = []

            if memories:

                lines = [
                    "MEMORIAS RELEVANTES"
                ]

                for memory in memories:

                    lines.append(
                        "- "
                        +
                        str(
                            memory.get(
                                "content",
                                ""
                            )
                        )
                    )

                parts.append(
                    "\n".join(
                        lines
                    )
                )

        return "\n\n".join(
            parts
        )

    # ==================================================
    # PROMPT
    # ==================================================

    @staticmethod
    def _build_prompt(
        context
    ):

        return f"""
Eres el motor predictivo de AURA.

Debes generar hipótesis sobre lo que el usuario podría
necesitar, hacer o preferir próximamente.

CONTEXTO:

{context}

REGLAS:

- No confundas hechos con predicciones.
- Toda predicción necesita evidencia.
- No predigas acontecimientos personales sensibles.
- No inventes intenciones.
- No conviertas una única coincidencia en un patrón.
- Da preferencia a patrones repetidos.
- Da preferencia a información reciente.
- Un proyecto activo puede generar predicciones sobre
  siguientes pasos.
- Un hábito repetido puede generar predicciones de conducta.
- Una necesidad repetida puede generar predicciones de necesidad.
- Las predicciones deben poder comprobarse posteriormente.
- No generes predicciones vagas si no aportan utilidad.

TIPOS:

need
next_action
preference
workflow
project
behavior
information
reminder
general

FORMATO:

{{
    "predictions": [
        {{
            "content": "predicción comprobable",
            "prediction_type": "need|next_action|preference|workflow|project|behavior|information|reminder|general",
            "importance": 0.0,
            "confidence": 0.0,
            "horizon_hours": 24,
            "evidence": [
                "evidencia"
            ]
        }}
    ]
}}

Si no existe una predicción suficientemente respaldada:

{{
    "predictions": []
}}

Devuelve únicamente JSON válido.
"""

    # ==================================================
    # PARSEAR
    # ==================================================

    def _parse_predictions(
        self,
        response
    ):

        data = self._parse_json(
            response
        )

        if not isinstance(
            data,
            dict
        ):

            return []

        raw = data.get(
            "predictions",
            []
        )

        if not isinstance(
            raw,
            list
        ):

            return []

        predictions = []

        for item in raw:

            if not isinstance(
                item,
                dict
            ):

                continue

            content = str(
                item.get(
                    "content",
                    ""
                )
            ).strip()

            if not content:

                continue

            prediction_type = str(
                item.get(
                    "prediction_type",
                    "general"
                )
            ).strip().lower()

            valid_types = {
                "need",
                "next_action",
                "preference",
                "workflow",
                "project",
                "behavior",
                "information",
                "reminder",
                "general"
            }

            if prediction_type not in valid_types:

                prediction_type = "general"

            importance = self._clamp(
                item.get(
                    "importance",
                    0.5
                ),
                0.5
            )

            confidence = self._clamp(
                item.get(
                    "confidence",
                    0.5
                ),
                0.5
            )

            if confidence < (
                self.config
                .PREDICTION_MIN_CONFIDENCE
            ):

                continue

            if importance < (
                self.config
                .PREDICTION_MIN_IMPORTANCE
            ):

                continue

            try:

                horizon_hours = float(
                    item.get(
                        "horizon_hours",
                        self.config
                        .PREDICTION_DEFAULT_HORIZON_HOURS
                    )
                )

            except Exception:

                horizon_hours = (
                    self.config
                    .PREDICTION_DEFAULT_HORIZON_HOURS
                )

            horizon_hours = max(
                1.0,
                min(
                    horizon_hours,
                    self.config
                    .PREDICTION_MAX_HORIZON_HOURS
                )
            )

            evidence = item.get(
                "evidence",
                []
            )

            if not isinstance(
                evidence,
                list
            ):

                evidence = []

            predictions.append({
                "content":
                    content,

                "prediction_type":
                    prediction_type,

                "importance":
                    importance,

                "confidence":
                    confidence,

                "horizon_hours":
                    horizon_hours,

                "evidence":
                    [
                        str(
                            value
                        ).strip()
                        for value in evidence
                        if str(
                            value
                        ).strip()
                    ]
            })

        return predictions

    # ==================================================
    # GUARDAR
    # ==================================================

    def _store_prediction(
        self,
        prediction
    ):

        content = str(
            prediction.get(
                "content",
                ""
            )
        ).strip()

        if not content:

            return None

        confidence = self._clamp(
            prediction.get(
                "confidence",
                0.5
            ),
            0.5
        )

        importance = self._clamp(
            prediction.get(
                "importance",
                0.5
            ),
            0.5
        )

        prediction_type = (
            prediction.get(
                "prediction_type",
                "general"
            )
        )

        horizon_hours = float(
            prediction.get(
                "horizon_hours",
                24
            )
        )

        expires_at = (
            datetime.now()
            +
            timedelta(
                hours=horizon_hours
            )
        ).isoformat(
            timespec="seconds"
        )

        evidence = prediction.get(
            "evidence",
            []
        )

        metadata = {
            "prediction":
                True,

            "prediction_type":
                prediction_type,

            "prediction_status":
                "active",

            "evidence":
                evidence,

            "horizon_hours":
                horizon_hours,

            "evaluation":
                {
                    "evaluation_count":
                        0,

                    "success_count":
                        0,

                    "failure_count":
                        0,

                    "partial_count":
                        0
                }
        }

        existing = (
            self._find_similar(
                content
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

            old_eval = dict(
                existing_metadata.get(
                    "evaluation",
                    {}
                )
                or {}
            )

            metadata[
                "evaluation"
            ] = old_eval

            merged_evidence = list(
                existing_metadata.get(
                    "evidence",
                    []
                )
                or []
            )

            for item in evidence:

                if item not in merged_evidence:

                    merged_evidence.append(
                        item
                    )

            metadata[
                "evidence"
            ] = merged_evidence[-20:]

            updated = (
                self.store.update_memory(
                    existing["id"],

                    content=content,

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

                    memory_type="prediction",

                    category="prediction",

                    metadata=metadata,

                    expires_at=expires_at,

                    status="active"
                )
            )

            return {
                "action":
                    "reinforced",

                "memory":
                    updated
            }

        key = (
            "prediction_"
            +
            self._slug(
                prediction_type
                + "_"
                + content
            )
        )

        memory = self.memory.remember(
            content=content,

            key=key,

            memory_type="prediction",

            category="prediction",

            importance=importance,

            confidence=confidence,

            source="inferred",

            metadata=metadata,

            create_associations=True,

            explicit=False
        )

        if memory is None:

            return None

        # remember() no acepta expires_at directamente,
        # así que lo añadimos inmediatamente después.
        updated = (
            self.store.update_memory(
                memory["id"],
                expires_at=expires_at
            )
        )

        return {
            "action":
                "created",

            "memory":
                updated
        }

    # ==================================================
    # SIMILAR
    # ==================================================

    def _find_similar(
        self,
        content
    ):

        try:

            results = (
                self.memory.search(
                    content,
                    limit=10,
                    memory_type="prediction"
                )
            )

        except Exception:

            return None

        for result in results:

            metadata = (
                result.get(
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
                "prediction",
                False
            ):

                continue

            if result.get(
                "status"
            ) != "active":

                continue

            relevance = max(
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

            if relevance >= 0.88:

                return result

        return None

    # ==================================================
    # ACTIVAS
    # ==================================================

    def active_predictions(
        self,
        limit=20
    ):

        predictions = (
            self.store.list_memories(
                memory_type="prediction",
                status="active",
                limit=limit
            )
        )

        now = datetime.now()

        result = []

        for prediction in predictions:

            expires_at = (
                prediction.get(
                    "expires_at"
                )
            )

            if expires_at:

                try:

                    expires = (
                        datetime.fromisoformat(
                            expires_at
                        )
                    )

                    if expires <= now:

                        self._expire(
                            prediction
                        )

                        continue

                except Exception:

                    pass

            result.append(
                prediction
            )

        return result

    # ==================================================
    # EXPIRAR
    # ==================================================

    def expire_predictions(
        self,
        limit=1000
    ):

        predictions = (
            self.store.list_memories(
                memory_type="prediction",
                status="active",
                limit=limit
            )
        )

        now = datetime.now()

        expired = []

        for prediction in predictions:

            expires_at = (
                prediction.get(
                    "expires_at"
                )
            )

            if not expires_at:

                continue

            try:

                expires = (
                    datetime.fromisoformat(
                        expires_at
                    )
                )

            except Exception:

                continue

            if expires > now:

                continue

            if self._expire(
                prediction
            ):

                expired.append(
                    prediction["id"]
                )

        return expired

    def _expire(
        self,
        prediction
    ):

        metadata = dict(
            prediction.get(
                "metadata",
                {}
            )
            or {}
        )

        metadata[
            "prediction_status"
        ] = "expired"

        try:

            self.store.update_memory(
                prediction["id"],
                status="expired",
                metadata=metadata
            )

            return True

        except Exception:

            return False

    # ==================================================
    # JSON
    # ==================================================

    @staticmethod
    def _parse_json(
        response
    ):

        text = str(
            response or ""
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
    # UTILIDADES
    # ==================================================

    @staticmethod
    def _clamp(
        value,
        default=0.5
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

    @staticmethod
    def _slug(
        text
    ):

        result = []

        for character in str(
            text
        ).lower():

            if (
                character.isalnum()
                or
                character == "_"
            ):

                result.append(
                    character
                )

            else:

                result.append(
                    "_"
                )

        slug = "".join(
            result
        )

        while "__" in slug:

            slug = slug.replace(
                "__",
                "_"
            )

        return slug[:120].strip(
            "_"
        )