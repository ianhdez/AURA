import json


class MemoryConflictResolver:

    """
    Gestiona cambios, contradicciones y evolución de recuerdos.

    Estados conceptuales:

        keep
            La información nueva confirma la existente.

        update
            La información amplía o mejora el recuerdo actual.

        supersede
            La información nueva sustituye al recuerdo anterior.

        contradict
            Existe una incompatibilidad, pero todavía no hay
            suficiente evidencia para decidir cuál debe prevalecer.

        related
            Ambas informaciones son compatibles pero diferentes.

    Principio fundamental:

        Nunca destruir información histórica.

    Cuando un recuerdo es sustituido:

        antiguo -> superseded
        nuevo   -> active

    Cuando la situación es incierta:

        recuerdo actual -> active
        nueva información -> uncertain
    """

    def __init__(
        self,
        memory_manager,
        model=None
    ):

        self.memory = memory_manager

        self.store = (
            memory_manager.store
        )

        self.config = (
            memory_manager.config
        )

        self.model = model

    # ==================================================
    # RESOLVER
    # ==================================================

    def resolve(
        self,
        content,
        key=None,
        memory_type="general",
        category="general",
        importance=0.5,
        confidence=1.0,
        source="conversation",
        metadata=None,
        explicit=False
    ):

        content = str(
            content or ""
        ).strip()

        if not content:

            return {
                "action": "ignored",
                "memory": None
            }

        if key is not None:

            key = (
                str(key)
                .strip()
                .lower()
            )

            if not key:

                key = None

        existing = None

        if key:

            existing = (
                self.store.get_by_key(
                    key
                )
            )

        # --------------------------------------------------
        # Sin clave.
        #
        # Una memoria sin clave no puede tener una identidad
        # absoluta. Se intenta localizar una coincidencia
        # semántica posteriormente.
        # --------------------------------------------------

        if existing is None and key is None:

            existing = (
                self._find_duplicate(
                    content
                )
            )

        # --------------------------------------------------
        # No existe.
        # --------------------------------------------------

        if existing is None:

            memory = (
                self._create_new(
                    content=content,
                    key=key,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence,
                    source=source,
                    metadata=metadata,
                    explicit=explicit
                )
            )

            return {
                "action": "created",
                "memory": memory
            }

        # --------------------------------------------------
        # Exactamente igual.
        # --------------------------------------------------

        if self._same_information(
            existing,
            content
        ):

            memory = (
                self._reinforce(
                    existing,
                    importance,
                    confidence
                )
            )

            return {
                "action": "reinforced",
                "memory": memory,
                "previous": existing
            }

        # --------------------------------------------------
        # Determinar relación.
        # --------------------------------------------------

        decision = (
            self._classify(
                existing,
                content=content,
                key=key,
                memory_type=memory_type,
                category=category,
                importance=importance,
                confidence=confidence,
                explicit=explicit
            )
        )

        action = decision.get(
            "action",
            "related"
        )

        # --------------------------------------------------
        # KEEP
        # --------------------------------------------------

        if action == "keep":

            memory = (
                self._reinforce(
                    existing,
                    importance,
                    confidence
                )
            )

            return {
                "action": "reinforced",
                "memory": memory,
                "previous": existing
            }

        # --------------------------------------------------
        # UPDATE
        # --------------------------------------------------

        if action == "update":

            memory = (
                self._update(
                    existing,
                    content=content,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence,
                    metadata=metadata
                )
            )

            return {
                "action": "updated",
                "memory": memory,
                "previous": existing,
                "reason": decision.get(
                    "reason",
                    ""
                )
            }

        # --------------------------------------------------
        # SUPERSEDE
        # --------------------------------------------------

        if action == "supersede":

            return (
                self._supersede(
                    existing,
                    content=content,
                    key=key,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence,
                    source=source,
                    metadata=metadata,
                    reason=decision.get(
                        "reason",
                        ""
                    )
                )
            )

        # --------------------------------------------------
        # CONTRADICCIÓN
        # --------------------------------------------------

        if action == "contradict":

            return (
                self._store_conflict(
                    existing,
                    content=content,
                    key=key,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence,
                    source=source,
                    metadata=metadata,
                    reason=decision.get(
                        "reason",
                        ""
                    )
                )
            )

        # --------------------------------------------------
        # RELATED
        # --------------------------------------------------

        if action == "related":

            self.store.add_relation(
                existing["id"],
                self._ensure_related_memory(
                    content=content,
                    key=key,
                    memory_type=memory_type,
                    category=category,
                    importance=importance,
                    confidence=confidence,
                    source=source,
                    metadata=metadata
                )["id"],
                "related",
                weight=(
                    decision.get(
                        "confidence",
                        0.5
                    )
                )
            )

            related = self._find_duplicate(
                content
            )

            return {
                "action": "related",
                "memory": existing,
                "related": related,
                "reason": decision.get(
                    "reason",
                    ""
                )
            }

        return {
            "action": "ignored",
            "memory": existing
        }

    # ==================================================
    # CREAR
    # ==================================================

    def _create_new(
        self,
        content,
        key,
        memory_type,
        category,
        importance,
        confidence,
        source,
        metadata,
        explicit=False
    ):

        memory_id = self.store.new_id(
            "mem"
        )

        metadata = dict(
            metadata or {}
        )

        metadata[
            "explicit"
        ] = bool(
            explicit
        )

        memory = self.store.save_memory(
            memory_id=memory_id,
            memory_type=memory_type,
            key=key,
            content=content,
            category=category,
            importance=self.config.clamp_importance(
                importance
            ),
            confidence=self.config.clamp_confidence(
                confidence
            ),
            source=source,
            metadata=metadata
        )

        self.memory._update_embedding(
            memory
        )

        self.memory._associate_safely(
            memory
        )

        return memory

    # ==================================================
    # ACTUALIZAR
    # ==================================================

    def _update(
        self,
        existing,
        content,
        memory_type,
        category,
        importance,
        confidence,
        metadata
    ):

        merged_metadata = dict(
            existing.get(
                "metadata",
                {}
            )
            or {}
        )

        if metadata:

            merged_metadata.update(
                metadata
            )

        merged_metadata[
            "last_change_type"
        ] = "update"

        memory = (
            self.store.update_memory(
                existing["id"],
                content=content,
                memory_type=memory_type,
                category=category,
                importance=max(
                    float(
                        existing.get(
                            "importance",
                            0.5
                        )
                    ),
                    self.config.clamp_importance(
                        importance
                    )
                ),
                confidence=self.config.clamp_confidence(
                    confidence
                ),
                metadata=merged_metadata
            )
        )

        self.memory._update_embedding(
            memory
        )

        self.memory._associate_safely(
            memory
        )

        return memory

    # ==================================================
    # SUPERSEDE
    # ==================================================

    def _supersede(
        self,
        existing,
        content,
        key,
        memory_type,
        category,
        importance,
        confidence,
        source,
        metadata,
        reason
    ):

        metadata = dict(
            metadata or {}
        )

        metadata.update({
            "supersedes":
                existing["id"],

            "change_reason":
                reason,

            "versioned":
                True
        })

        new_id = self.store.new_id(
            "mem"
        )

        new_memory = self.store.save_memory(
            memory_id=new_id,
            memory_type=memory_type,
            key=(
                key
                or
                existing.get(
                    "memory_key"
                )
            ),
            content=content,
            category=category,
            importance=self.config.clamp_importance(
                importance
            ),
            confidence=self.config.clamp_confidence(
                confidence
            ),
            source=source,
            metadata=metadata,
            status="active",
            supersedes=existing["id"]
        )

        self.store.update_memory(
            existing["id"],
            status="superseded",
            superseded_by=new_id
        )

        self.store.add_relation(
            existing["id"],
            new_id,
            "superseded_by",
            weight=1.0,
            metadata={
                "reason":
                    reason
            }
        )

        self.store.add_relation(
            new_id,
            existing["id"],
            "supersedes",
            weight=1.0,
            metadata={
                "reason":
                    reason
            }
        )

        self.memory._update_embedding(
            new_memory
        )

        self.memory._associate_safely(
            new_memory
        )

        return {
            "action": "superseded",
            "previous": existing,
            "memory": new_memory,
            "reason": reason
        }

    # ==================================================
    # CONFLICTO
    # ==================================================

    def _store_conflict(
        self,
        existing,
        content,
        key,
        memory_type,
        category,
        importance,
        confidence,
        source,
        metadata,
        reason
    ):

        metadata = dict(
            metadata or {}
        )

        metadata.update({
            "conflict":
                True,

            "conflicts_with":
                existing["id"],

            "conflict_reason":
                reason
        })

        new_id = self.store.new_id(
            "mem"
        )

        conflict_memory = (
            self.store.save_memory(
                memory_id=new_id,
                memory_type=memory_type,
                key=key,
                content=content,
                category=category,
                importance=self.config.clamp_importance(
                    importance
                ),
                confidence=self.config.clamp_confidence(
                    confidence
                ),
                source=source,
                metadata=metadata,
                status="uncertain"
            )
        )

        self.store.add_relation(
            existing["id"],
            new_id,
            "contradicts",
            weight=self.config.clamp_confidence(
                confidence
            ),
            metadata={
                "reason":
                    reason
            }
        )

        self.store.add_relation(
            new_id,
            existing["id"],
            "contradicts",
            weight=self.config.clamp_confidence(
                confidence
            ),
            metadata={
                "reason":
                    reason
            }
        )

        return {
            "action": "contradict",
            "previous": existing,
            "memory": conflict_memory,
            "reason": reason
        }

    # ==================================================
    # RELATED
    # ==================================================

    def _ensure_related_memory(
        self,
        content,
        key,
        memory_type,
        category,
        importance,
        confidence,
        source,
        metadata
    ):

        existing = None

        if key:

            existing = (
                self.store.get_by_key(
                    key
                )
            )

        if existing:

            return existing

        return self._create_new(
            content=content,
            key=key,
            memory_type=memory_type,
            category=category,
            importance=importance,
            confidence=confidence,
            source=source,
            metadata=metadata,
            explicit=False
        )

    # ==================================================
    # REFORZAR
    # ==================================================

    def _reinforce(
        self,
        existing,
        importance,
        confidence
    ):

        current_confidence = (
            self.config.clamp_confidence(
                existing.get(
                    "confidence",
                    0.5
                )
            )
        )

        incoming_confidence = (
            self.config.clamp_confidence(
                confidence
            )
        )

        # Evidencia repetida aumenta la confianza
        # de manera progresiva, pero con rendimientos
        # decrecientes.

        gain = (
            0.12
            *
            incoming_confidence
            *
            (
                1.0
                -
                current_confidence
            )
        )

        new_confidence = (
            current_confidence
            +
            gain
        )

        new_importance = max(
            float(
                existing.get(
                    "importance",
                    0.5
                )
            ),
            self.config.clamp_importance(
                importance
            )
        )

        metadata = dict(
            existing.get(
                "metadata",
                {}
            )
            or {}
        )

        metadata[
            "reinforced"
        ] = True

        memory = (
            self.store.update_memory(
                existing["id"],
                importance=new_importance,
                confidence=new_confidence,
                metadata=metadata
            )
        )

        return memory

    # ==================================================
    # BUSCAR DUPLICADO
    # ==================================================

    def _find_duplicate(
        self,
        content
    ):

        if not content:

            return None

        try:

            results = (
                self.memory.search(
                    content,
                    limit=5
                )
            )

        except Exception:

            return None

        for item in results:

            semantic = float(
                item.get(
                    "semantic_score",
                    0.0
                )
            )

            relevance = float(
                item.get(
                    "relevance",
                    0.0
                )
            )

            if (
                semantic >= 0.93
                or
                relevance >= 0.94
            ):

                return item

        return None

    # ==================================================
    # CLASIFICAR
    # ==================================================

    def _classify(
        self,
        existing,
        content,
        key,
        memory_type,
        category,
        importance,
        confidence,
        explicit
    ):

        # --------------------------------------------------
        # Si no tenemos modelo, utilizamos reglas
        # conservadoras.
        # --------------------------------------------------

        if self.model is None:

            return self._heuristic_classify(
                existing,
                content,
                key,
                memory_type,
                category,
                explicit
            )

        prompt = f"""
Eres el sistema de control de versiones de memoria de AURA.

Debes comparar una memoria vigente con nueva información
procedente del usuario.

MEMORIA ACTUAL:

{json.dumps(
    existing,
    ensure_ascii=False,
    indent=2
)}

NUEVA INFORMACIÓN:

{json.dumps(
    {
        "key": key,
        "content": content,
        "memory_type": memory_type,
        "category": category,
        "importance": importance,
        "confidence": confidence,
        "explicit": explicit
    },
    ensure_ascii=False,
    indent=2
)}

ACCIONES:

keep
La nueva información confirma la existente.

update
La nueva información amplía o mejora la existente sin
cambiar su significado fundamental.

supersede
La nueva información indica que el estado anterior dejó
de ser válido y debe ser sustituido.

contradict
Las dos informaciones son incompatibles, pero no existe
suficiente evidencia para afirmar que la nueva sustituye
definitivamente a la anterior.

related
Son compatibles y distintas.

REGLAS:

- Una preferencia nueva puede sustituir una preferencia anterior.
- Un cambio explícito del usuario tiene mucho peso.
- "Ya no", "ahora", "he cambiado", "antes", "actualmente"
  son señales importantes de cambio.
- Una afirmación vaga no debe sustituir un recuerdo firme.
- Nunca inventes una contradicción.
- Nunca confundas ampliación con sustitución.
- No elimines información histórica.

Devuelve exclusivamente:

{{
    "action": "keep|update|supersede|contradict|related",
    "confidence": 0.0,
    "reason": "motivo breve"
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
                            "Determina la relación."
                    }
                ],
                tools=[]
            )

        except Exception:

            return self._heuristic_classify(
                existing,
                content,
                key,
                memory_type,
                category,
                explicit
            )

        result = (
            self._parse_json(
                response
            )
        )

        if result is None:

            return self._heuristic_classify(
                existing,
                content,
                key,
                memory_type,
                category,
                explicit
            )

        action = str(
            result.get(
                "action",
                "related"
            )
        ).strip().lower()

        if action not in {
            "keep",
            "update",
            "supersede",
            "contradict",
            "related"
        }:

            action = "related"

        try:

            confidence_value = float(
                result.get(
                    "confidence",
                    0.5
                )
            )

        except Exception:

            confidence_value = 0.5

        return {
            "action": action,
            "confidence": max(
                0.0,
                min(
                    1.0,
                    confidence_value
                )
            ),
            "reason": str(
                result.get(
                    "reason",
                    ""
                )
            )
        }

    # ==================================================
    # HEURÍSTICA
    # ==================================================

    def _heuristic_classify(
        self,
        existing,
        content,
        key,
        memory_type,
        category,
        explicit
    ):

        existing_text = str(
            existing.get(
                "content",
                ""
            )
        ).lower()

        new_text = str(
            content
        ).lower()

        change_markers = (
            "ya no",
            "ahora",
            "he cambiado",
            "cambie",
            "antes",
            "actualmente",
            "a partir de ahora",
            "desde ahora",
            "prefiero",
            "mi nuevo",
            "mi nueva"
        )

        has_change_marker = any(
            marker in new_text
            for marker in change_markers
        )

        stateful_types = {
            "preference",
            "personal",
            "habit",
            "project",
            "prediction",
            "pattern"
        }

        if (
            explicit
            and
            memory_type in stateful_types
        ):

            return {
                "action": "supersede",
                "confidence": 0.95,
                "reason":
                    "Nueva afirmación explícita sobre "
                    "un estado persistente."
            }

        if (
            has_change_marker
            and
            memory_type in stateful_types
        ):

            return {
                "action": "supersede",
                "confidence": 0.90,
                "reason":
                    "Se detectó lenguaje explícito de cambio."
            }

        # Si parece una ampliación pero no una contradicción.

        if (
            existing_text
            and
            existing_text in new_text
        ):

            return {
                "action": "update",
                "confidence": 0.80,
                "reason":
                    "La nueva información contiene "
                    "el recuerdo anterior."
            }

        return {
            "action": "related",
            "confidence": 0.50,
            "reason":
                "No hay evidencia suficiente "
                "para sustituir el recuerdo."
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
    # IGUAL
    # ==================================================

    @staticmethod
    def _same_information(
        existing,
        content
    ):

        old = (
            str(
                existing.get(
                    "content",
                    ""
                )
            )
            .strip()
            .casefold()
        )

        new = (
            str(
                content
            )
            .strip()
            .casefold()
        )

        return old == new