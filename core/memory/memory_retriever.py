import math
from datetime import datetime


class MemoryRetriever:

    """
    Recuperación híbrida de AURA.

    Combina:

    - FTS5 / búsqueda textual
    - embeddings semánticos
    - importancia
    - confianza
    - recencia
    - frecuencia
    - diversidad

    Nunca depende de la posición del recuerdo.
    """

    def __init__(
        self,
        store,
        config,
        embedding_engine=None
    ):

        self.store = store

        self.config = config

        self.embedding_engine = (
            embedding_engine
        )

    # ==================================================
    # SEARCH
    # ==================================================

    def search(
        self,
        query,
        limit=None,
        memory_type=None
    ):

        if not query:

            return []

        if limit is None:

            limit = (
                self.config.DEFAULT_SEARCH_LIMIT
            )

        limit = max(
            1,
            min(
                int(limit),
                self.config.MAX_SEARCH_LIMIT
            )
        )

        candidate_limit = max(
            50,
            limit * 6
        )

        # --------------------------------------------------
        # RECUPERACIÓN LÉXICA
        # --------------------------------------------------

        lexical = self.store.search_fts(
            query,
            limit=candidate_limit
        )

        # --------------------------------------------------
        # RECUPERACIÓN SEMÁNTICA
        # --------------------------------------------------

        semantic = []

        if (
            self.embedding_engine is not None
            and self.config.ENABLE_EMBEDDINGS
        ):

            try:

                semantic = (
                    self._semantic_search(
                        query,
                        candidate_limit
                    )
                )

            except Exception:

                # La memoria textual sigue funcionando
                # aunque temporalmente no esté disponible
                # el motor de embeddings.

                semantic = []

        # --------------------------------------------------
        # FUSIÓN
        # --------------------------------------------------

        merged = (
            self._merge_candidates(
                lexical,
                semantic
            )
        )

        if memory_type:

            merged = [
                item
                for item in merged
                if item.get(
                    "memory_type"
                ) == memory_type
            ]

        if not merged:

            return []

        # --------------------------------------------------
        # RANKING
        # --------------------------------------------------

        ranked = []

        for memory in merged:

            score_data = (
                self._score(
                    memory,
                    query
                )
            )

            item = dict(
                memory
            )

            item.update(
                score_data
            )

            ranked.append(
                item
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

        results = []

        for memory in ranked:

            self.store.register_access(
                memory["id"]
            )

            results.append(
                memory
            )

        return results

    # ==================================================
    # SEMÁNTICA
    # ==================================================

    def _semantic_search(
        self,
        query,
        limit
    ):

        query_vector = (
            self.embedding_engine.encode(
                query
            )
        )

        if not query_vector:

            return []

        stored = (
            self.store.list_embeddings(
                limit=100000
            )
        )

        if not stored:

            return []

        results = []

        for memory in stored:

            vector = memory.get(
                "vector",
                []
            )

            if not vector:

                continue

            if len(vector) != len(
                query_vector
            ):

                continue

            similarity = (
                self._cosine_similarity(
                    query_vector,
                    vector
                )
            )

            if similarity <= 0:

                continue

            item = dict(
                memory
            )

            item["semantic_score"] = (
                similarity
            )

            item["relevance"] = (
                similarity
            )

            results.append(
                item
            )

        results.sort(
            key=lambda item:
                item.get(
                    "semantic_score",
                    0.0
                ),
            reverse=True
        )

        return results[
            :limit
        ]

    # ==================================================
    # COSENO
    # ==================================================

    @staticmethod
    def _cosine_similarity(
        a,
        b
    ):

        dot = 0.0

        norm_a = 0.0

        norm_b = 0.0

        for x, y in zip(
            a,
            b
        ):

            x = float(x)

            y = float(y)

            dot += (
                x * y
            )

            norm_a += (
                x * x
            )

            norm_b += (
                y * y
            )

        if (
            norm_a <= 0
            or norm_b <= 0
        ):

            return 0.0

        return (
            dot
            /
            (
                math.sqrt(norm_a)
                *
                math.sqrt(norm_b)
            )
        )

    # ==================================================
    # FUSIÓN
    # ==================================================

    def _merge_candidates(
        self,
        lexical,
        semantic
    ):

        merged = {}

        for item in lexical:

            memory_id = item.get(
                "id"
            )

            if not memory_id:

                continue

            merged[
                memory_id
            ] = dict(item)

            merged[
                memory_id
            ]["keyword_score"] = float(
                item.get(
                    "relevance",
                    0.0
                )
            )

        for item in semantic:

            memory_id = item.get(
                "id"
            )

            if not memory_id:

                continue

            if memory_id not in merged:

                merged[
                    memory_id
                ] = dict(item)

            else:

                merged[
                    memory_id
                ].update({
                    key: value
                    for key, value in item.items()
                    if key not in {
                        "keyword_score"
                    }
                })

            merged[
                memory_id
            ]["semantic_score"] = float(
                item.get(
                    "semantic_score",
                    0.0
                )
            )

        return list(
            merged.values()
        )

    # ==================================================
    # SCORE
    # ==================================================

    def _score(
        self,
        memory,
        query
    ):

        keyword = self._clamp(
            memory.get(
                "keyword_score",
                0.0
            )
        )

        semantic = self._clamp(
            memory.get(
                "semantic_score",
                0.0
            )
        )

        # Cuando ambas búsquedas coinciden,
        # el recuerdo recibe mayor confianza.
        agreement = (
            min(
                keyword,
                semantic
            )
            if keyword > 0
            and semantic > 0
            else 0.0
        )

        relevance = (
            keyword * 0.35
            +
            semantic * 0.50
            +
            agreement * 0.15
        )

        importance = self._clamp(
            memory.get(
                "importance",
                0.5
            )
        )

        confidence = self._clamp(
            memory.get(
                "confidence",
                1.0
            )
        )

        recency = self._recency(
            memory
        )

        frequency = self._frequency(
            memory
        )

        score = (
            relevance
            * self.config.RELEVANCE_WEIGHT
            +
            importance
            * self.config.IMPORTANCE_WEIGHT
            +
            recency
            * self.config.RECENCY_WEIGHT
            +
            confidence
            * self.config.CONFIDENCE_WEIGHT
            +
            frequency
            * self.config.FREQUENCY_WEIGHT
        )

        return {
            "score": score,

            "relevance": relevance,

            "keyword_score": keyword,

            "semantic_score": semantic,

            "importance_score": importance,

            "recency_score": recency,

            "confidence_score": confidence,

            "frequency_score": frequency
        }

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

        age_days = max(
            0.0,
            (
                datetime.now()
                - date
            ).total_seconds()
            / 86400.0
        )

        return math.exp(
            -age_days / 90.0
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

        if len(
            memories
        ) <= limit:

            return memories

        selected = []

        seen_types = set()

        seen_keys = set()

        # Primero intentamos evitar que todos los
        # recuerdos recuperados sean del mismo tipo.

        for memory in memories:

            if len(
                selected
            ) >= limit:

                break

            memory_type = (
                memory.get(
                    "memory_type",
                    "general"
                )
            )

            key = (
                memory.get(
                    "memory_key"
                )
                or
                memory.get(
                    "key"
                )
            )

            if (
                memory_type
                not in seen_types
                or
                key
                not in seen_keys
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

        if len(
            selected
        ) < limit:

            for memory in memories:

                if memory in selected:

                    continue

                selected.append(
                    memory
                )

                if len(
                    selected
                ) >= limit:

                    break

        return selected

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

            return 0.0

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )