import hashlib
import sys
from pathlib import Path


class EmbeddingIndexer:

    """
    Genera y mantiene los embeddings de las memorias
    almacenadas en SQLite.

    Este proceso sirve para:

    - indexar memorias antiguas;
    - detectar embeddings inexistentes;
    - detectar memorias cuyo contenido cambió;
    - regenerar únicamente lo necesario;
    - evitar trabajo duplicado.

    Los embeddings quedan guardados permanentemente
    en aura.db.
    """

    def __init__(
        self,
        base_dir
    ):

        self.base_dir = Path(
            base_dir
        ).resolve()

        from .memory_config import MemoryConfig
        from .memory_store import MemoryStore
        from .embedding_engine import EmbeddingEngine

        self.config = MemoryConfig()

        database_path = (
            self.config.database_path(
                self.base_dir
            )
        )

        self.store = MemoryStore(
            database_path
        )

        self.engine = EmbeddingEngine(
            self.base_dir,
            self.config
        )

    # ==================================================
    # EJECUTAR
    # ==================================================

    def run(
        self,
        batch_size=None
    ):

        if batch_size is None:

            batch_size = (
                self.config.EMBEDDING_BATCH_SIZE
            )

        memories = self.store.list_memories(
            status="active",
            limit=100000
        )

        if not memories:

            print(
                "No hay memorias que indexar."
            )

            return {
                "total": 0,
                "indexed": 0,
                "skipped": 0,
                "errors": 0
            }

        indexed = 0
        skipped = 0
        errors = 0

        pending = []

        for memory in memories:

            try:

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
                        memory["id"]
                    )
                )

                # ------------------------------------------
                # Ya existe y pertenece exactamente al
                # mismo contenido.
                # ------------------------------------------

                if (
                    existing
                    and
                    existing.get(
                        "content_hash"
                    )
                    ==
                    content_hash
                ):

                    skipped += 1

                    continue

                pending.append({
                    "memory": memory,
                    "text": text,
                    "content_hash": content_hash
                })

            except Exception as error:

                errors += 1

                print(
                    f"[ERROR] Preparando "
                    f"{memory.get('id')}: "
                    f"{error}"
                )

        total_pending = len(
            pending
        )

        print()
        print(
            f"Memorias totales: "
            f"{len(memories)}"
        )

        print(
            f"Pendientes de indexar: "
            f"{total_pending}"
        )

        print(
            f"Ya indexadas: "
            f"{skipped}"
        )

        print()

        # ==================================================
        # PROCESAMIENTO POR LOTES
        # ==================================================

        for start in range(
            0,
            total_pending,
            batch_size
        ):

            batch = pending[
                start:
                start + batch_size
            ]

            texts = [
                item["text"]
                for item in batch
            ]

            try:

                vectors = (
                    self.engine.encode_batch(
                        texts
                    )
                )

            except Exception as error:

                errors += len(
                    batch
                )

                print(
                    "[ERROR] Lote de embeddings: "
                    f"{error}"
                )

                # ------------------------------------------
                # Intentamos individualmente.
                # Así un elemento defectuoso no impide
                # indexar todo el resto.
                # ------------------------------------------

                for item in batch:

                    try:

                        vector = (
                            self.engine.encode(
                                item["text"]
                            )
                        )

                        self._save(
                            item,
                            vector
                        )

                        indexed += 1

                    except Exception as individual_error:

                        print(
                            "[ERROR] Memoria "
                            f"{item['memory']['id']}: "
                            f"{individual_error}"
                        )

                continue

            # ==================================================
            # GUARDAR LOTE
            # ==================================================

            for item, vector in zip(
                batch,
                vectors
            ):

                try:

                    self._save(
                        item,
                        vector
                    )

                    indexed += 1

                except Exception as error:

                    errors += 1

                    print(
                        "[ERROR] Guardando "
                        f"{item['memory']['id']}: "
                        f"{error}"
                    )

            processed = min(
                start + len(batch),
                total_pending
            )

            print(
                f"Indexadas: "
                f"{processed}/{total_pending}"
            )

        # ==================================================
        # CERRAR
        # ==================================================

        self.engine.unload()

        result = {
            "total": len(memories),
            "indexed": indexed,
            "skipped": skipped,
            "errors": errors
        }

        print()
        print(
            "================================"
        )

        print(
            "Indexación completada."
        )

        print(
            f"Total: {result['total']}"
        )

        print(
            f"Nuevas: {result['indexed']}"
        )

        print(
            f"Sin cambios: {result['skipped']}"
        )

        print(
            f"Errores: {result['errors']}"
        )

        print(
            "================================"
        )

        return result

    # ==================================================
    # GUARDAR VECTOR
    # ==================================================

    def _save(
        self,
        item,
        vector_data
    ):

        if not vector_data:

            raise RuntimeError(
                "El modelo devolvió "
                "un vector vacío."
            )

        self.store.save_embedding(
            memory_id=item[
                "memory"
            ][
                "id"
            ],

            provider=(
                self.config.EMBEDDING_PROVIDER
            ),

            dimensions=len(
                vector_data
            ),

            vector=vector_data,

            content_hash=item[
                "content_hash"
            ]
        )

    # ==================================================
    # TEXTO DEL EMBEDDING
    # ==================================================

    @staticmethod
    def _embedding_text(
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

        category = memory.get(
            "category",
            ""
        )

        memory_type = memory.get(
            "memory_type",
            ""
        )

        content = memory.get(
            "content",
            ""
        )

        return (
            f"tipo: {memory_type}\n"
            f"categoria: {category}\n"
            f"concepto: {key}\n"
            f"informacion: {content}"
        )


def main():

    base_dir = Path(
        __file__
    ).resolve().parents[2]

    print()
    print(
        "================================"
    )
    print(
        "      AURA MEMORY INDEXER"
    )
    print(
        "================================"
    )
    print()

    try:

        indexer = EmbeddingIndexer(
            base_dir
        )

        indexer.run()

    except Exception as error:

        print()
        print(
            "[ERROR]"
        )

        print(
            str(error)
        )

        print()

        return 1

    return 0


if __name__ == "__main__":

    sys.exit(
        main()
    )