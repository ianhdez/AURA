import json
import sqlite3
import struct
import uuid

from datetime import datetime
from pathlib import Path


class MemoryStore:

    CURRENT_SCHEMA_VERSION = 7

    def __init__(
        self,
        database_path
    ):

        self.database_path = (
            Path(database_path)
            .resolve()
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.fts_available = False

        self._initialize()

    # ==================================================
    # CONEXIÓN
    # ==================================================

    def _connect(self):

        connection = sqlite3.connect(
            str(
                self.database_path
            ),
            timeout=30
        )

        connection.row_factory = (
            sqlite3.Row
        )

        connection.execute(
            "PRAGMA journal_mode=WAL"
        )

        connection.execute(
            "PRAGMA foreign_keys=ON"
        )

        connection.execute(
            "PRAGMA synchronous=NORMAL"
        )

        connection.execute(
            "PRAGMA busy_timeout=30000"
        )

        return connection

    # ==================================================
    # ID
    # ==================================================

    @staticmethod
    def new_id(
        prefix
    ):

        return (
            str(prefix)
            + "_"
            + uuid.uuid4().hex[:16]
        )

    # ==================================================
    # FECHA
    # ==================================================

    @staticmethod
    def _now():

        return datetime.now().isoformat(
            timespec="seconds"
        )

    # ==================================================
    # INICIALIZACIÓN
    # ==================================================

    def _initialize(self):

        with self._connect() as db:

            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS
                schema_version (

                    version INTEGER NOT NULL
                );


                CREATE TABLE IF NOT EXISTS
                memories (

                    id TEXT PRIMARY KEY,

                    memory_type TEXT NOT NULL,

                    memory_key TEXT,

                    content TEXT NOT NULL,

                    category TEXT DEFAULT 'general',

                    importance REAL DEFAULT 0.5,

                    confidence REAL DEFAULT 1.0,

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL,

                    last_accessed_at TEXT,

                    access_count INTEGER DEFAULT 0,

                    source TEXT DEFAULT 'conversation',

                    status TEXT DEFAULT 'active',

                    supersedes TEXT,

                    superseded_by TEXT,

                    expires_at TEXT,

                    metadata TEXT DEFAULT '{}'
                );


                CREATE INDEX IF NOT EXISTS
                idx_memories_key
                ON memories(memory_key);


                CREATE INDEX IF NOT EXISTS
                idx_memories_type
                ON memories(memory_type);


                CREATE INDEX IF NOT EXISTS
                idx_memories_category
                ON memories(category);


                CREATE INDEX IF NOT EXISTS
                idx_memories_status
                ON memories(status);


                CREATE INDEX IF NOT EXISTS
                idx_memories_updated
                ON memories(updated_at);


                CREATE INDEX IF NOT EXISTS
                idx_memories_importance
                ON memories(importance);


                CREATE INDEX IF NOT EXISTS
                idx_memories_confidence
                ON memories(confidence);


                CREATE TABLE IF NOT EXISTS
                conversations (

                    id TEXT PRIMARY KEY,

                    started_at TEXT NOT NULL,

                    ended_at TEXT,

                    title TEXT,

                    summary TEXT,

                    metadata TEXT DEFAULT '{}'
                );


                CREATE INDEX IF NOT EXISTS
                idx_conversations_started
                ON conversations(started_at);


                CREATE TABLE IF NOT EXISTS
                conversation_messages (

                    id TEXT PRIMARY KEY,

                    conversation_id TEXT NOT NULL,

                    role TEXT NOT NULL,

                    content TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    sequence INTEGER DEFAULT 0,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        conversation_id
                    )
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_messages_conversation
                ON conversation_messages(
                    conversation_id
                );


                CREATE INDEX IF NOT EXISTS
                idx_messages_created
                ON conversation_messages(
                    created_at
                );


                CREATE INDEX IF NOT EXISTS
                idx_messages_sequence
                ON conversation_messages(
                    conversation_id,
                    sequence
                );


                CREATE TABLE IF NOT EXISTS
                memory_relations (

                    id TEXT PRIMARY KEY,

                    source_id TEXT NOT NULL,

                    target_id TEXT NOT NULL,

                    relation TEXT NOT NULL,

                    weight REAL DEFAULT 1.0,

                    created_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        source_id
                    )
                    REFERENCES memories(id)
                    ON DELETE CASCADE,

                    FOREIGN KEY(
                        target_id
                    )
                    REFERENCES memories(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_rel_source
                ON memory_relations(source_id);


                CREATE INDEX IF NOT EXISTS
                idx_rel_target
                ON memory_relations(target_id);


                CREATE TABLE IF NOT EXISTS
                memory_history (

                    id TEXT PRIMARY KEY,

                    memory_id TEXT,

                    operation TEXT NOT NULL,

                    old_content TEXT,

                    new_content TEXT,

                    created_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        memory_id
                    )
                    REFERENCES memories(id)
                    ON DELETE SET NULL
                );


                CREATE INDEX IF NOT EXISTS
                idx_history_memory
                ON memory_history(memory_id);


                CREATE INDEX IF NOT EXISTS
                idx_history_created
                ON memory_history(created_at);


                CREATE TABLE IF NOT EXISTS
                memory_embeddings (

                    memory_id TEXT PRIMARY KEY,

                    provider TEXT NOT NULL,

                    dimensions INTEGER,

                    vector BLOB,

                    content_hash TEXT,

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        memory_id
                    )
                    REFERENCES memories(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_embeddings_provider
                ON memory_embeddings(provider);


                CREATE TABLE IF NOT EXISTS
                memory_tags (

                    memory_id TEXT NOT NULL,

                    tag TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    PRIMARY KEY(
                        memory_id,
                        tag
                    ),

                    FOREIGN KEY(
                        memory_id
                    )
                    REFERENCES memories(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_memory_tags_tag
                ON memory_tags(tag);


                CREATE TABLE IF NOT EXISTS
                procedural_skills (

                    id TEXT PRIMARY KEY,

                    memory_id TEXT,

                    skill_key TEXT NOT NULL UNIQUE,

                    name TEXT NOT NULL,

                    description TEXT NOT NULL,

                    category TEXT DEFAULT 'general',

                    version INTEGER DEFAULT 1,

                    confidence REAL DEFAULT 0.5,

                    reliability REAL DEFAULT 0.0,

                    use_count INTEGER DEFAULT 0,

                    success_count INTEGER DEFAULT 0,

                    failure_count INTEGER DEFAULT 0,

                    partial_count INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,

                    updated_at TEXT NOT NULL,

                    last_used_at TEXT,

                    status TEXT DEFAULT 'active',

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        memory_id
                    )
                    REFERENCES memories(id)
                    ON DELETE SET NULL
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_skill_key

                ON procedural_skills(
                    skill_key
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_skill_status

                ON procedural_skills(
                    status
                );


                CREATE TABLE IF NOT EXISTS
                procedural_steps (

                    id TEXT PRIMARY KEY,

                    skill_id TEXT NOT NULL,

                    step_number INTEGER NOT NULL,

                    instruction TEXT NOT NULL,

                    expected_result TEXT,

                    failure_hint TEXT,

                    optional INTEGER DEFAULT 0,

                    created_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        skill_id
                    )
                    REFERENCES procedural_skills(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_steps_skill

                ON procedural_steps(
                    skill_id,
                    step_number
                );


                CREATE TABLE IF NOT EXISTS
                procedural_preconditions (

                    id TEXT PRIMARY KEY,

                    skill_id TEXT NOT NULL,

                    condition TEXT NOT NULL,

                    created_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        skill_id
                    )
                    REFERENCES procedural_skills(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_preconditions_skill

                ON procedural_preconditions(
                    skill_id
                );


                CREATE TABLE IF NOT EXISTS
                procedural_runs (

                    id TEXT PRIMARY KEY,

                    skill_id TEXT NOT NULL,

                    started_at TEXT NOT NULL,

                    ended_at TEXT,

                    outcome TEXT DEFAULT 'unknown',

                    notes TEXT,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        skill_id
                    )
                    REFERENCES procedural_skills(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_runs_skill

                ON procedural_runs(
                    skill_id
                );


                CREATE TABLE IF NOT EXISTS
                procedural_step_results (

                    id TEXT PRIMARY KEY,

                    run_id TEXT NOT NULL,

                    step_number INTEGER NOT NULL,

                    outcome TEXT DEFAULT 'unknown',

                    notes TEXT,

                    created_at TEXT NOT NULL,

                    metadata TEXT DEFAULT '{}',

                    FOREIGN KEY(
                        run_id
                    )
                    REFERENCES procedural_runs(id)
                    ON DELETE CASCADE
                );


                CREATE INDEX IF NOT EXISTS
                idx_procedural_step_results_run

                ON procedural_step_results(
                    run_id
                );
                """
            )

            self._ensure_optional_columns(
                db
            )

            self._initialize_fts(
                db
            )

            self._set_schema_version(
                db
            )

    # ==================================================
    # COLUMNAS OPCIONALES
    # ==================================================

    def _ensure_optional_columns(
        self,
        db
    ):

        rows = db.execute(
            """
            PRAGMA table_info(memories)
            """
        ).fetchall()

        columns = {
            row["name"]
            for row in rows
        }

        if "supersedes" not in columns:

            db.execute(
                """
                ALTER TABLE memories
                ADD COLUMN supersedes TEXT
                """
            )

        if "superseded_by" not in columns:

            db.execute(
                """
                ALTER TABLE memories
                ADD COLUMN superseded_by TEXT
                """
            )

        if "expires_at" not in columns:

            db.execute(
                """
                ALTER TABLE memories
                ADD COLUMN expires_at TEXT
                """
            )

        message_rows = db.execute(
            """
            PRAGMA table_info(
                conversation_messages
            )
            """
        ).fetchall()

        message_columns = {
            row["name"]
            for row in message_rows
        }

        if "sequence" not in message_columns:

            db.execute(
                """
                ALTER TABLE conversation_messages

                ADD COLUMN sequence
                INTEGER DEFAULT 0
                """
            )

    # ==================================================
    # VERSIÓN
    # ==================================================

    def _set_schema_version(
        self,
        db
    ):

        row = db.execute(
            """
            SELECT version
            FROM schema_version
            LIMIT 1
            """
        ).fetchone()

        if row is None:

            db.execute(
                """
                INSERT INTO schema_version(
                    version
                )
                VALUES (?)
                """,
                (
                    self.CURRENT_SCHEMA_VERSION,
                )
            )

        elif int(
            row["version"]
        ) < self.CURRENT_SCHEMA_VERSION:

            db.execute(
                """
                UPDATE schema_version
                SET version=?
                """,
                (
                    self.CURRENT_SCHEMA_VERSION,
                )
            )

    # ==================================================
    # FTS
    # ==================================================

    def _initialize_fts(
        self,
        db
    ):

        try:

            db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS
                memories_search

                USING fts5(

                    memory_id UNINDEXED,

                    memory_key,

                    content,

                    category,

                    memory_type,

                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )

            db.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS
                conversation_search

                USING fts5(

                    message_id UNINDEXED,

                    conversation_id UNINDEXED,

                    role,

                    content,

                    tokenize='unicode61 remove_diacritics 2'
                )
                """
            )

            self.fts_available = True

            self._rebuild_fts(
                db
            )

        except sqlite3.OperationalError:

            self.fts_available = False

    def _rebuild_fts(
        self,
        db
    ):

        if not self.fts_available:

            return

        db.execute(
            "DELETE FROM memories_search"
        )

        db.execute(
            """
            INSERT INTO memories_search(

                memory_id,
                memory_key,
                content,
                category,
                memory_type

            )

            SELECT

                id,
                COALESCE(
                    memory_key,
                    ''
                ),
                content,
                COALESCE(
                    category,
                    ''
                ),
                memory_type

            FROM memories

            WHERE status='active'
            """
        )

        db.execute(
            "DELETE FROM conversation_search"
        )

        db.execute(
            """
            INSERT INTO conversation_search(

                message_id,
                conversation_id,
                role,
                content

            )

            SELECT

                id,
                conversation_id,
                role,
                content

            FROM conversation_messages
            """
        )

    # ==================================================
    # GUARDAR MEMORIA
    # ==================================================

    def save_memory(
        self,
        memory_id,
        memory_type,
        key,
        content,
        category,
        importance,
        confidence,
        source,
        metadata,
        status="active",
        supersedes=None,
        expires_at=None
    ):

        now = self._now()

        with self._connect() as db:

            db.execute(
                """
                INSERT INTO memories(

                    id,
                    memory_type,
                    memory_key,
                    content,
                    category,
                    importance,
                    confidence,
                    created_at,
                    updated_at,
                    last_accessed_at,
                    access_count,
                    source,
                    status,
                    supersedes,
                    superseded_by,
                    expires_at,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?
                )
                """,
                (
                    memory_id,
                    memory_type,
                    key,
                    content,
                    category,
                    importance,
                    confidence,
                    now,
                    now,
                    None,
                    0,
                    source,
                    status,
                    supersedes,
                    None,
                    expires_at,
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

            self._update_fts(
                db,
                memory_id,
                key,
                content,
                category,
                memory_type,
                status
            )

            self._add_history(
                db,
                memory_id,
                "create",
                None,
                content,
                {}
            )

        return self.get_memory(
            memory_id
        )

    # ==================================================
    # ACTUALIZAR MEMORIA
    # ==================================================

    def update_memory(
        self,
        memory_id,
        content=None,
        key=None,
        memory_type=None,
        category=None,
        importance=None,
        confidence=None,
        status=None,
        metadata=None,
        supersedes=None,
        superseded_by=None,
        expires_at=None
    ):

        current = self.get_memory(
            memory_id
        )

        if current is None:

            return None

        old_content = current.get(
            "content"
        )

        values = {
            "content":
                old_content,

            "memory_key":
                current.get(
                    "memory_key"
                ),

            "memory_type":
                current.get(
                    "memory_type"
                ),

            "category":
                current.get(
                    "category"
                ),

            "importance":
                current.get(
                    "importance",
                    0.5
                ),

            "confidence":
                current.get(
                    "confidence",
                    1.0
                ),

            "status":
                current.get(
                    "status",
                    "active"
                ),

            "metadata":
                current.get(
                    "metadata",
                    {}
                ),

            "supersedes":
                current.get(
                    "supersedes"
                ),

            "superseded_by":
                current.get(
                    "superseded_by"
                ),

            "expires_at":
                current.get(
                    "expires_at"
                )
        }

        if content is not None:

            values["content"] = str(
                content
            )

        if key is not None:

            values["memory_key"] = (
                str(key)
                .strip()
                .lower()
            )

        if memory_type is not None:

            values["memory_type"] = (
                str(memory_type)
                .strip()
                .lower()
            )

        if category is not None:

            values["category"] = (
                str(category)
                .strip()
                .lower()
            )

        if importance is not None:

            try:

                values["importance"] = float(
                    importance
                )

            except Exception:

                pass

        if confidence is not None:

            try:

                values["confidence"] = float(
                    confidence
                )

            except Exception:

                pass

        if status is not None:

            values["status"] = (
                str(status)
                .strip()
                .lower()
            )

        if metadata is not None:

            values["metadata"] = metadata

        if supersedes is not None:

            values["supersedes"] = supersedes

        if superseded_by is not None:

            values["superseded_by"] = superseded_by

        if expires_at is not None:

            values["expires_at"] = expires_at

        values["importance"] = max(
            0.0,
            min(
                1.0,
                float(
                    values["importance"]
                )
            )
        )

        values["confidence"] = max(
            0.0,
            min(
                1.0,
                float(
                    values["confidence"]
                )
            )
        )

        now = self._now()

        metadata_json = json.dumps(
            values["metadata"] or {},
            ensure_ascii=False
        )

        with self._connect() as db:

            db.execute(
                """
                UPDATE memories

                SET

                    memory_type=?,
                    memory_key=?,
                    content=?,
                    category=?,
                    importance=?,
                    confidence=?,
                    updated_at=?,
                    status=?,
                    supersedes=?,
                    superseded_by=?,
                    expires_at=?,
                    metadata=?

                WHERE id=?
                """,
                (
                    values["memory_type"],
                    values["memory_key"],
                    values["content"],
                    values["category"],
                    values["importance"],
                    values["confidence"],
                    now,
                    values["status"],
                    values["supersedes"],
                    values["superseded_by"],
                    values["expires_at"],
                    metadata_json,
                    memory_id
                )
            )

            self._update_fts(
                db,
                memory_id,
                values["memory_key"],
                values["content"],
                values["category"],
                values["memory_type"],
                values["status"]
            )

            if old_content != values[
                "content"
            ]:

                self._add_history(
                    db,
                    memory_id,
                    "update",
                    old_content,
                    values["content"],
                    {}
                )

        return self.get_memory(
            memory_id
        )

    # ==================================================
    # OBTENER MEMORIA
    # ==================================================

    def get_memory(
        self,
        memory_id
    ):

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM memories

                WHERE id=?
                """,
                (
                    memory_id,
                )
            ).fetchone()

        if row is None:

            return None

        return self._row_to_dict(
            row
        )

    # ==================================================
    # OBTENER POR CLAVE
    # ==================================================

    def get_by_key(
        self,
        key
    ):

        if key is None:

            return None

        normalized = (
            str(key)
            .strip()
            .lower()
        )

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM memories

                WHERE

                    LOWER(memory_key)=?

                    AND status='active'

                ORDER BY

                    confidence DESC,

                    importance DESC,

                    updated_at DESC

                LIMIT 1
                """,
                (
                    normalized,
                )
            ).fetchone()

        if row is None:

            return None

        return self._row_to_dict(
            row
        )

    # ==================================================
    # LISTAR MEMORIAS
    # ==================================================

    def list_memories(
        self,
        memory_type=None,
        status="active",
        limit=100
    ):

        limit = max(
            1,
            min(
                int(limit),
                100000
            )
        )

        with self._connect() as db:

            if memory_type:

                rows = db.execute(
                    """
                    SELECT *

                    FROM memories

                    WHERE

                        status=?

                        AND memory_type=?

                    ORDER BY

                        importance DESC,

                        confidence DESC,

                        updated_at DESC

                    LIMIT ?
                    """,
                    (
                        status,
                        memory_type,
                        limit
                    )
                ).fetchall()

            else:

                rows = db.execute(
                    """
                    SELECT *

                    FROM memories

                    WHERE status=?

                    ORDER BY

                        importance DESC,

                        confidence DESC,

                        updated_at DESC

                    LIMIT ?
                    """,
                    (
                        status,
                        limit
                    )
                ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # BUSCAR MEMORIAS
    # ==================================================

    def search_fts(
        self,
        query,
        limit=50
    ):

        query = str(
            query or ""
        ).strip()

        if not query:

            return []

        limit = max(
            1,
            min(
                int(limit),
                1000
            )
        )

        tokens = []

        for token in query.split():

            cleaned = "".join(
                character
                for character in token
                if character.isalnum()
                or character == "_"
            )

            if cleaned:

                tokens.append(
                    cleaned
                )

        if not tokens:

            return []

        if not self.fts_available:

            return self._search_fallback(
                query,
                limit
            )

        fts_query = " OR ".join(
            tokens
        )

        with self._connect() as db:

            try:

                rows = db.execute(
                    """
                    SELECT

                        memories.*,

                        bm25(
                            memories_search
                        ) AS bm25_score

                    FROM memories_search

                    JOIN memories

                    ON memories.id =
                       memories_search.memory_id

                    WHERE

                        memories_search MATCH ?

                        AND memories.status='active'

                    ORDER BY

                        bm25_score

                    LIMIT ?
                    """,
                    (
                        fts_query,
                        limit
                    )
                ).fetchall()

            except sqlite3.OperationalError:

                return self._search_fallback(
                    query,
                    limit
                )

        results = []

        if rows:

            scores = [
                float(
                    row["bm25_score"]
                )
                for row in rows
            ]

            minimum = min(
                scores
            )

            maximum = max(
                scores
            )

            spread = (
                maximum
                - minimum
            )

        else:

            maximum = 0.0

            spread = 0.0

        for row in rows:

            raw_score = float(
                row["bm25_score"]
            )

            if spread > 0:

                relevance = (
                    maximum
                    -
                    raw_score
                ) / spread

            else:

                relevance = 1.0

            item = self._row_to_dict(
                row
            )

            item["relevance"] = max(
                0.0,
                min(
                    1.0,
                    relevance
                )
            )

            results.append(
                item
            )

        return results

    # ==================================================
    # FALLBACK DE BÚSQUEDA
    # ==================================================

    def _search_fallback(
        self,
        query,
        limit
    ):

        words = [
            word.lower()
            for word in query.split()
            if word.strip()
        ]

        if not words:

            return []

        clauses = []

        params = []

        for word in words:

            pattern = (
                "%"
                +
                word
                +
                "%"
            )

            clauses.append(
                """
                (
                    LOWER(
                        COALESCE(
                            memory_key,
                            ''
                        )
                    ) LIKE ?

                    OR LOWER(content)
                    LIKE ?

                    OR LOWER(
                        COALESCE(
                            category,
                            ''
                        )
                    ) LIKE ?

                    OR LOWER(memory_type)
                    LIKE ?
                )
                """
            )

            params.extend([
                pattern,
                pattern,
                pattern,
                pattern
            ])

        params.append(
            limit
        )

        sql = f"""
            SELECT *

            FROM memories

            WHERE

                status='active'

                AND (
                    {" OR ".join(clauses)}
                )

            ORDER BY

                importance DESC,

                confidence DESC,

                updated_at DESC

            LIMIT ?
        """

        with self._connect() as db:

            rows = db.execute(
                sql,
                params
            ).fetchall()

        results = []

        for row in rows:

            item = self._row_to_dict(
                row
            )

            searchable = " ".join([
                str(
                    item.get(
                        "memory_key",
                        ""
                    )
                ),

                str(
                    item.get(
                        "content",
                        ""
                    )
                ),

                str(
                    item.get(
                        "category",
                        ""
                    )
                ),

                str(
                    item.get(
                        "memory_type",
                        ""
                    )
                )
            ]).lower()

            matches = sum(
                1
                for word in words
                if word in searchable
            )

            item["relevance"] = (
                matches
                /
                len(words)
            )

            results.append(
                item
            )

        return results

    # ==================================================
    # EMBEDDINGS
    # ==================================================

    def save_embedding(
        self,
        memory_id,
        provider,
        dimensions,
        vector,
        content_hash=None,
        metadata=None
    ):

        if not vector:

            return False

        packed = struct.pack(
            f"<{len(vector)}f",
            *[
                float(value)
                for value in vector
            ]
        )

        now = self._now()

        with self._connect() as db:

            db.execute(
                """
                INSERT INTO memory_embeddings(

                    memory_id,
                    provider,
                    dimensions,
                    vector,
                    content_hash,
                    created_at,
                    updated_at,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?
                )

                ON CONFLICT(memory_id)

                DO UPDATE SET

                    provider=
                        excluded.provider,

                    dimensions=
                        excluded.dimensions,

                    vector=
                        excluded.vector,

                    content_hash=
                        excluded.content_hash,

                    updated_at=
                        excluded.updated_at,

                    metadata=
                        excluded.metadata
                """,
                (
                    memory_id,
                    provider,
                    int(
                        dimensions
                    ),
                    packed,
                    content_hash,
                    now,
                    now,
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

        return True

    def get_embedding(
        self,
        memory_id
    ):

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM memory_embeddings

                WHERE memory_id=?
                """,
                (
                    memory_id,
                )
            ).fetchone()

        if row is None:

            return None

        vector_blob = row[
            "vector"
        ]

        if not vector_blob:

            return None

        dimensions = int(
            row["dimensions"]
        )

        vector = list(
            struct.unpack(
                f"<{dimensions}f",
                vector_blob
            )
        )

        return {
            "memory_id":
                row["memory_id"],

            "provider":
                row["provider"],

            "dimensions":
                dimensions,

            "vector":
                vector,

            "content_hash":
                row["content_hash"],

            "created_at":
                row["created_at"],

            "updated_at":
                row["updated_at"]
        }

    # ==================================================
    # ACCESO
    # ==================================================

    def register_access(
        self,
        memory_id
    ):

        with self._connect() as db:

            db.execute(
                """
                UPDATE memories

                SET

                    last_accessed_at=?,

                    access_count=
                        access_count + 1

                WHERE id=?
                """,
                (
                    self._now(),
                    memory_id
                )
            )

    # ==================================================
    # ELIMINAR
    # ==================================================

    def delete_memory(
        self,
        memory_id
    ):

        current = self.get_memory(
            memory_id
        )

        if current is None:

            return False

        with self._connect() as db:

            db.execute(
                """
                UPDATE memories

                SET

                    status='deleted',

                    updated_at=?

                WHERE id=?
                """,
                (
                    self._now(),
                    memory_id
                )
            )

            self._remove_fts(
                db,
                memory_id
            )

            db.execute(
                """
                DELETE FROM memory_embeddings

                WHERE memory_id=?
                """,
                (
                    memory_id,
                )
            )

            self._add_history(
                db,
                memory_id,
                "delete",
                current.get(
                    "content"
                ),
                None,
                {}
            )

        return True

    # ==================================================
    # RELACIONES
    # ==================================================

    def add_relation(
        self,
        source_id,
        target_id,
        relation,
        weight=1.0,
        metadata=None
    ):

        relation_id = self.new_id(
            "rel"
        )

        with self._connect() as db:

            existing = db.execute(
                """
                SELECT id

                FROM memory_relations

                WHERE

                    source_id=?

                    AND target_id=?

                    AND relation=?

                LIMIT 1
                """,
                (
                    source_id,
                    target_id,
                    relation
                )
            ).fetchone()

            if existing:

                return existing[
                    "id"
                ]

            db.execute(
                """
                INSERT INTO memory_relations(

                    id,
                    source_id,
                    target_id,
                    relation,
                    weight,
                    created_at,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    relation_id,
                    source_id,
                    target_id,
                    relation,
                    float(weight),
                    self._now(),
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

        return relation_id

    def get_relations(
        self,
        memory_id
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM memory_relations

                WHERE

                    source_id=?

                    OR target_id=?

                ORDER BY
                    weight DESC
                """,
                (
                    memory_id,
                    memory_id
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # PROCEDURAL SKILLS
    # ==================================================

    def create_skill(
        self,
        skill_key,
        name,
        description,
        category="general",
        memory_id=None,
        confidence=0.6,
        metadata=None
    ):

        skill_id = self.new_id(
            "skill"
        )

        now = self._now()

        with self._connect() as db:

            existing = db.execute(
                """
                SELECT *

                FROM procedural_skills

                WHERE skill_key=?
                """,
                (
                    skill_key,
                )
            ).fetchone()

            if existing:

                return self._row_to_dict(
                    existing
                )

            db.execute(
                """
                INSERT INTO procedural_skills(

                    id,
                    memory_id,
                    skill_key,
                    name,
                    description,
                    category,
                    version,
                    confidence,
                    reliability,
                    use_count,
                    success_count,
                    failure_count,
                    partial_count,
                    created_at,
                    updated_at,
                    last_used_at,
                    status,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?
                )
                """,
                (
                    skill_id,
                    memory_id,
                    skill_key,
                    name,
                    description,
                    category,
                    1,
                    float(confidence),
                    0.0,
                    0,
                    0,
                    0,
                    0,
                    now,
                    now,
                    None,
                    "active",
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

        return self.get_skill(
            skill_id
        )

    def get_skill(
        self,
        skill_id
    ):

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM procedural_skills

                WHERE id=?
                """,
                (
                    skill_id,
                )
            ).fetchone()

        if row is None:

            return None

        return self._row_to_dict(
            row
        )

    def get_skill_by_key(
        self,
        skill_key
    ):

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM procedural_skills

                WHERE

                    skill_key=?

                    AND status='active'

                LIMIT 1
                """,
                (
                    skill_key,
                )
            ).fetchone()

        if row is None:

            return None

        return self._row_to_dict(
            row
        )

    def update_skill(
        self,
        skill_id,
        name=None,
        description=None,
        category=None,
        confidence=None,
        reliability=None,
        version=None,
        status=None,
        metadata=None
    ):

        current = self.get_skill(
            skill_id
        )

        if current is None:

            return None

        values = {
            "name":
                current["name"],

            "description":
                current["description"],

            "category":
                current["category"],

            "confidence":
                current["confidence"],

            "reliability":
                current["reliability"],

            "version":
                current["version"],

            "status":
                current["status"],

            "metadata":
                current.get(
                    "metadata",
                    {}
                )
        }

        if name is not None:

            values["name"] = str(
                name
            ).strip()

        if description is not None:

            values["description"] = str(
                description
            ).strip()

        if category is not None:

            values["category"] = str(
                category
            ).strip().lower()

        if confidence is not None:

            values["confidence"] = max(
                0.0,
                min(
                    1.0,
                    float(
                        confidence
                    )
                )
            )

        if reliability is not None:

            values["reliability"] = max(
                0.0,
                min(
                    1.0,
                    float(
                        reliability
                    )
                )
            )

        if version is not None:

            values["version"] = max(
                1,
                int(version)
            )

        if status is not None:

            values["status"] = str(
                status
            ).strip().lower()

        if metadata is not None:

            values["metadata"] = metadata

        with self._connect() as db:

            db.execute(
                """
                UPDATE procedural_skills

                SET

                    name=?,

                    description=?,

                    category=?,

                    confidence=?,

                    reliability=?,

                    version=?,

                    updated_at=?,

                    status=?,

                    metadata=?

                WHERE id=?
                """,
                (
                    values["name"],
                    values["description"],
                    values["category"],
                    values["confidence"],
                    values["reliability"],
                    values["version"],
                    self._now(),
                    values["status"],
                    json.dumps(
                        values["metadata"]
                        or {},
                        ensure_ascii=False
                    ),
                    skill_id
                )
            )

        return self.get_skill(
            skill_id
        )

    def list_skills(
        self,
        limit=100,
        category=None
    ):

        limit = max(
            1,
            min(
                int(limit),
                10000
            )
        )

        with self._connect() as db:

            if category:

                rows = db.execute(
                    """
                    SELECT *

                    FROM procedural_skills

                    WHERE

                        status='active'

                        AND category=?

                    ORDER BY

                        confidence DESC,

                        reliability DESC,

                        updated_at DESC

                    LIMIT ?
                    """,
                    (
                        category,
                        limit
                    )
                ).fetchall()

            else:

                rows = db.execute(
                    """
                    SELECT *

                    FROM procedural_skills

                    WHERE status='active'

                    ORDER BY

                        confidence DESC,

                        reliability DESC,

                        updated_at DESC

                    LIMIT ?
                    """,
                    (
                        limit,
                    )
                ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # PASOS
    # ==================================================

    def replace_skill_steps(
        self,
        skill_id,
        steps
    ):

        with self._connect() as db:

            db.execute(
                """
                DELETE FROM procedural_steps

                WHERE skill_id=?
                """,
                (
                    skill_id,
                )
            )

            for index, step in enumerate(
                steps,
                start=1
            ):

                if not isinstance(
                    step,
                    dict
                ):

                    continue

                instruction = str(
                    step.get(
                        "instruction",
                        ""
                    )
                ).strip()

                if not instruction:

                    continue

                step_id = self.new_id(
                    "step"
                )

                db.execute(
                    """
                    INSERT INTO procedural_steps(

                        id,
                        skill_id,
                        step_number,
                        instruction,
                        expected_result,
                        failure_hint,
                        optional,
                        created_at,
                        metadata

                    )

                    VALUES(
                        ?, ?, ?, ?, ?,
                        ?, ?, ?, ?
                    )
                    """,
                    (
                        step_id,
                        skill_id,
                        index,
                        instruction,
                        step.get(
                            "expected_result"
                        ),
                        step.get(
                            "failure_hint"
                        ),
                        int(
                            bool(
                                step.get(
                                    "optional",
                                    False
                                )
                            )
                        ),
                        self._now(),
                        json.dumps(
                            step.get(
                                "metadata",
                                {}
                            )
                            or {},
                            ensure_ascii=False
                        )
                    )
                )

        return self.get_skill_steps(
            skill_id
        )

    def get_skill_steps(
        self,
        skill_id
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM procedural_steps

                WHERE skill_id=?

                ORDER BY step_number ASC
                """,
                (
                    skill_id,
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # PRECONDICIONES
    # ==================================================

    def replace_skill_preconditions(
        self,
        skill_id,
        conditions
    ):

        with self._connect() as db:

            db.execute(
                """
                DELETE FROM procedural_preconditions

                WHERE skill_id=?
                """,
                (
                    skill_id,
                )
            )

            for condition in conditions:

                condition = str(
                    condition
                ).strip()

                if not condition:

                    continue

                condition_id = self.new_id(
                    "pre"
                )

                db.execute(
                    """
                    INSERT INTO procedural_preconditions(

                        id,
                        skill_id,
                        condition,
                        created_at,
                        metadata

                    )

                    VALUES(
                        ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        condition_id,
                        skill_id,
                        condition,
                        self._now(),
                        "{}"
                    )
                )

        return self.get_skill_preconditions(
            skill_id
        )

    def get_skill_preconditions(
        self,
        skill_id
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM procedural_preconditions

                WHERE skill_id=?

                ORDER BY created_at ASC
                """,
                (
                    skill_id,
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # EJECUCIONES
    # ==================================================

    def start_skill_run(
        self,
        skill_id,
        metadata=None
    ):

        run_id = self.new_id(
            "run"
        )

        with self._connect() as db:

            db.execute(
                """
                INSERT INTO procedural_runs(

                    id,
                    skill_id,
                    started_at,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?
                )
                """,
                (
                    run_id,
                    skill_id,
                    self._now(),
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

            db.execute(
                """
                UPDATE procedural_skills

                SET

                    use_count=
                        use_count + 1,

                    last_used_at=?

                WHERE id=?
                """,
                (
                    self._now(),
                    skill_id
                )
            )

        return run_id

    def finish_skill_run(
        self,
        run_id,
        outcome,
        notes=None,
        metadata=None
    ):

        outcome = str(
            outcome
        ).strip().lower()

        if outcome not in {
            "success",
            "failure",
            "partial",
            "unknown"
        }:

            outcome = "unknown"

        with self._connect() as db:

            row = db.execute(
                """
                SELECT skill_id

                FROM procedural_runs

                WHERE id=?
                """,
                (
                    run_id,
                )
            ).fetchone()

            if row is None:

                return False

            skill_id = row[
                "skill_id"
            ]

            db.execute(
                """
                UPDATE procedural_runs

                SET

                    ended_at=?,

                    outcome=?,

                    notes=?,

                    metadata=?

                WHERE id=?
                """,
                (
                    self._now(),
                    outcome,
                    notes,
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    ),
                    run_id
                )
            )

            if outcome == "success":

                db.execute(
                    """
                    UPDATE procedural_skills

                    SET success_count=
                        success_count + 1

                    WHERE id=?
                    """,
                    (
                        skill_id,
                    )
                )

            elif outcome == "failure":

                db.execute(
                    """
                    UPDATE procedural_skills

                    SET failure_count=
                        failure_count + 1

                    WHERE id=?
                    """,
                    (
                        skill_id,
                    )
                )

            elif outcome == "partial":

                db.execute(
                    """
                    UPDATE procedural_skills

                    SET partial_count=
                        partial_count + 1

                    WHERE id=?
                    """,
                    (
                        skill_id,
                    )
                )

            stats = db.execute(
                """
                SELECT

                    success_count,
                    failure_count,
                    partial_count

                FROM procedural_skills

                WHERE id=?
                """,
                (
                    skill_id,
                )
            ).fetchone()

            success = int(
                stats[
                    "success_count"
                ]
            )

            failure = int(
                stats[
                    "failure_count"
                ]
            )

            partial = int(
                stats[
                    "partial_count"
                ]
            )

            total = (
                success
                +
                failure
                +
                partial
            )

            if total > 0:

                reliability = (
                    success
                    +
                    (
                        partial
                        * 0.5
                    )
                ) / total

                db.execute(
                    """
                    UPDATE procedural_skills

                    SET reliability=?

                    WHERE id=?
                    """,
                    (
                        reliability,
                        skill_id
                    )
                )

        return True

    def add_skill_step_result(
        self,
        run_id,
        step_number,
        outcome,
        notes=None,
        metadata=None
    ):

        result_id = self.new_id(
            "stepresult"
        )

        with self._connect() as db:

            db.execute(
                """
                INSERT INTO procedural_step_results(

                    id,
                    run_id,
                    step_number,
                    outcome,
                    notes,
                    created_at,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    result_id,
                    run_id,
                    int(step_number),
                    outcome,
                    notes,
                    self._now(),
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

        return result_id

    def get_skill_runs(
        self,
        skill_id,
        limit=50
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM procedural_runs

                WHERE skill_id=?

                ORDER BY started_at DESC

                LIMIT ?
                """,
                (
                    skill_id,
                    int(limit)
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # CONVERSACIONES
    # ==================================================

    def create_conversation(
        self,
        conversation_id=None,
        title=None,
        metadata=None
    ):

        if conversation_id is None:

            conversation_id = self.new_id(
                "conv"
            )

        with self._connect() as db:

            db.execute(
                """
                INSERT INTO conversations(

                    id,
                    started_at,
                    title,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?
                )
                """,
                (
                    conversation_id,
                    self._now(),
                    title,
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

        return conversation_id

    def end_conversation(
        self,
        conversation_id,
        title=None,
        summary=None
    ):

        with self._connect() as db:

            db.execute(
                """
                UPDATE conversations

                SET

                    ended_at=?,

                    title=
                        COALESCE(
                            ?,
                            title
                        ),

                    summary=
                        COALESCE(
                            ?,
                            summary
                        )

                WHERE id=?
                """,
                (
                    self._now(),
                    title,
                    summary,
                    conversation_id
                )
            )

    # ==================================================
    # ACTUALIZAR CONVERSACIÓN
    # ==================================================

    def update_conversation(
        self,
        conversation_id,
        title=None,
        summary=None,
        metadata=None
    ):

        with self._connect() as db:

            current = db.execute(
                """
                SELECT metadata

                FROM conversations

                WHERE id=?
                """,
                (
                    conversation_id,
                )
            ).fetchone()

            if current is None:

                return False

            try:

                current_metadata = json.loads(
                    current["metadata"]
                    or "{}"
                )

            except Exception:

                current_metadata = {}

            if not isinstance(
                current_metadata,
                dict
            ):

                current_metadata = {}

            if metadata is not None:

                if isinstance(
                    metadata,
                    dict
                ):

                    current_metadata.update(
                        metadata
                    )

            db.execute(
                """
                UPDATE conversations

                SET

                    title=
                        COALESCE(
                            ?,
                            title
                        ),

                    summary=
                        COALESCE(
                            ?,
                            summary
                        ),

                    metadata=?

                WHERE id=?
                """,
                (
                    title,
                    summary,
                    json.dumps(
                        current_metadata,
                        ensure_ascii=False
                    ),
                    conversation_id
                )
            )

        return True

    # ==================================================
    # MENSAJE
    # ==================================================

    def add_message(
        self,
        conversation_id,
        role,
        content,
        metadata=None
    ):

        message_id = self.new_id(
            "msg"
        )

        with self._connect() as db:

            row = db.execute(
                """
                SELECT

                    COALESCE(
                        MAX(sequence),
                        -1
                    ) + 1 AS next_sequence

                FROM conversation_messages

                WHERE conversation_id=?
                """,
                (
                    conversation_id,
                )
            ).fetchone()

            sequence = int(
                row[
                    "next_sequence"
                ]
            )

            db.execute(
                """
                INSERT INTO conversation_messages(

                    id,
                    conversation_id,
                    role,
                    content,
                    created_at,
                    sequence,
                    metadata

                )

                VALUES(
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    message_id,
                    conversation_id,
                    role,
                    content,
                    self._now(),
                    sequence,
                    json.dumps(
                        metadata or {},
                        ensure_ascii=False
                    )
                )
            )

            if self.fts_available:

                db.execute(
                    """
                    INSERT INTO conversation_search(

                        message_id,
                        conversation_id,
                        role,
                        content

                    )

                    VALUES(
                        ?, ?, ?, ?
                    )
                    """,
                    (
                        message_id,
                        conversation_id,
                        role,
                        content
                    )
                )

        return message_id

    # ==================================================
    # MENSAJES DE CONVERSACIÓN
    # ==================================================

    def get_conversation_messages(
        self,
        conversation_id,
        limit=1000
    ):

        limit = max(
            1,
            min(
                int(limit),
                10000
            )
        )

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM conversation_messages

                WHERE conversation_id=?

                ORDER BY sequence ASC

                LIMIT ?
                """,
                (
                    conversation_id,
                    limit
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # CONVERSACIÓN COMPLETA
    # ==================================================

    def get_conversation(
        self,
        conversation_id,
        limit=1000
    ):

        with self._connect() as db:

            row = db.execute(
                """
                SELECT *

                FROM conversations

                WHERE id=?
                """,
                (
                    conversation_id,
                )
            ).fetchone()

        if row is None:

            return None

        result = self._row_to_dict(
            row
        )

        result[
            "messages"
        ] = self.get_conversation_messages(
            conversation_id,
            limit
        )

        return result

    # ==================================================
    # CONVERSACIONES
    # ==================================================

    def list_conversations(
        self,
        limit=20
    ):

        limit = max(
            1,
            min(
                int(limit),
                1000
            )
        )

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM conversations

                ORDER BY started_at DESC

                LIMIT ?
                """,
                (
                    limit,
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # BUSCAR CONVERSACIONES
    # ==================================================

    def search_conversations(
        self,
        query,
        limit=20
    ):

        query = str(
            query or ""
        ).strip()

        if not query:

            return []

        limit = max(
            1,
            min(
                int(limit),
                100
            )
        )

        if self.fts_available:

            tokens = []

            for token in query.split():

                cleaned = "".join(
                    character
                    for character in token
                    if character.isalnum()
                )

                if cleaned:

                    tokens.append(
                        cleaned
                    )

            if tokens:

                fts_query = (
                    " OR ".join(
                        tokens
                    )
                )

                with self._connect() as db:

                    try:

                        rows = db.execute(
                            """
                            SELECT

                                message_id,

                                conversation_id,

                                role,

                                content,

                                bm25(
                                    conversation_search
                                ) AS score

                            FROM conversation_search

                            WHERE

                                conversation_search
                                MATCH ?

                            ORDER BY score

                            LIMIT ?
                            """,
                            (
                                fts_query,
                                limit
                            )
                        ).fetchall()

                    except sqlite3.OperationalError:

                        rows = []

                if rows:

                    return [
                        self._row_to_dict(
                            row
                        )
                        for row in rows
                    ]

        pattern = (
            "%"
            +
            query
            +
            "%"
        )

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM conversation_messages

                WHERE content LIKE ?

                ORDER BY created_at DESC

                LIMIT ?
                """,
                (
                    pattern,
                    limit
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # HISTORIAL
    # ==================================================

    def get_history(
        self,
        memory_id,
        limit=50
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT *

                FROM memory_history

                WHERE memory_id=?

                ORDER BY created_at DESC

                LIMIT ?
                """,
                (
                    memory_id,
                    int(limit)
                )
            ).fetchall()

        return [
            self._row_to_dict(
                row
            )
            for row in rows
        ]

    # ==================================================
    # TAGS
    # ==================================================

    def add_tag(
        self,
        memory_id,
        tag
    ):

        tag = (
            str(tag)
            .strip()
            .lower()
        )

        if not tag:

            return

        with self._connect() as db:

            db.execute(
                """
                INSERT OR IGNORE INTO memory_tags(

                    memory_id,
                    tag,
                    created_at

                )

                VALUES(
                    ?, ?, ?
                )
                """,
                (
                    memory_id,
                    tag,
                    self._now()
                )
            )

    def get_tags(
        self,
        memory_id
    ):

        with self._connect() as db:

            rows = db.execute(
                """
                SELECT tag

                FROM memory_tags

                WHERE memory_id=?

                ORDER BY tag
                """,
                (
                    memory_id,
                )
            ).fetchall()

        return [
            row["tag"]
            for row in rows
        ]

    # ==================================================
    # FTS UPDATE
    # ==================================================

    def _update_fts(
        self,
        db,
        memory_id,
        key,
        content,
        category,
        memory_type,
        status="active"
    ):

        if not self.fts_available:

            return

        db.execute(
            """
            DELETE FROM memories_search

            WHERE memory_id=?
            """,
            (
                memory_id,
            )
        )

        if status != "active":

            return

        db.execute(
            """
            INSERT INTO memories_search(

                memory_id,
                memory_key,
                content,
                category,
                memory_type

            )

            VALUES(
                ?, ?, ?, ?, ?
            )
            """,
            (
                memory_id,
                key or "",
                content or "",
                category or "",
                memory_type or ""
            )
        )

    def _remove_fts(
        self,
        db,
        memory_id
    ):

        if not self.fts_available:

            return

        db.execute(
            """
            DELETE FROM memories_search

            WHERE memory_id=?
            """,
            (
                memory_id,
            )
        )

    # ==================================================
    # HISTORIAL INTERNO
    # ==================================================

    def _add_history(
        self,
        db,
        memory_id,
        operation,
        old_content,
        new_content,
        metadata
    ):

        history_id = self.new_id(
            "hist"
        )

        db.execute(
            """
            INSERT INTO memory_history(

                id,
                memory_id,
                operation,
                old_content,
                new_content,
                created_at,
                metadata

            )

            VALUES(
                ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                history_id,
                memory_id,
                operation,
                old_content,
                new_content,
                self._now(),
                json.dumps(
                    metadata or {},
                    ensure_ascii=False
                )
            )
        )

    # ==================================================
    # ROW → DICT
    # ==================================================

    @staticmethod
    def _row_to_dict(
        row
    ):

        result = dict(
            row
        )

        if "metadata" in result:

            try:

                result[
                    "metadata"
                ] = json.loads(
                    result[
                        "metadata"
                    ]
                    or "{}"
                )

            except Exception:

                result[
                    "metadata"
                ] = {}

        return result