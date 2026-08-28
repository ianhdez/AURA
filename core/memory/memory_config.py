from pathlib import Path


class MemoryConfig:

    VERSION = 8

    DATABASE_NAME = "aura.db"

    # ==================================================
    # BÚSQUEDA
    # ==================================================

    MAX_SEARCH_RESULTS = 12

    DEFAULT_SEARCH_LIMIT = 10

    MAX_SEARCH_LIMIT = 50

    MINIMUM_SEARCH_SCORE = 0.05

    # ==================================================
    # MEMORIA
    # ==================================================

    DEFAULT_IMPORTANCE = 0.5

    DEFAULT_CONFIDENCE = 1.0

    MEMORY_TYPES = {
        "working",
        "episodic",
        "semantic",
        "personal",
        "preference",
        "habit",
        "skill",
        "knowledge",
        "project",
        "pattern",
        "prediction",
        "relationship",
        "contextual",
        "conversation",
        "procedural",
        "general"
    }

    # ==================================================
    # ESTADOS
    # ==================================================

    MEMORY_STATUSES = {
        "active",
        "superseded",
        "deleted",
        "archived",
        "expired",
        "uncertain"
    }

    # ==================================================
    # FUENTES
    # ==================================================

    MEMORY_SOURCES = {
        "conversation",
        "user_explicit",
        "user_confirmed",
        "inferred",
        "observed",
        "learned",
        "imported",
        "system",
        "legacy"
    }

    # ==================================================
    # RECUPERACIÓN
    # ==================================================

    RELEVANCE_WEIGHT = 0.50

    IMPORTANCE_WEIGHT = 0.15

    RECENCY_WEIGHT = 0.12

    CONFIDENCE_WEIGHT = 0.13

    FREQUENCY_WEIGHT = 0.10

    # ==================================================
    # CONTEXTO
    # ==================================================

    RECENT_CONVERSATION_LIMIT = 20

    RECENT_MEMORY_LIMIT = 20

    MAX_MEMORY_CONTEXT_ITEMS = 12

    MAX_EPISODIC_CONTEXT_ITEMS = 8

    MAX_RELATED_MEMORY_ITEMS = 8

    MAX_CONVERSATION_CONTEXT_ITEMS = 12

    # ==================================================
    # EPISÓDICA
    # ==================================================

    ENABLE_EPISODIC_MEMORY = True

    EPISODIC_MAX_MESSAGES_PER_EPISODE = 1000

    EPISODIC_MAX_EPISODES_IN_CONTEXT = 6

    EPISODIC_MIN_MESSAGES_FOR_ANALYSIS = 3

    EPISODIC_CREATE_SUMMARY_MEMORY = True

    EPISODIC_ANALYZE_ON_END = True

    # ==================================================
    # APRENDIZAJE
    # ==================================================

    ENABLE_LEARNING = True

    ENABLE_MEMORY_EXTRACTION = True

    ENABLE_MEMORY_UPDATES = True

    ENABLE_MEMORY_RELATIONS = True

    ENABLE_PATTERN_DETECTION = True

    ENABLE_PREDICTION = True

    ENABLE_PROCEDURAL_LEARNING = True

    # ==================================================
    # CONSOLIDACIÓN
    # ==================================================

    ENABLE_CONSOLIDATION = True

    CONSOLIDATION_MIN_OBSERVATIONS = 2

    CONSOLIDATION_STRONG_OBSERVATIONS = 3

    CONSOLIDATION_SIMILARITY_THRESHOLD = 0.84

    CONSOLIDATION_CONFIDENCE_THRESHOLD = 0.75

    CONSOLIDATION_IMPORTANCE_THRESHOLD = 0.60

    CONSOLIDATION_BATCH_SIZE = 20

    CONSOLIDATION_INTERVAL = 12

    LEARNING_INTERVAL = 6

    PREDICTION_EVALUATION_INTERVAL = 6

    # ==================================================
    # PATRONES
    # ==================================================

    PATTERN_MIN_OBSERVATIONS = 3

    PATTERN_CONFIDENCE_THRESHOLD = 0.65

    PATTERN_IMPORTANCE_THRESHOLD = 0.55

    PATTERN_SIMILARITY_THRESHOLD = 0.84

    PATTERN_MAX_OBSERVATIONS = 12

    PATTERN_MAX_RESULTS = 20

    # ==================================================
    # PREDICCIONES
    # ==================================================

    PREDICTION_MIN_CONFIDENCE = 0.60

    PREDICTION_MIN_IMPORTANCE = 0.40

    PREDICTION_DEFAULT_HORIZON_HOURS = 24

    PREDICTION_MAX_HORIZON_HOURS = 720

    PREDICTION_MAX_ACTIVE = 20

    PREDICTION_MAX_CONTEXT = 12

    PREDICTION_GENERATION_INTERVAL = 10

    PREDICTION_EVALUATION_INTERVAL = 3

    PREDICTION_CORRECT_GAIN = 0.10

    PREDICTION_INCORRECT_LOSS = 0.15

    PREDICTION_PARTIAL_GAIN = 0.02

    PREDICTION_MAX_CONFIDENCE = 0.99

    PREDICTION_MIN_CONFIDENCE_AFTER_FAILURE = 0.10

    # ==================================================
    # PROCEDIMIENTOS
    # ==================================================

    PROCEDURAL_MIN_CONFIDENCE = 0.60

    PROCEDURAL_MIN_IMPORTANCE = 0.50

    PROCEDURAL_MAX_STEPS = 50

    PROCEDURAL_MAX_PRECONDITIONS = 20

    PROCEDURAL_MAX_EXAMPLES = 20

    PROCEDURAL_MAX_ACTIVE = 100

    PROCEDURAL_MAX_CONTEXT = 8

    PROCEDURAL_SUCCESS_GAIN = 0.08

    PROCEDURAL_FAILURE_LOSS = 0.12

    PROCEDURAL_PARTIAL_GAIN = 0.01

    PROCEDURAL_MIN_REUSE_CONFIDENCE = 0.55

    PROCEDURAL_SIMILARITY_THRESHOLD = 0.86

    # ==================================================
    # DECAY
    # ==================================================

    ENABLE_MEMORY_DECAY = True

    DECAY_RATE = 0.01

    MINIMUM_DECAY_FACTOR = 0.10

    # ==================================================
    # RELACIONES
    # ==================================================

    DEFAULT_RELATION_STRENGTH = 0.5

    MINIMUM_RELATION_STRENGTH = 0.0

    MAXIMUM_RELATION_STRENGTH = 1.0

    # ==================================================
    # EMBEDDINGS
    # ==================================================

    ENABLE_EMBEDDINGS = True

    EMBEDDING_PROVIDER = "llama_cpp"

    EMBEDDING_MODEL_NAME = "bge-m3"

    EMBEDDING_MODEL_DIRECTORY = "bge-m3"

    EMBEDDING_MODEL_FILE = "bge-m3.gguf"

    EMBEDDING_DIMENSIONS = 1024

    EMBEDDING_CONTEXT_SIZE = 8192

    EMBEDDING_HOST = "127.0.0.1"

    EMBEDDING_PORT = 8081

    EMBEDDING_BATCH_SIZE = 16

    # ==================================================
    # DIRECTORIOS
    # ==================================================

    @classmethod
    def memory_directory(
        cls,
        base_dir
    ):

        directory = (
            Path(base_dir).resolve()
            / "memory"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return directory

    @classmethod
    def database_path(
        cls,
        base_dir
    ):

        return (
            cls.memory_directory(
                base_dir
            )
            /
            cls.DATABASE_NAME
        )

    @classmethod
    def embeddings_directory(
        cls,
        base_dir
    ):

        directory = (
            cls.memory_directory(
                base_dir
            )
            /
            "embeddings"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return directory

    @classmethod
    def embedding_model_path(
        cls,
        base_dir
    ):

        return (
            Path(base_dir).resolve()
            /
            "models"
            /
            cls.EMBEDDING_MODEL_DIRECTORY
            /
            cls.EMBEDDING_MODEL_FILE
        )

    @classmethod
    def embedding_executable_path(
        cls,
        base_dir
    ):

        return (
            Path(base_dir).resolve()
            /
            "backends"
            /
            "llama_cpp"
            /
            "bin"
            /
            "llama-server.exe"
        )

    @classmethod
    def conversations_directory(
        cls,
        base_dir
    ):

        directory = (
            cls.memory_directory(
                base_dir
            )
            /
            "conversations"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return directory

    @classmethod
    def snapshots_directory(
        cls,
        base_dir
    ):

        directory = (
            cls.memory_directory(
                base_dir
            )
            /
            "snapshots"
        )

        directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return directory

    # ==================================================
    # VALIDACIÓN
    # ==================================================

    @classmethod
    def is_valid_memory_type(
        cls,
        memory_type
    ):

        if memory_type is None:

            return False

        return (
            str(memory_type)
            .strip()
            .lower()
            in cls.MEMORY_TYPES
        )

    @classmethod
    def is_valid_status(
        cls,
        status
    ):

        if status is None:

            return False

        return (
            str(status)
            .strip()
            .lower()
            in cls.MEMORY_STATUSES
        )

    @classmethod
    def is_valid_source(
        cls,
        source
    ):

        if source is None:

            return False

        return (
            str(source)
            .strip()
            .lower()
            in cls.MEMORY_SOURCES
        )

    # ==================================================
    # CLAMP
    # ==================================================

    @classmethod
    def clamp_importance(
        cls,
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

            value = cls.DEFAULT_IMPORTANCE

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    @classmethod
    def clamp_confidence(
        cls,
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

            value = cls.DEFAULT_CONFIDENCE

        return max(
            0.0,
            min(
                1.0,
                value
            )
        )

    @classmethod
    def clamp_relation_strength(
        cls,
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

            value = cls.DEFAULT_RELATION_STRENGTH

        return max(
            cls.MINIMUM_RELATION_STRENGTH,
            min(
                cls.MAXIMUM_RELATION_STRENGTH,
                value
            )
        )

    # ==================================================
    # PESOS
    # ==================================================

    @classmethod
    def get_search_weights(
        cls
    ):

        return {
            "relevance":
                cls.RELEVANCE_WEIGHT,

            "importance":
                cls.IMPORTANCE_WEIGHT,

            "recency":
                cls.RECENCY_WEIGHT,

            "confidence":
                cls.CONFIDENCE_WEIGHT,

            "frequency":
                cls.FREQUENCY_WEIGHT
        }