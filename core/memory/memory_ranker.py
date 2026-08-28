import math
from datetime import datetime


class MemoryRanker:

    """
    Clasifica recuerdos candidatos según múltiples factores.

    La posición física del recuerdo en SQLite nunca interviene
    en la puntuación.

    Factores utilizados:

    - relevancia textual
    - coincidencia de clave
    - coincidencia de categoría
    - coincidencia de tipo
    - importancia
    - confianza
    - recencia
    - frecuencia de acceso
    - coincidencia semántica cuando exista
    """

    def __init__(
        self,
        config
    ):

        self.config = config

    # ==================================================
    # RANKING
    # ==================================================

    def rank(
        self,
        candidates,
        query,
        limit=None
    ):

        if not candidates:

            return []

        if limit is None:

            limit = (
                self.config.MAX_SEARCH_RESULTS
            )

        ranked = []

        normalized_query = (
            self._normalize(
                query
            )
        )

        query_words = set(
            self._words(
                normalized_query
            )
        )

        for candidate in candidates:

            score_data = (
                self._score(
                    candidate,
                    normalized_query,
                    query_words
                )
            )

            candidate = dict(
                candidate
            )

            candidate.update(
                score_data
            )

            ranked.append(
                candidate
            )

        ranked.sort(
            key=lambda item: (
                item["score"],
                item.get(
                    "importance",
                    0.0
                ),
                item.get(
                    "confidence",
                    0.0
                ),
                item.get(
                    "updated_at",
                    ""
                )
            ),
            reverse=True
        )

        ranked = self._diversify(
            ranked,
            limit
        )

        return ranked

    # ==================================================
    # PUNTUACIÓN
    # ==================================================

    def _score(
        self,
        memory,
        query,
        query_words
    ):

        key = self._normalize(
            memory.get(
                "memory_key",
                memory.get(
                    "key",
                    ""
                )
            )
        )

        content = self._normalize(
            memory.get(
                "content",
                ""
            )
        )

        category = self._normalize(
            memory.get(
                "category",
                ""
            )
        )

        memory_type = self._normalize(
            memory.get(
                "memory_type",
                ""
            )
        )

        keyword_text = self._normalize(
            " ".join(
                memory.get(
                    "keywords",
                    []
                )
            )
        )

        searchable = " ".join([
            key,
            content,
            category,
            memory_type,
            keyword_text
        ]).strip()

        # --------------------------------------------------
        # Coincidencia textual
        # --------------------------------------------------

        keyword_score = (
            self._keyword_relevance(
                query,
                query_words,
                key,
                content,
                category,
                memory_type,
                keyword_text
            )
        )

        # --------------------------------------------------
        # Coincidencia exacta de clave
        # --------------------------------------------------

        exact_score = 0.0

        if query and query == key:

            exact_score = 1.0

        elif (
            query
            and query in key
        ):

            exact_score = 0.7

        # --------------------------------------------------
        # Coincidencia de contenido
        # --------------------------------------------------

        phrase_score = 0.0

        if (
            query
            and query in searchable
        ):

            phrase_score = 1.0

        # --------------------------------------------------
        # Importancia
        # --------------------------------------------------

        importance = self._clamp(
            memory.get(
                "importance",
                0.5
            )
        )

        # --------------------------------------------------
        # Confianza
        # --------------------------------------------------

        confidence = self._clamp(
            memory.get(
                "confidence",
                1.0
            )
        )

        # --------------------------------------------------
        # Recencia
        # --------------------------------------------------

        recency = self._recency(
            memory
        )

        # --------------------------------------------------
        # Frecuencia
        # --------------------------------------------------

        frequency = self._frequency(
            memory
        )

        # --------------------------------------------------
        # Embedding si existe
        # --------------------------------------------------

        semantic = self._clamp(
            memory.get(
                "semantic_score",
                0.0
            )
        )

        # --------------------------------------------------
        # SCORE FINAL
        # --------------------------------------------------

        relevance = (
            keyword_score * 0.45
            +
            semantic * 0.35
            +
            exact_score * 0.15
            +
            phrase_score * 0.05
        )

        score = (
            relevance * self.config.RELEVANCE_WEIGHT
            +
            importance * self.config.IMPORTANCE_WEIGHT
            +
            recency * self.config.RECENCY_WEIGHT
            +
            confidence * self.config.CONFIDENCE_WEIGHT
            +
            frequency * self.config.FREQUENCY_WEIGHT
        )

        return {
            "score": score,
            "relevance": relevance,
            "keyword_score": keyword_score,
            "semantic_score": semantic,
            "importance_score": importance,
            "recency_score": recency,
            "confidence_score": confidence,
            "frequency_score": frequency
        }

    # ==================================================
    # RELEVANCIA TEXTUAL
    # ==================================================

    def _keyword_relevance(
        self,
        query,
        query_words,
        key,
        content,
        category,
        memory_type,
        keyword_text
    ):

        if not query_words:

            return 0.0

        key_words = set(
            self._words(
                key
            )
        )

        content_words = set(
            self._words(
                content
            )
        )

        category_words = set(
            self._words(
                category
            )
        )

        type_words = set(
            self._words(
                memory_type
            )
        )

        keyword_words = set(
            self._words(
                keyword_text
            )
        )

        score = 0.0

        total = len(
            query_words
        )

        for word in query_words:

            if word in key_words:

                score += 1.0

            elif word in keyword_words:

                score += 0.85

            elif word in category_words:

                score += 0.65

            elif word in type_words:

                score += 0.55

            elif word in content_words:

                score += 0.45

            else:

                similarity = (
                    self._best_similarity(
                        word,
                        (
                            key_words
                            |
                            keyword_words
                            |
                            category_words
                            |
                            content_words
                        )
                    )
                )

                if similarity >= 0.90:

                    score += 0.40

                elif similarity >= 0.80:

                    score += 0.25

        return min(
            1.0,
            score / total
        )

    # ==================================================
    # SIMILITUD DE PALABRA
    # ==================================================

    @staticmethod
    def _best_similarity(
        word,
        candidates
    ):

        if not candidates:

            return 0.0

        best = 0.0

        for candidate in candidates:

            if not candidate:

                continue

            same = 0

            length = max(
                len(word),
                len(candidate)
            )

            for index in range(
                min(
                    len(word),
                    len(candidate)
                )
            ):

                if word[index] == candidate[index]:

                    same += 1

            similarity = (
                same / length
            )

            if similarity > best:

                best = similarity

        return best

    # ==================================================
    # RECENCIA
    # ==================================================

    def _recency(
        self,
        memory
    ):

        timestamp = (
            memory.get(
                "updated_at"
            )
            or
            memory.get(
                "created_at"
            )
        )

        if not timestamp:

            return 0.5

        try:

            date = datetime.fromisoformat(
                timestamp
            )

        except Exception:

            return 0.5

        age = (
            datetime.now()
            - date
        ).total_seconds()

        days = max(
            0.0,
            age / 86400.0
        )

        return math.exp(
            -days / 90.0
        )

    # ==================================================
    # FRECUENCIA
    # ==================================================

    def _frequency(
        self,
        memory
    ):

        count = max(
            0,
            int(
                memory.get(
                    "access_count",
                    0
                )
            )
        )

        return min(
            1.0,
            math.log1p(
                count
            )
            /
            math.log(11)
        )

    # ==================================================
    # DIVERSIDAD
    # ==================================================

    def _diversify(
        self,
        memories,
        limit
    ):

        if len(memories) <= limit:

            return memories

        selected = []

        seen_types = set()
        seen_keys = set()

        # Primero recuerdos claramente fuertes.
        for memory in memories:

            if len(
                selected
            ) >= limit:

                break

            memory_type = memory.get(
                "memory_type",
                "general"
            )

            key = memory.get(
                "memory_key",
                memory.get(
                    "key"
                )
            )

            # Favorecemos diversidad cuando la
            # relevancia es parecida.

            if (
                memory_type not in seen_types
                or key not in seen_keys
            ):

                selected.append(
                    memory
                )

                seen_types.add(
                    memory_type
                )

                if key:
                    seen_keys.add(
                        key
                    )

        # Completar si aún faltan resultados.

        if len(selected) < limit:

            for memory in memories:

                if memory in selected:

                    continue

                selected.append(
                    memory
                )

                if len(selected) >= limit:

                    break

        return selected

    # ==================================================
    # PALABRAS
    # ==================================================

    @staticmethod
    def _words(
        text
    ):

        text = str(
            text or ""
        ).lower()

        separators = (
            ",.;:!?¿¡()[]{}\"'/-"
        )

        for separator in separators:

            text = text.replace(
                separator,
                " "
            )

        return [
            word
            for word in text.split()
            if word
        ]

    # ==================================================
    # NORMALIZACIÓN
    # ==================================================

    @staticmethod
    def _normalize(
        text
    ):

        return " ".join(
            MemoryRanker._words(
                text
            )
        ).strip()

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

            value = 0.0

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )