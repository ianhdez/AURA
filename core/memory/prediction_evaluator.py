import json
from datetime import datetime


class PredictionEvaluator:

    """
    Evalúa predicciones anteriores y ajusta su confianza.

    Resultados:

        correct
        incorrect
        partial
        unknown

    La evaluación produce aprendizaje sobre el propio sistema
    predictivo.

    Una predicción acertada aumenta ligeramente la confianza.

    Una predicción fallida la reduce con mayor intensidad.

    Una predicción parcialmente correcta recibe un ajuste pequeño.

    Las predicciones desconocidas no modifican la confianza.
    """

    VALID_OUTCOMES = {
        "correct",
        "incorrect",
        "partial",
        "unknown"
    }

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
    # EVALUAR DIRECTAMENTE
    # ==================================================

    def evaluate(
        self,
        prediction_id,
        outcome,
        evidence=None,
        notes=None
    ):

        outcome = (
            str(
                outcome or ""
            )
            .strip()
            .lower()
        )

        if outcome not in self.VALID_OUTCOMES:

            return {
                "success": False,
                "error":
                    "Resultado de predicción inválido."
            }

        prediction = (
            self.store.get_memory(
                prediction_id
            )
        )

        if prediction is None:

            return {
                "success": False,
                "error":
                    "Predicción no encontrada."
            }

        if prediction.get(
            "memory_type"
        ) != "prediction":

            return {
                "success": False,
                "error":
                    "La memoria indicada no es una predicción."
            }

        current_confidence = self._clamp(
            prediction.get(
                "confidence",
                0.5
            )
        )

        new_confidence = (
            self._adjust_confidence(
                current_confidence,
                outcome
            )
        )

        metadata = dict(
            prediction.get(
                "metadata",
                {}
            )
            or {}
        )

        stats = dict(
            metadata.get(
                "evaluation",
                {}
            )
            or {}
        )

        stats[
            "evaluation_count"
        ] = (
            int(
                stats.get(
                    "evaluation_count",
                    0
                )
            )
            + 1
        )

        if outcome == "correct":

            stats[
                "success_count"
            ] = (
                int(
                    stats.get(
                        "success_count",
                        0
                    )
                )
                + 1
            )

        elif outcome == "incorrect":

            stats[
                "failure_count"
            ] = (
                int(
                    stats.get(
                        "failure_count",
                        0
                    )
                )
                + 1
            )

        elif outcome == "partial":

            stats[
                "partial_count"
            ] = (
                int(
                    stats.get(
                        "partial_count",
                        0
                    )
                )
                + 1
            )

        if evidence is not None:

            stats[
                "last_evidence"
            ] = str(
                evidence
            )

        if notes is not None:

            stats[
                "last_notes"
            ] = str(
                notes
            )

        stats[
            "last_outcome"
        ] = outcome

        stats[
            "last_evaluated_at"
        ] = self._now()

        metadata[
            "evaluation"
        ] = stats

        metadata[
            "prediction_status"
        ] = (
            "confirmed"
            if outcome == "correct"
            else
            "rejected"
            if outcome == "incorrect"
            else
            "partial"
            if outcome == "partial"
            else
            "unknown"
        )

        updated = (
            self.store.update_memory(
                prediction_id,

                confidence=new_confidence,

                metadata=metadata,

                status=(
                    "archived"
                    if outcome in {
                        "correct",
                        "incorrect",
                        "partial"
                    }
                    else
                    "active"
                )
            )
        )

        return {
            "success": True,
            "prediction": updated,
            "outcome": outcome,
            "previous_confidence":
                current_confidence,
            "new_confidence":
                new_confidence
        }

    # ==================================================
    # EVALUAR AUTOMÁTICAMENTE
    # ==================================================

    def evaluate_from_message(
        self,
        user_message,
        predictions=None
    ):

        if not user_message:

            return []

        if self.model is None:

            return []

        if predictions is None:

            predictions = (
                self.memory
                .active_predictions(
                    limit=10
                )
            )

        if not predictions:

            return []

        candidates = []

        for prediction in predictions:

            if "memory" in prediction:

                prediction = (
                    prediction[
                        "memory"
                    ]
                )

            metadata = (
                prediction.get(
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

            candidates.append({
                "id":
                    prediction.get(
                        "id"
                    ),

                "content":
                    prediction.get(
                        "content",
                        ""
                    ),

                "type":
                    metadata.get(
                        "prediction_type",
                        "general"
                    ),

                "confidence":
                    prediction.get(
                        "confidence",
                        0.5
                    )
            })

        if not candidates:

            return []

        prompt = f"""
Eres el evaluador de predicciones de una IA personal llamada AURA.

Debes determinar si el siguiente mensaje del usuario aporta
evidencia de que alguna predicción anterior:

- ocurrió;
- no ocurrió;
- ocurrió parcialmente;
- todavía no puede determinarse.

PREDICCIONES:

{json.dumps(
    candidates,
    ensure_ascii=False,
    indent=2
)}

MENSAJE DEL USUARIO:

{user_message}

REGLAS:

- No fuerces una evaluación.
- No supongas que una predicción se cumplió solamente porque
  el usuario habló del mismo tema.
- "unknown" es preferible a una evaluación incorrecta.
- Una predicción de necesidad puede considerarse correcta si
  el mensaje muestra claramente que esa necesidad apareció.
- Una predicción de siguiente acción solo puede considerarse
  correcta si el usuario realmente realiza o anuncia esa acción.
- Una predicción parcial debe tener evidencia clara de que
  parte del resultado ocurrió.
- Devuelve únicamente predicciones sobre las que el mensaje
  aporte evidencia suficiente.

FORMATO:

{{
    "evaluations": [
        {{
            "prediction_id": "id",
            "outcome": "correct|incorrect|partial|unknown",
            "confidence": 0.0,
            "evidence": "explicación breve"
        }}
    ]
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
                            user_message
                    }
                ],
                tools=[]
            )

        except Exception:

            return []

        data = self._parse_json(
            response
        )

        if not isinstance(
            data,
            dict
        ):

            return []

        evaluations = data.get(
            "evaluations",
            []
        )

        if not isinstance(
            evaluations,
            list
        ):

            return []

        results = []

        for evaluation in evaluations:

            if not isinstance(
                evaluation,
                dict
            ):

                continue

            prediction_id = (
                evaluation.get(
                    "prediction_id"
                )
            )

            outcome = (
                evaluation.get(
                    "outcome"
                )
            )

            confidence = self._clamp(
                evaluation.get(
                    "confidence",
                    0.0
                )
            )

            if not prediction_id:

                continue

            if (
                outcome
                not in
                self.VALID_OUTCOMES
            ):

                continue

            # Exigimos evidencia suficiente para modificar
            # una predicción automáticamente.
            if confidence < 0.75:

                continue

            result = self.evaluate(
                prediction_id=prediction_id,
                outcome=outcome,
                evidence=evaluation.get(
                    "evidence"
                )
            )

            if result.get(
                "success"
            ):

                results.append(
                    result
                )

        return results

    # ==================================================
    # AJUSTAR CONFIANZA
    # ==================================================

    def _adjust_confidence(
        self,
        confidence,
        outcome
    ):

        confidence = self._clamp(
            confidence
        )

        if outcome == "correct":

            confidence += (
                self.config
                .PREDICTION_CORRECT_GAIN
                *
                (
                    1.0
                    -
                    confidence
                )
            )

        elif outcome == "incorrect":

            confidence -= (
                self.config
                .PREDICTION_INCORRECT_LOSS
                *
                max(
                    confidence,
                    0.25
                )
            )

        elif outcome == "partial":

            confidence += (
                self.config
                .PREDICTION_PARTIAL_GAIN
            )

        return max(
            self.config
            .PREDICTION_MIN_CONFIDENCE_AFTER_FAILURE,

            min(
                self.config
                .PREDICTION_MAX_CONFIDENCE,
                confidence
            )
        )

    # ==================================================
    # ESTADÍSTICAS
    # ==================================================

    def statistics(
        self,
        limit=1000
    ):

        predictions = (
            self.store.list_memories(
                memory_type="prediction",
                status="archived",
                limit=limit
            )
        )

        total = 0

        correct = 0

        incorrect = 0

        partial = 0

        for prediction in predictions:

            metadata = (
                prediction.get(
                    "metadata",
                    {}
                )
            )

            if not isinstance(
                metadata,
                dict
            ):

                continue

            evaluation = (
                metadata.get(
                    "evaluation",
                    {}
                )
            )

            if not isinstance(
                evaluation,
                dict
            ):

                continue

            total += int(
                evaluation.get(
                    "evaluation_count",
                    0
                )
            )

            correct += int(
                evaluation.get(
                    "success_count",
                    0
                )
            )

            incorrect += int(
                evaluation.get(
                    "failure_count",
                    0
                )
            )

            partial += int(
                evaluation.get(
                    "partial_count",
                    0
                )
            )

        evaluated = (
            correct
            +
            incorrect
            +
            partial
        )

        accuracy = (
            correct
            /
            evaluated
            if evaluated > 0
            else 0.0
        )

        return {
            "evaluations":
                total,

            "correct":
                correct,

            "incorrect":
                incorrect,

            "partial":
                partial,

            "evaluated":
                evaluated,

            "accuracy":
                accuracy
        }

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

        return datetime.now().isoformat(
            timespec="seconds"
        )