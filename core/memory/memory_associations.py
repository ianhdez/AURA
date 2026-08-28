import math


class MemoryAssociator:

    """
    Construye asociaciones entre recuerdos.

    La memoria de AURA no debe ser una colección de elementos
    independientes. Los recuerdos relevantes deben poder
    conectarse entre sí.

    Las asociaciones pueden surgir por:

    - similitud semántica
    - coincidencia textual
    - misma categoría
    - mismo tipo de memoria
    - etiquetas compartidas
    - relaciones conceptualmente cercanas

    Este componente NO elimina recuerdos.

    Solo crea y refuerza conexiones.
    """

    def __init__(
        self,
        memory_manager,
        config
    ):

        self.memory = memory_manager

        self.store = (
            memory_manager.store
        )

        self.retriever = (
            memory_manager.retriever
        )

        self.config = config

        # --------------------------------------------------
        # Umbrales
        # --------------------------------------------------

        self.strong_similarity = 0.88

        self.medium_similarity = 0.75

        self.minimum_similarity = 0.68

        self.maximum_relations_per_memory = 8

    # ==================================================
    # ASOCIAR MEMORIA
    # ==================================================

    def associate(
        self,
        memory
    ):

        if not memory:

            return []

        memory_id = memory.get(
            "id"
        )

        if not memory_id:

            return []

        query = (
            self._build_query(
                memory
            )
        )

        if not query:

            return []

        try:

            candidates = (
                self.retriever.search(
                    query,
                    limit=20
                )
            )

        except Exception:

            return []

        if not candidates:

            return []

        relations = []

        existing_relations = (
            self.store.get_relations(
                memory_id
            )
        )

        existing_pairs = set()

        for relation in existing_relations:

            source = relation.get(
                "source_id"
            )

            target = relation.get(
                "target_id"
            )

            existing_pairs.add(
                tuple(
                    sorted(
                        [
                            source,
                            target
                        ]
                    )
                )
            )

        for candidate in candidates:

            candidate_id = candidate.get(
                "id"
            )

            if not candidate_id:

                continue

            if candidate_id == memory_id:

                continue

            pair = tuple(
                sorted(
                    [
                        memory_id,
                        candidate_id
                    ]
                )
            )

            if pair in existing_pairs:

                continue

            similarity = (
                self._similarity(
                    memory,
                    candidate
                )
            )

            if (
                similarity
                <
                self.minimum_similarity
            ):

                continue

            relation_type = (
                self._infer_relation(
                    memory,
                    candidate
                )
            )

            weight = (
                self._relation_weight(
                    similarity,
                    memory,
                    candidate
                )
            )

            try:

                relation_id = (
                    self.store.add_relation(
                        source_id=memory_id,
                        target_id=candidate_id,
                        relation=relation_type,
                        weight=weight,
                        metadata={
                            "automatic": True,
                            "similarity": similarity
                        }
                    )
                )

            except Exception:

                continue

            relations.append({
                "relation_id": relation_id,
                "source_id": memory_id,
                "target_id": candidate_id,
                "relation": relation_type,
                "weight": weight,
                "similarity": similarity
            })

            existing_pairs.add(
                pair
            )

            if len(
                relations
            ) >= self.maximum_relations_per_memory:

                break

        return relations

    # ==================================================
    # CONSULTAR RED
    # ==================================================

    def related_memories(
        self,
        memory_id,
        limit=10
    ):

        relations = (
            self.store.get_relations(
                memory_id
            )
        )

        if not relations:

            return []

        result = []

        seen = set()

        for relation in relations:

            source = relation.get(
                "source_id"
            )

            target = relation.get(
                "target_id"
            )

            other_id = (
                target
                if source == memory_id
                else source
            )

            if not other_id:

                continue

            if other_id in seen:

                continue

            memory = (
                self.store.get_memory(
                    other_id
                )
            )

            if memory is None:

                continue

            if memory.get(
                "status"
            ) != "active":

                continue

            result.append({
                "memory": memory,
                "relation": relation
            })

            seen.add(
                other_id
            )

            if len(result) >= limit:

                break

        return result

    # ==================================================
    # CONSTRUIR CONSULTA
    # ==================================================

    @staticmethod
    def _build_query(
        memory
    ):

        key = (
            memory.get(
                "memory_key"
            )
            or
            memory.get(
                "key"
            )
            or
            ""
        )

        content = str(
            memory.get(
                "content",
                ""
            )
        )

        category = str(
            memory.get(
                "category",
                ""
            )
        )

        memory_type = str(
            memory.get(
                "memory_type",
                ""
            )
        )

        return " ".join([
            key,
            content,
            category,
            memory_type
        ]).strip()

    # ==================================================
    # SIMILITUD
    # ==================================================

    def _similarity(
        self,
        source,
        target
    ):

        semantic = float(
            target.get(
                "semantic_score",
                0.0
            )
        )

        relevance = float(
            target.get(
                "relevance",
                0.0
            )
        )

        # Cuando hay embedding, damos prioridad a la
        # similitud semántica.

        if semantic > 0:

            base = semantic

        else:

            base = relevance

        if (
            source.get(
                "category"
            )
            ==
            target.get(
                "category"
            )
            and
            source.get(
                "category"
            )
        ):

            base += 0.05

        if (
            source.get(
                "memory_type"
            )
            ==
            target.get(
                "memory_type"
            )
        ):

            base += 0.03

        return min(
            1.0,
            base
        )

    # ==================================================
    # TIPO DE RELACIÓN
    # ==================================================

    def _infer_relation(
        self,
        source,
        target
    ):

        source_type = str(
            source.get(
                "memory_type",
                ""
            )
        ).lower()

        target_type = str(
            target.get(
                "memory_type",
                ""
            )
        ).lower()

        source_category = str(
            source.get(
                "category",
                ""
            )
        ).lower()

        target_category = str(
            target.get(
                "category",
                ""
            )
        ).lower()

        # --------------------------------------------------
        # Proyecto → conocimiento / habilidad
        # --------------------------------------------------

        if source_type == "project":

            if target_type == "skill":

                return "uses_skill"

            if target_type == "knowledge":

                return "uses_knowledge"

            if target_type == "preference":

                return "related_preference"

        # --------------------------------------------------
        # Preferencias
        # --------------------------------------------------

        if source_type == "preference":

            if target_type == "preference":

                return "related_preference"

            if target_type == "knowledge":

                return "related_knowledge"

        # --------------------------------------------------
        # Hábitos
        # --------------------------------------------------

        if source_type == "habit":

            return "related_habit"

        # --------------------------------------------------
        # Habilidades
        # --------------------------------------------------

        if source_type == "skill":

            if target_type == "skill":

                return "related_skill"

            if target_type == "knowledge":

                return "requires_knowledge"

        # --------------------------------------------------
        # Conocimientos
        # --------------------------------------------------

        if source_type == "knowledge":

            if target_type == "knowledge":

                return "related_knowledge"

        # --------------------------------------------------
        # Categorías iguales
        # --------------------------------------------------

        if (
            source_category
            and
            source_category == target_category
        ):

            return "same_topic"

        # --------------------------------------------------
        # Fallback
        # --------------------------------------------------

        return "related"

    # ==================================================
    # PESO
    # ==================================================

    def _relation_weight(
        self,
        similarity,
        source,
        target
    ):

        weight = float(
            similarity
        )

        if (
            source.get(
                "category"
            )
            ==
            target.get(
                "category"
            )
            and
            source.get(
                "category"
            )
        ):

            weight += 0.05

        if (
            source.get(
                "memory_type"
            )
            ==
            target.get(
                "memory_type"
            )
        ):

            weight += 0.03

        return max(
            0.0,
            min(
                1.0,
                weight
            )
        )