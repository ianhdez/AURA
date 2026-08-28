import hashlib
import json

from pathlib import Path

from .memory_config import MemoryConfig
from .memory_store import MemoryStore
from .memory_retriever import MemoryRetriever
from .episodic_memory import EpisodicMemory
from .memory_context import MemoryContextBuilder
from .embedding_engine import EmbeddingEngine
from .memory_associations import MemoryAssociator
from .working_memory import WorkingMemory
from .memory_consolidator import MemoryConsolidator
from .memory_conflicts import MemoryConflictResolver
from .user_profile import UserProfile
from .pattern_detector import PatternDetector
from .prediction_engine import PredictionEngine
from .prediction_evaluator import PredictionEvaluator
from .procedural_memory import ProceduralMemory
from .episode_analyzer import EpisodeAnalyzer


class MemoryManager:

    def __init__(
        self,
        base_dir
    ):

        self.base_dir = (
            Path(base_dir)
            .resolve()
        )

        self.config = MemoryConfig()

        database_path = (
            self.config.database_path(
                self.base_dir
            )
        )

        self.store = MemoryStore(
            database_path
        )

        self.embedding_engine = None

        if self.config.ENABLE_EMBEDDINGS:

            self.embedding_engine = (
                EmbeddingEngine(
                    self.base_dir,
                    self.config
                )
            )

        self.retriever = MemoryRetriever(
            self.store,
            self.config,
            self.embedding_engine
        )

        self.context_builder = (
            MemoryContextBuilder(
                self.config
            )
        )

        self.episodic = EpisodicMemory(
            self.store,
            self.config
        )

        self.episode_analyzer = (
            EpisodeAnalyzer(
                memory_manager=self,
                model=None
            )
        )

        self.episodic.attach_analyzer(
            self.episode_analyzer
        )

        self.associations = (
            MemoryAssociator(
                self,
                self.config
            )
        )

        self.working = WorkingMemory(
            max_items=40
        )

        self.consolidator = (
            MemoryConsolidator(
                model=None,
                memory_manager=self
            )
        )

        self.conflicts = (
            MemoryConflictResolver(
                memory_manager=self,
                model=None
            )
        )

        self.profile = (
            UserProfile(
                self
            )
        )

        self.pattern_detector = (
            PatternDetector(
                memory_manager=self,
                model=None
            )
        )

        self.predictions = (
            PredictionEngine(
                memory_manager=self,
                model=None
            )
        )

        self.prediction_evaluator = (
            PredictionEvaluator(
                memory_manager=self,
                model=None
            )
        )

        self.procedural = (
            ProceduralMemory(
                memory_manager=self,
                model=None
            )
        )

        self._migrate_legacy_memory()

    # ==================================================
    # MODELO
    # ==================================================

    def attach_model(
        self,
        model
    ):

        self.consolidator.model = model

        self.conflicts.model = model

        self.pattern_detector.model = model

        self.predictions.model = model

        self.prediction_evaluator.model = model

        self.procedural.model = model

        self.episode_analyzer.model = model

    # ==================================================
    # CONSOLIDACIÓN
    # ==================================================

    def consolidate(
        self
    ):

        result = {
            "memories": [],
            "patterns": [],
            "predictions": [],
            "procedures": [],
            "expired_predictions": [],
            "episodes": []
        }

        if (
            self.config.ENABLE_CONSOLIDATION
            and
            self.consolidator.model is not None
        ):

            try:

                consolidation = (
                    self.consolidator
                    .consolidate()
                )

                result[
                    "memories"
                ].extend(
                    consolidation.get(
                        "memories",
                        []
                    )
                )

            except Exception:

                pass

        if (
            self.config.ENABLE_PATTERN_DETECTION
            and
            self.pattern_detector.model is not None
        ):

            try:

                result[
                    "patterns"
                ].extend(
                    self.detect_patterns()
                )

            except Exception:

                pass

        try:

            result[
                "expired_predictions"
            ] = (
                self.expire_predictions()
            )

        except Exception:

            pass

        return result

    # ==================================================
    # EPISODIOS
    # ==================================================

    def analyze_episode(
        self,
        conversation_id,
        force=False
    ):

        if not self.config.ENABLE_EPISODIC_MEMORY:

            return None

        try:

            return (
                self.episode_analyzer
                .analyze(
                    conversation_id,
                    force=force
                )
            )

        except Exception:

            return None

    def create_episode_memory(
        self,
        conversation_id
    ):

        if not self.config.ENABLE_EPISODIC_MEMORY:

            return None

        if not self.config.EPISODIC_CREATE_SUMMARY_MEMORY:

            return None

        try:

            return (
                self.episode_analyzer
                .create_episode_memory(
                    conversation_id
                )
            )

        except Exception:

            return None

    def get_episode(
        self,
        conversation_id
    ):

        try:

            return (
                self.episode_analyzer
                .get_episode(
                    conversation_id
                )
            )

        except Exception:

            return None

    def search_episodes(
        self,
        query,
        limit=10
    ):

        try:

            return (
                self.episode_analyzer
                .search_episodes(
                    query,
                    limit
                )
            )

        except Exception:

            return []

    # ==================================================
    # PATRONES
    # ==================================================

    def detect_patterns(
        self,
        limit=10000
    ):

        if not self.config.ENABLE_PATTERN_DETECTION:

            return []

        try:

            return (
                self.pattern_detector.detect(
                    limit=limit
                )
            )

        except Exception:

            return []

    def get_pattern(
        self,
        key
    ):

        return self.store.get_by_key(
            key
        )

    def list_patterns(
        self,
        limit=100
    ):

        return self.store.list_memories(
            memory_type="pattern",
            status="active",
            limit=limit
        )

    # ==================================================
    # PREDICCIONES
    # ==================================================

    def predict(
        self,
        query=None,
        limit=5
    ):

        if not self.config.ENABLE_PREDICTION:

            return []

        try:

            self.expire_predictions()

            existing = (
                self.active_predictions(
                    limit=(
                        self.config
                        .PREDICTION_MAX_ACTIVE
                    )
                )
            )

            if (
                query is None
                and
                existing
            ):

                return existing[
                    :limit
                ]

            return (
                self.predictions.predict(
                    query=query,
                    limit=limit
                )
            )

        except Exception:

            return []

    def active_predictions(
        self,
        limit=20
    ):

        return (
            self.predictions
            .active_predictions(
                limit=limit
            )
        )

    def expire_predictions(
        self,
        limit=1000
    ):

        return (
            self.predictions
            .expire_predictions(
                limit=limit
            )
        )

    def evaluate_prediction(
        self,
        prediction_id,
        outcome,
        evidence=None,
        notes=None
    ):

        return (
            self.prediction_evaluator
            .evaluate(
                prediction_id=prediction_id,
                outcome=outcome,
                evidence=evidence,
                notes=notes
            )
        )

    def evaluate_predictions_from_message(
        self,
        user_message
    ):

        if not user_message:

            return []

        try:

            return (
                self.prediction_evaluator
                .evaluate_from_message(
                    user_message=user_message
                )
            )

        except Exception:

            return []

    def prediction_statistics(
        self
    ):

        return (
            self.prediction_evaluator
            .statistics()
        )

    # ==================================================
    # PROCEDIMIENTOS
    # ==================================================

    def learn_procedure(
        self,
        user_message,
        assistant_response,
        conversation_context=None
    ):

        if not self.config.ENABLE_PROCEDURAL_LEARNING:

            return []

        try:

            return (
                self.procedural.learn(
                    user_message=user_message,
                    assistant_response=assistant_response,
                    conversation_context=(
                        conversation_context
                        or []
                    )
                )
            )

        except Exception:

            return []

    def find_skill(
        self,
        query,
        limit=5
    ):

        try:

            return (
                self.procedural.find_skill(
                    query,
                    limit=limit
                )
            )

        except Exception:

            return []

    def get_skill(
        self,
        skill_key
    ):

        try:

            return (
                self.procedural
                .get_skill(
                    skill_key
                )
            )

        except Exception:

            return None

    def list_skills(
        self,
        limit=100,
        category=None
    ):

        try:

            return self.store.list_skills(
                limit=limit,
                category=category
            )

        except Exception:

            return []

    def start_skill_run(
        self,
        skill_key,
        metadata=None
    ):

        try:

            return self.procedural.start_run(
                skill_key,
                metadata=metadata
            )

        except Exception:

            return None

    def add_skill_step_result(
        self,
        run_id,
        step_number,
        outcome,
        notes=None
    ):

        try:

            return (
                self.procedural
                .add_step_result(
                    run_id=run_id,
                    step_number=step_number,
                    outcome=outcome,
                    notes=notes
                )
            )

        except Exception:

            return None

    def finish_skill_run(
        self,
        run_id,
        outcome,
        notes=None
    ):

        try:

            return (
                self.procedural
                .finish_run(
                    run_id=run_id,
                    outcome=outcome,
                    notes=notes
                )
            )

        except Exception:

            return False

    def procedural_statistics(
        self
    ):

        try:

            return (
                self.procedural
                .statistics()
            )

        except Exception:

            return {
                "skills": 0,
                "runs": 0,
                "success": 0,
                "failure": 0,
                "partial": 0,
                "reliability": 0.0
            }

    # ==================================================
    # PERFIL
    # ==================================================

    def get_profile(
        self,
        include_predictions=False,
        include_patterns=True
    ):

        return self.profile.build(
            include_predictions=(
                include_predictions
            ),
            include_patterns=(
                include_patterns
            )
        )

    def build_profile_context(
        self,
        max_chars=5000,
        include_predictions=False,
        include_patterns=True
    ):

        return self.profile.build_context(
            max_chars=max_chars,
            include_predictions=(
                include_predictions
            ),
            include_patterns=(
                include_patterns
            )
        )

    def get_profile_statistics(
        self
    ):

        return self.profile.statistics()

    # ==================================================
    # GUARDAR
    # ==================================================

    def remember(
        self,
        content,
        key=None,
        memory_type="general",
        category="general",
        importance=None,
        confidence=None,
        source="conversation",
        metadata=None,
        create_associations=True,
        explicit=False
    ):

        if content is None:

            raise ValueError(
                "No se puede guardar una memoria vacía."
            )

        content = str(
            content
        ).strip()

        if not content:

            raise ValueError(
                "No se puede guardar una memoria vacía."
            )

        memory_type = (
            str(
                memory_type
                or
                "general"
            )
            .strip()
            .lower()
        )

        if not self.config.is_valid_memory_type(
            memory_type
        ):

            memory_type = "general"

        category = (
            str(
                category
                or
                "general"
            )
            .strip()
            .lower()
        )

        importance = (
            self.config.clamp_importance(
                importance
                if importance is not None
                else
                self.config.DEFAULT_IMPORTANCE
            )
        )

        confidence = (
            self.config.clamp_confidence(
                confidence
                if confidence is not None
                else
                self.config.DEFAULT_CONFIDENCE
            )
        )

        result = (
            self.conflicts.resolve(
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

        return result.get(
            "memory"
        )

    # ==================================================
    # RECALL
    # ==================================================

    def recall(
        self,
        key
    ):

        if key is None:

            return None

        return self.store.get_by_key(
            str(key)
            .strip()
            .lower()
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

        return self.retriever.search(
            query,
            limit=limit,
            memory_type=memory_type
        )

    # ==================================================
    # CONTEXTO
    # ==================================================

    def retrieve_context(
        self,
        query,
        memory_limit=None,
        episode_limit=6,
        conversation_limit=6
    ):

        data = (
            self.retriever
            .retrieve_context(
                query=query,
                memory_limit=memory_limit,
                episode_limit=episode_limit,
                conversation_limit=conversation_limit
            )
        )

        memories = data.get(
            "memories",
            []
        )

        related = []

        seen = {
            item.get("id")
            for item in memories
            if item.get("id")
        }

        for memory in memories[
            :self.config.MAX_RELATED_MEMORY_ITEMS
        ]:

            try:

                related_items = (
                    self.associations
                    .related_memories(
                        memory["id"],
                        limit=4
                    )
                )

            except Exception:

                continue

            for item in related_items:

                related_memory = (
                    item.get(
                        "memory"
                    )
                )

                if not related_memory:

                    continue

                related_id = (
                    related_memory.get(
                        "id"
                    )
                )

                if (
                    not related_id
                    or
                    related_id in seen
                ):

                    continue

                related.append(
                    related_memory
                )

                seen.add(
                    related_id
                )

        data[
            "related_memories"
        ] = related

        relations = []

        for memory in memories:

            try:

                relations.extend(
                    self.store.get_relations(
                        memory["id"]
                    )
                )

            except Exception:

                continue

        unique = {}

        for relation in relations:

            relation_id = (
                relation.get(
                    "id"
                )
            )

            if relation_id:

                unique[
                    relation_id
                ] = relation

        data[
            "relations"
        ] = list(
            unique.values()
        )

        return data

    # ==================================================
    # BUILD CONTEXT
    # ==================================================

    def build_context(
        self,
        query,
        memory_limit=None,
        episode_limit=6,
        conversation_limit=6,
        include_profile=True,
        include_predictions=False
    ):

        data = self.retrieve_context(
            query=query,
            memory_limit=memory_limit,
            episode_limit=episode_limit,
            conversation_limit=conversation_limit
        )

        memories = list(
            data.get(
                "memories",
                []
            )
        )

        for related in data.get(
            "related_memories",
            []
        ):

            if related not in memories:

                memories.append(
                    related
                )

        persistent_context = (
            self.context_builder.build(
                memories=memories,
                episodes=data.get(
                    "episodes",
                    []
                ),
                relations=data.get(
                    "relations",
                    []
                ),
                conversations=data.get(
                    "conversations",
                    []
                )
            )
        )

        working_context = (
            self.build_working_context()
        )

        sections = []

        if working_context:

            sections.append(
                working_context
            )

        if include_profile:

            profile_context = (
                self.build_profile_context(
                    max_chars=4500,
                    include_predictions=(
                        include_predictions
                    ),
                    include_patterns=True
                )
            )

            if profile_context:

                sections.append(
                    profile_context
                )

        if persistent_context:

            sections.append(
                persistent_context
            )

        return "\n\n".join(
            sections
        )

    # ==================================================
    # UPDATE
    # ==================================================

    def update(
        self,
        key,
        content=None,
        memory_type=None,
        category=None,
        importance=None,
        confidence=None,
        metadata=None
    ):

        existing = self.recall(
            key
        )

        if existing is None:

            return {
                "updated": False,
                "key": key
            }

        if content is None:

            content = existing.get(
                "content",
                ""
            )

        result = (
            self.conflicts.resolve(
                content=content,
                key=key,
                memory_type=(
                    memory_type
                    or
                    existing.get(
                        "memory_type",
                        "general"
                    )
                ),
                category=(
                    category
                    or
                    existing.get(
                        "category",
                        "general"
                    )
                ),
                importance=(
                    importance
                    if importance is not None
                    else
                    existing.get(
                        "importance",
                        0.5
                    )
                ),
                confidence=(
                    confidence
                    if confidence is not None
                    else
                    existing.get(
                        "confidence",
                        1.0
                    )
                ),
                source="user_confirmed",
                metadata=metadata,
                explicit=True
            )
        )

        return {
            "updated": True,
            "action": result.get(
                "action"
            ),
            "memory": result.get(
                "memory"
            ),
            "previous": result.get(
                "previous"
            ),
            "reason": result.get(
                "reason"
            )
        }

    # ==================================================
    # FORGET
    # ==================================================

    def forget(
        self,
        key
    ):

        memory = self.recall(
            key
        )

        if memory is None:

            return {
                "deleted": False,
                "key": key
            }

        deleted = (
            self.store.delete_memory(
                memory["id"]
            )
        )

        return {
            "deleted": deleted,
            "key": key,
            "memory_id": memory["id"]
        }

    # ==================================================
    # LIST
    # ==================================================

    def list(
        self,
        memory_type=None,
        limit=100
    ):

        return self.store.list_memories(
            memory_type=memory_type,
            status="active",
            limit=limit
        )

    # ==================================================
    # RELACIONES
    # ==================================================

    def relate(
        self,
        source_key,
        target_key,
        relation,
        weight=1.0
    ):

        source = self.recall(
            source_key
        )

        target = self.recall(
            target_key
        )

        if not source or not target:

            return {
                "success": False,
                "error":
                    "No se encontraron ambas memorias."
            }

        relation_id = (
            self.store.add_relation(
                source["id"],
                target["id"],
                relation,
                weight
            )
        )

        return {
            "success": True,
            "relation_id": relation_id
        }

    def relations(
        self,
        key
    ):

        memory = self.recall(
            key
        )

        if not memory:

            return []

        return self.store.get_relations(
            memory["id"]
        )

    # ==================================================
    # WORKING MEMORY
    # ==================================================

    def start_working_memory(
        self,
        session_id=None,
        metadata=None
    ):

        self.working.start(
            session_id=session_id,
            metadata=metadata
        )

        return self.working.get_state()

    def clear_working_memory(
        self
    ):

        self.working.clear()

    def get_working_memory(
        self
    ):

        return self.working.get_state()

    def build_working_context(
        self,
        max_chars=4500
    ):

        return self.working.build_context(
            max_chars=max_chars
        )

    def set_current_topic(
        self,
        topic
    ):

        self.working.set_topic(
            topic
        )

    def set_current_goal(
        self,
        goal
    ):

        self.working.set_goal(
            goal
        )

    def set_current_task(
        self,
        task,
        state=None
    ):

        self.working.set_task(
            task,
            state
        )

    def add_working_entity(
        self,
        name,
        value,
        entity_type=None
    ):

        self.working.set_entity(
            name,
            value,
            entity_type
        )

    def add_working_decision(
        self,
        decision
    ):

        self.working.add_decision(
            decision
        )

    def add_working_information(
        self,
        content,
        importance=0.5,
        source="conversation",
        temporary=True
    ):

        self.working.add_information(
            content=content,
            importance=importance,
            source=source,
            temporary=temporary
        )

    def observe_working_turn(
        self,
        role,
        content
    ):

        self.working.observe_turn(
            role,
            content
        )

    # ==================================================
    # CONVERSACIONES
    # ==================================================

    def start_conversation(
        self,
        title=None,
        metadata=None
    ):

        return (
            self.episodic
            .start_conversation(
                title=title,
                metadata=metadata
            )
        )

    def end_conversation(
        self,
        title=None,
        summary=None
    ):

        result = (
            self.episodic
            .end_conversation(
                title=title,
                summary=summary,
                analyze=(
                    self.config
                    .EPISODIC_ANALYZE_ON_END
                )
            )
        )

        conversation_id = None

        if isinstance(
            result,
            dict
        ):

            conversation_id = (
                result.get(
                    "conversation_id"
                )
            )

        if (
            conversation_id
            and
            self.config
            .EPISODIC_CREATE_SUMMARY_MEMORY
        ):

            try:

                self.create_episode_memory(
                    conversation_id
                )

            except Exception:

                pass

        return result

    def current_conversation_id(
        self
    ):

        return (
            self.episodic
            .current_conversation_id
        )

    def add_conversation_message(
        self,
        role,
        content,
        metadata=None
    ):

        self.observe_working_turn(
            role,
            content
        )

        return (
            self.episodic
            .add_message(
                role,
                content,
                metadata
            )
        )

    def recent_messages(
        self,
        limit=20
    ):

        return self.episodic.recent_messages(
            limit
        )

    def search_conversations(
        self,
        query,
        limit=10
    ):

        return self.episodic.search(
            query,
            limit
        )

    def search_episodes(
        self,
        query,
        limit=10
    ):

        return self.episodic.search_episodes(
            query,
            limit
        )

    def get_conversation(
        self,
        conversation_id,
        limit=1000
    ):

        return self.episodic.get_conversation(
            conversation_id,
            limit
        )

    def get_episode(
        self,
        conversation_id
    ):

        return self.episodic.get_episode(
            conversation_id
        )

    def recent_conversations(
        self,
        limit=10
    ):

        return self.episodic.recent_conversations(
            limit
        )

    # ==================================================
    # EVENTO
    # ==================================================

    def record_event(
        self,
        content,
        importance=0.5,
        confidence=1.0,
        metadata=None
    ):

        return self.episodic.record_event(
            content=content,
            importance=importance,
            confidence=confidence,
            metadata=metadata
        )

    # ==================================================
    # HISTORIAL
    # ==================================================

    def history(
        self,
        key,
        limit=50
    ):

        memory = self.recall(
            key
        )

        if not memory:

            return []

        return self.store.get_history(
            memory["id"],
            limit
        )

    # ==================================================
    # STATUS
    # ==================================================

    def get_status(
        self
    ):

        return {
            "database":
                str(
                    self.store.database_path
                ),

            "fts_available":
                self.store.fts_available,

            "embeddings_enabled":
                self.config.ENABLE_EMBEDDINGS,

            "current_conversation":
                self.current_conversation_id(),

            "working_memory":
                self.working.get_state(),

            "profile_statistics":
                self.get_profile_statistics(),

            "pattern_detection":
                self.config.ENABLE_PATTERN_DETECTION,

            "prediction_enabled":
                self.config.ENABLE_PREDICTION,

            "active_predictions":
                len(
                    self.active_predictions(
                        limit=(
                            self.config
                            .PREDICTION_MAX_ACTIVE
                        )
                    )
                ),

            "prediction_statistics":
                self.prediction_statistics(),

            "procedural_learning":
                self.config.ENABLE_PROCEDURAL_LEARNING,

            "procedural_statistics":
                self.procedural_statistics(),

            "episodic_memory":
                self.config.ENABLE_EPISODIC_MEMORY
        }

    # ==================================================
    # EMBEDDINGS
    # ==================================================

    def _update_embedding(
        self,
        memory
    ):

        if not memory:

            return

        if (
            self.embedding_engine is None
            or
            not self.config.ENABLE_EMBEDDINGS
        ):

            return

        memory_id = memory.get(
            "id"
        )

        if not memory_id:

            return

        text = self._embedding_text(
            memory
        )

        content_hash = (
            hashlib.sha256(
                text.encode(
                    "utf-8"
                )
            ).hexdigest()
        )

        existing = (
            self.store.get_embedding(
                memory_id
            )
        )

        if existing and (
            existing.get(
                "content_hash"
            )
            ==
            content_hash
        ):

            return

        vector = (
            self.embedding_engine
            .encode(
                text
            )
        )

        if not vector:

            return

        self.store.save_embedding(
            memory_id=memory_id,
            provider=(
                self.config
                .EMBEDDING_PROVIDER
            ),
            dimensions=len(
                vector
            ),
            vector=vector,
            content_hash=content_hash
        )

    @staticmethod
    def _embedding_text(
        memory
    ):

        return (
            f"tipo: "
            f"{memory.get('memory_type', '')}\n"
            f"categoria: "
            f"{memory.get('category', '')}\n"
            f"concepto: "
            f"{memory.get('memory_key', '')}\n"
            f"informacion: "
            f"{memory.get('content', '')}"
        )

    # ==================================================
    # MIGRACIÓN LEGACY
    # ==================================================

    def _migrate_legacy_memory(
        self
    ):

        legacy_file = (
            self.base_dir
            / "memory"
            / "memory.json"
        )

        if not legacy_file.exists():

            return

        try:

            with open(
                legacy_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(
                    file
                )

        except Exception:

            return

        memories = []

        if isinstance(
            data,
            dict
        ):

            if isinstance(
                data.get(
                    "memories"
                ),
                list
            ):

                memories = data[
                    "memories"
                ]

            else:

                for key, value in data.items():

                    if key == "version":

                        continue

                    memories.append({
                        "key":
                            key,

                        "content":
                            value
                    })

        for item in memories:

            if not isinstance(
                item,
                dict
            ):

                continue

            key = item.get(
                "key"
            )

            content = (
                item.get(
                    "content"
                )
                or
                item.get(
                    "value"
                )
            )

            if key is None or content is None:

                continue

            try:

                if self.recall(
                    key
                ):

                    continue

                self.remember(
                    content=content,
                    key=key,
                    memory_type=(
                        item.get(
                            "memory_type"
                        )
                        or
                        self._legacy_type(
                            item.get(
                                "category"
                            )
                        )
                    ),
                    category=(
                        item.get(
                            "category"
                        )
                        or
                        "general"
                    ),
                    importance=(
                        item.get(
                            "importance"
                        )
                        or
                        0.5
                    ),
                    confidence=1.0,
                    source="legacy",
                    create_associations=False,
                    explicit=False
                )

            except Exception:

                continue

    @staticmethod
    def _legacy_type(
        category
    ):

        category = str(
            category
            or
            ""
        ).lower()

        if category == "preferencia":

            return "preference"

        if category == "personal":

            return "personal"

        return "general"