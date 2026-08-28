from pathlib import Path

from core.model_manager import ModelManager
from core.conversation_manager import ConversationManager
from core.system_context import SystemContext
from core.tool_manager import ToolManager
from core.tool_parser import ToolParser
from core.tool_executor import ToolExecutor
from core.agent import Agent
from core.cognitive_orchestrator import CognitiveOrchestrator

from core.memory.memory_manager import MemoryManager
from core.memory.memory_learner import MemoryLearner

from tools.system_tool import SystemTool
from tools.memory_tool import MemoryTool


BASE_DIR = (
    Path(__file__).resolve().parent
)


def create_tool_manager(
    system_context,
    memory_manager
):

    tool_manager = ToolManager()

    # ==================================================
    # SYSTEM
    # ==================================================

    system_tool = SystemTool(
        system_context
    )

    tool_manager.register(
        system_tool.name,
        system_tool
    )

    # ==================================================
    # MEMORY
    # ==================================================

    memory_tool = MemoryTool(
        memory_manager
    )

    tool_manager.register(
        memory_tool.name,
        memory_tool
    )

    return tool_manager


def main():

    print()
    print("================================")
    print("             AURA")
    print("================================")
    print()

    print(
        "Iniciando sistema..."
    )

    print()

    # ==================================================
    # MODELO
    # ==================================================

    model = ModelManager()

    # ==================================================
    # CONVERSACIÓN TEMPORAL DEL AGENTE
    # ==================================================

    conversation = (
        ConversationManager(
            max_messages=10
        )
    )

    # ==================================================
    # CONTEXTO DEL SISTEMA
    # ==================================================

    system = SystemContext(
        BASE_DIR
    )

    # ==================================================
    # MEMORIA CENTRAL
    # ==================================================

    print(
        "Inicializando memoria..."
    )

    memory_manager = (
        MemoryManager(
            BASE_DIR
        )
    )

    memory_learner = None

    cognitive_orchestrator = None

    tool_manager = None

    tool_parser = None

    tool_executor = None

    agent = None

    memory_conversation_id = None

    # ==================================================
    # ARRANQUE
    # ==================================================

    try:

        print(
            "Cargando modelo..."
        )

        model.load()

        print(
            "Modelo cargado."
        )

        print()

        # ==================================================
        # CONECTAR MODELO CON MEMORIA
        # ==================================================

        memory_manager.attach_model(
            model
        )

        # ==================================================
        # APRENDIZAJE
        # ==================================================

        memory_learner = (
            MemoryLearner(
                model=model,
                memory_manager=memory_manager
            )
        )

        # ==================================================
        # ORQUESTADOR COGNITIVO
        # ==================================================

        cognitive_orchestrator = (
            CognitiveOrchestrator(
                memory_manager=memory_manager,
                memory_learner=memory_learner
            )
        )

        # ==================================================
        # HERRAMIENTAS
        # ==================================================

        tool_manager = create_tool_manager(
            system_context=system,
            memory_manager=memory_manager
        )

        tool_parser = ToolParser()

        tool_executor = ToolExecutor(
            tool_manager
        )

        # ==================================================
        # AGENTE
        # ==================================================

        agent = Agent(
            model=model,
            conversation=conversation,
            tool_manager=tool_manager,
            tool_parser=tool_parser,
            tool_executor=tool_executor,
            memory_manager=memory_manager,
            memory_learner=memory_learner,
            cognitive_orchestrator=(
                cognitive_orchestrator
            )
        )

        # ==================================================
        # INICIAR MEMORIA EPISÓDICA
        # ==================================================

        try:

            memory_conversation_id = (
                memory_manager
                .start_conversation(
                    title="Sesión de AURA"
                )
            )

        except Exception as error:

            print(
                "[Advertencia] No se pudo iniciar "
                f"la memoria episódica: {error}"
            )

        # ==================================================
        # ESTADO
        # ==================================================

        print(
            "AURA está lista."
        )

        print()

        print(
            "Herramientas:",
            tool_manager.list_tools()
        )

        print()

        try:

            status = (
                memory_manager
                .get_status()
            )

            print(
                "Base de memoria:",
                status.get(
                    "database"
                )
            )

            print(
                "FTS:",
                status.get(
                    "fts_available"
                )
            )

            print(
                "Embeddings:",
                status.get(
                    "embeddings_enabled"
                )
            )

            print(
                "Predicciones:",
                status.get(
                    "prediction_enabled"
                )
            )

            print(
                "Procedimientos:",
                status.get(
                    "procedural_learning"
                )
            )

            print(
                "Memoria episódica:",
                status.get(
                    "episodic_memory"
                )
            )

            print()

        except Exception as error:

            print(
                "[Advertencia al mostrar estado]",
                error
            )

            print()

        # ==================================================
        # BUCLE PRINCIPAL
        # ==================================================

        while True:

            try:

                user_message = input(
                    "Tú: "
                ).strip()

            except (
                KeyboardInterrupt,
                EOFError
            ):

                print()

                break

            if not user_message:

                continue

            if user_message.lower() in {
                "salir",
                "exit",
                "quit"
            }:

                break

            print()

            print(
                "AURA está pensando..."
            )

            try:

                response = agent.process(
                    user_message
                )

                print()

                print(
                    f"AURA: {response}"
                )

                print()

            except Exception as error:

                print()

                print(
                    "AURA: Ha ocurrido un problema "
                    "al procesar eso."
                )

                print()

                print(
                    f"[Error interno] {error}"
                )

                print()

    except Exception as error:

        print()

        print(
            "AURA no ha podido iniciar correctamente."
        )

        print()

        print(
            f"[Error de inicio] {error}"
        )

        print()

    finally:

        # ==================================================
        # CERRAR EPISODIO
        # ==================================================

        if (
            memory_manager is not None
            and
            memory_conversation_id is not None
        ):

            try:

                memory_manager.end_conversation()

            except Exception as error:

                print(
                    "[Advertencia al cerrar "
                    f"la memoria episódica] {error}"
                )

        print()

        print(
            "Cerrando AURA..."
        )

        try:

            model.unload()

        except Exception as error:

            print(
                f"[Error al cerrar el modelo] {error}"
            )

        print(
            "Sistema detenido."
        )


if __name__ == "__main__":
    main()