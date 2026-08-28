from datetime import datetime


class WorkingMemory:

    """
    Memoria de trabajo de AURA.

    Mantiene información activa durante la sesión y durante
    la resolución de una tarea.

    La memoria de trabajo NO sustituye a la memoria persistente.

    Se utiliza para:

    - tema actual;
    - objetivo actual;
    - tarea activa;
    - estado de una tarea;
    - entidades activas;
    - decisiones recientes;
    - contexto temporal;
    - información que todavía no debe convertirse
      en memoria permanente.

    La información se mantiene en RAM y desaparece al cerrar
    AURA, salvo que posteriormente sea consolidada por el
    sistema de memoria a largo plazo.
    """

    def __init__(
        self,
        max_items=40
    ):

        self.max_items = (
            max_items
        )

        self.session_id = None

        self.created_at = None

        self.updated_at = None

        self.topic = None

        self.goal = None

        self.task = None

        self.task_state = None

        self.entities = {}

        self.decisions = []

        self.active_information = []

        self.recent_turns = []

        self.metadata = {}

    # ==================================================
    # INICIO
    # ==================================================

    def start(
        self,
        session_id=None,
        metadata=None
    ):

        now = self._now()

        self.session_id = (
            session_id
            or
            self._session_id()
        )

        self.created_at = now

        self.updated_at = now

        self.topic = None

        self.goal = None

        self.task = None

        self.task_state = None

        self.entities.clear()

        self.decisions.clear()

        self.active_information.clear()

        self.recent_turns.clear()

        self.metadata = dict(
            metadata or {}
        )

    # ==================================================
    # RESET
    # ==================================================

    def clear(
        self
    ):

        self.topic = None

        self.goal = None

        self.task = None

        self.task_state = None

        self.entities.clear()

        self.decisions.clear()

        self.active_information.clear()

        self.recent_turns.clear()

        self.updated_at = self._now()

    # ==================================================
    # TEMA
    # ==================================================

    def set_topic(
        self,
        topic
    ):

        if topic is None:

            return

        topic = str(
            topic
        ).strip()

        if not topic:

            return

        self.topic = topic

        self._touch()

    # ==================================================
    # OBJETIVO
    # ==================================================

    def set_goal(
        self,
        goal
    ):

        if goal is None:

            return

        goal = str(
            goal
        ).strip()

        if not goal:

            return

        self.goal = goal

        self._touch()

    # ==================================================
    # TAREA
    # ==================================================

    def set_task(
        self,
        task,
        state=None
    ):

        if task is not None:

            task = str(
                task
            ).strip()

            if task:

                self.task = task

        if state is not None:

            self.task_state = str(
                state
            ).strip()

        self._touch()

    # ==================================================
    # ENTIDADES
    # ==================================================

    def set_entity(
        self,
        name,
        value,
        entity_type=None
    ):

        if name is None:

            return

        name = str(
            name
        ).strip()

        if not name:

            return

        self.entities[name] = {
            "name": name,
            "value": value,
            "type": (
                str(
                    entity_type
                ).strip()
                if entity_type
                else "unknown"
            ),
            "updated_at": self._now()
        }

        self._limit_entities()

        self._touch()

    # ==================================================
    # DECISIÓN
    # ==================================================

    def add_decision(
        self,
        decision
    ):

        if decision is None:

            return

        decision = str(
            decision
        ).strip()

        if not decision:

            return

        self.decisions.append({
            "content": decision,
            "timestamp": self._now()
        })

        self._limit_list(
            self.decisions,
            12
        )

        self._touch()

    # ==================================================
    # INFORMACIÓN ACTIVA
    # ==================================================

    def add_information(
        self,
        content,
        importance=0.5,
        source="conversation",
        temporary=True
    ):

        if content is None:

            return

        content = str(
            content
        ).strip()

        if not content:

            return

        item = {
            "content": content,

            "importance": self._clamp(
                importance
            ),

            "source": str(
                source
            ),

            "temporary": bool(
                temporary
            ),

            "timestamp": self._now()
        }

        self.active_information.append(
            item
        )

        self._limit_list(
            self.active_information,
            self.max_items
        )

        self._touch()

    # ==================================================
    # TURNO
    # ==================================================

    def add_turn(
        self,
        role,
        content
    ):

        if not content:

            return

        self.recent_turns.append({
            "role": str(
                role
            ),

            "content": str(
                content
            ),

            "timestamp": self._now()
        })

        self._limit_list(
            self.recent_turns,
            10
        )

        self._touch()

    # ==================================================
    # OBTENER ESTADO
    # ==================================================

    def get_state(
        self
    ):

        return {
            "session_id":
                self.session_id,

            "topic":
                self.topic,

            "goal":
                self.goal,

            "task":
                self.task,

            "task_state":
                self.task_state,

            "entities":
                dict(
                    self.entities
                ),

            "decisions":
                list(
                    self.decisions
                ),

            "active_information":
                list(
                    self.active_information
                ),

            "recent_turns":
                list(
                    self.recent_turns
                ),

            "metadata":
                dict(
                    self.metadata
                ),

            "created_at":
                self.created_at,

            "updated_at":
                self.updated_at
        }

    # ==================================================
    # CONTEXTO PARA EL MODELO
    # ==================================================

    def build_context(
        self,
        max_chars=4500
    ):

        sections = []

        if self.topic:

            sections.append(
                f"TEMA ACTUAL:\n{self.topic}"
            )

        if self.goal:

            sections.append(
                f"OBJETIVO ACTUAL:\n{self.goal}"
            )

        if self.task:

            task_text = self.task

            if self.task_state:

                task_text += (
                    f"\nEstado: "
                    f"{self.task_state}"
                )

            sections.append(
                f"TAREA ACTIVA:\n{task_text}"
            )

        if self.entities:

            lines = []

            for item in self.entities.values():

                lines.append(
                    "- "
                    f"{item['name']}: "
                    f"{item['value']}"
                )

            sections.append(
                "ENTIDADES ACTIVAS:\n"
                +
                "\n".join(
                    lines
                )
            )

        if self.decisions:

            lines = [
                "- "
                + item["content"]
                for item in self.decisions[-8:]
            ]

            sections.append(
                "DECISIONES RECIENTES:\n"
                +
                "\n".join(
                    lines
                )
            )

        if self.active_information:

            lines = [
                "- "
                + item["content"]
                for item in self.active_information[-12:]
            ]

            sections.append(
                "INFORMACIÓN ACTIVA:\n"
                +
                "\n".join(
                    lines
                )
            )

        if not sections:

            return ""

        context = (
            "MEMORIA DE TRABAJO\n"
            "===================\n\n"
            +
            "\n\n".join(
                sections
            )
        )

        if len(context) <= max_chars:

            return context

        return (
            context[:max_chars]
            +
            "\n\n[MEMORIA DE TRABAJO RECORTADA]"
        )

    # ==================================================
    # ACTUALIZAR POR TURNO
    # ==================================================

    def observe_turn(
        self,
        role,
        content
    ):

        self.add_turn(
            role,
            content
        )

    # ==================================================
    # EXPORTAR
    # ==================================================

    def to_dict(
        self
    ):

        return self.get_state()

    # ==================================================
    # UTILIDADES
    # ==================================================

    def _touch(
        self
    ):

        self.updated_at = self._now()

    def _limit_entities(
        self
    ):

        if len(
            self.entities
        ) <= 20:

            return

        ordered = sorted(
            self.entities.items(),
            key=lambda item:
                item[1].get(
                    "updated_at",
                    ""
                ),
            reverse=True
        )

        self.entities = dict(
            ordered[:20]
        )

    @staticmethod
    def _limit_list(
        items,
        maximum
    ):

        if len(items) <= maximum:

            return

        del items[
            :-maximum
        ]

    @staticmethod
    def _clamp(
        value
    ):

        try:

            value = float(
                value
            )

        except Exception:

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

    @staticmethod
    def _session_id():

        import uuid

        return (
            "session_"
            +
            uuid.uuid4().hex[:16]
        )