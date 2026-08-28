from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Memory:

    id: str

    memory_type: str

    key: Optional[str]

    content: Any

    category: str = "general"

    importance: float = 0.5

    confidence: float = 1.0

    created_at: str = ""

    updated_at: str = ""

    last_accessed_at: str = ""

    access_count: int = 0

    source: str = "conversation"

    status: str = "active"

    supersedes: Optional[str] = None

    superseded_by: Optional[str] = None

    expires_at: Optional[str] = None

    metadata: dict = field(
        default_factory=dict
    )

    keywords: list = field(
        default_factory=list
    )

    def to_dict(
        self
    ):

        return {
            "id":
                self.id,

            "memory_type":
                self.memory_type,

            "key":
                self.key,

            "content":
                self.content,

            "category":
                self.category,

            "importance":
                self.importance,

            "confidence":
                self.confidence,

            "created_at":
                self.created_at,

            "updated_at":
                self.updated_at,

            "last_accessed_at":
                self.last_accessed_at,

            "access_count":
                self.access_count,

            "source":
                self.source,

            "status":
                self.status,

            "supersedes":
                self.supersedes,

            "superseded_by":
                self.superseded_by,

            "expires_at":
                self.expires_at,

            "metadata":
                self.metadata,

            "keywords":
                self.keywords
        }


@dataclass
class MemoryResult:

    memory: Memory

    score: float

    relevance: float = 0.0

    importance: float = 0.0

    recency: float = 0.0

    confidence: float = 0.0

    frequency: float = 0.0

    semantic_score: float = 0.0

    keyword_score: float = 0.0

    relationship_score: float = 0.0

    reason: str = ""

    def to_dict(
        self
    ):

        data = self.memory.to_dict()

        data["score"] = (
            self.score
        )

        data["relevance"] = (
            self.relevance
        )

        data["importance_score"] = (
            self.importance
        )

        data["recency_score"] = (
            self.recency
        )

        data["confidence_score"] = (
            self.confidence
        )

        data["frequency_score"] = (
            self.frequency
        )

        data["semantic_score"] = (
            self.semantic_score
        )

        data["keyword_score"] = (
            self.keyword_score
        )

        data["relationship_score"] = (
            self.relationship_score
        )

        data["reason"] = (
            self.reason
        )

        return data


@dataclass
class ConversationMessage:

    id: str

    conversation_id: str

    role: str

    content: str

    created_at: str

    sequence: int = 0

    metadata: dict = field(
        default_factory=dict
    )

    def to_dict(
        self
    ):

        return {
            "id":
                self.id,

            "conversation_id":
                self.conversation_id,

            "role":
                self.role,

            "content":
                self.content,

            "created_at":
                self.created_at,

            "sequence":
                self.sequence,

            "metadata":
                self.metadata
        }


@dataclass
class Conversation:

    id: str

    started_at: str

    ended_at: Optional[str] = None

    title: Optional[str] = None

    summary: Optional[str] = None

    metadata: dict = field(
        default_factory=dict
    )

    def to_dict(
        self
    ):

        return {
            "id":
                self.id,

            "started_at":
                self.started_at,

            "ended_at":
                self.ended_at,

            "title":
                self.title,

            "summary":
                self.summary,

            "metadata":
                self.metadata
        }


@dataclass
class MemoryRelation:

    id: str

    source_id: str

    target_id: str

    relation: str

    weight: float = 1.0

    created_at: str = ""

    metadata: dict = field(
        default_factory=dict
    )

    def to_dict(
        self
    ):

        return {
            "id":
                self.id,

            "source_id":
                self.source_id,

            "target_id":
                self.target_id,

            "relation":
                self.relation,

            "weight":
                self.weight,

            "created_at":
                self.created_at,

            "metadata":
                self.metadata
        }


@dataclass
class MemoryHistory:

    id: str

    memory_id: Optional[str]

    operation: str

    old_content: Any = None

    new_content: Any = None

    created_at: str = ""

    metadata: dict = field(
        default_factory=dict
    )

    def to_dict(
        self
    ):

        return {
            "id":
                self.id,

            "memory_id":
                self.memory_id,

            "operation":
                self.operation,

            "old_content":
                self.old_content,

            "new_content":
                self.new_content,

            "created_at":
                self.created_at,

            "metadata":
                self.metadata
        }


@dataclass
class MemoryContext:

    memories: list = field(
        default_factory=list
    )

    relations: list = field(
        default_factory=list
    )

    recent_conversations: list = field(
        default_factory=list
    )

    recent_messages: list = field(
        default_factory=list
    )

    summary: str = ""

    metadata: dict = field(
        default_factory=dict
    )