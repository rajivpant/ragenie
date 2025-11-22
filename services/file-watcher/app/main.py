"""Main file watcher service."""
import asyncio
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import asyncpg
import structlog
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()


class RagbotDataWatcher(FileSystemEventHandler):
    """File system event handler for ragbot-data directory."""

    def __init__(self, db_pool: asyncpg.Pool):
        """Initialize the watcher with a database pool."""
        self.db_pool = db_pool
        self.loop = asyncio.get_event_loop()
        self.file_hashes = {}  # Cache of file hashes
        logger.info("RagbotDataWatcher initialized")

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        # Check if file matches our criteria
        if not self._should_process(event.src_path):
            return

        logger.info("file_modified", path=event.src_path)

        # Schedule async processing
        asyncio.run_coroutine_threadsafe(
            self._process_file_change(event.src_path),
            self.loop
        )

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        logger.info("file_created", path=event.src_path)

        asyncio.run_coroutine_threadsafe(
            self._process_file_change(event.src_path),
            self.loop
        )

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if event.is_directory:
            return

        if not self._should_process(event.src_path):
            return

        logger.info("file_deleted", path=event.src_path)

        asyncio.run_coroutine_threadsafe(
            self._process_file_deletion(event.src_path),
            self.loop
        )

    def _should_process(self, file_path: str) -> bool:
        """Check if file should be processed."""
        path = Path(file_path)

        # Check file extension
        if path.suffix not in settings.INCLUDE_EXTENSIONS:
            return False

        # Check exclude patterns
        for pattern in settings.EXCLUDE_PATTERNS:
            if pattern in str(path):
                return False

        return True

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA-256 hash of file content."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error("hash_computation_failed", path=file_path, error=str(e))
            return ""

    def _get_relative_path(self, absolute_path: str) -> str:
        """Get path relative to ragbot-data root."""
        try:
            return str(Path(absolute_path).relative_to(settings.RAGBOT_DATA_PATH))
        except ValueError:
            logger.error("path_not_relative", path=absolute_path)
            return absolute_path

    async def _process_file_change(self, file_path: str) -> None:
        """Process file change (creation or modification)."""
        try:
            # Get file info
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            modified_at = datetime.fromtimestamp(file_stat.st_mtime)

            # Compute content hash
            content_hash = self._compute_file_hash(file_path)
            if not content_hash:
                return

            # Get relative path
            relative_path = self._get_relative_path(file_path)

            # Check if hash changed
            cached_hash = self.file_hashes.get(relative_path)
            if cached_hash == content_hash:
                logger.debug("file_unchanged", path=relative_path, hash=content_hash[:16])
                return

            # Update cache
            self.file_hashes[relative_path] = content_hash

            # Check database
            async with self.db_pool.acquire() as conn:
                existing = await conn.fetchrow(
                    "SELECT id, content_hash, embedding_status FROM ragbot_documents WHERE file_path = $1",
                    relative_path
                )

                if existing:
                    if existing['content_hash'] == content_hash:
                        logger.debug("file_unchanged_in_db", path=relative_path)
                        return

                    # File changed - update record and queue for re-embedding
                    logger.info(
                        "file_changed",
                        path=relative_path,
                        old_hash=existing['content_hash'][:16],
                        new_hash=content_hash[:16]
                    )

                    # Update document record
                    await conn.execute("""
                        UPDATE ragbot_documents
                        SET content_hash = $1,
                            file_size = $2,
                            modified_at = $3,
                            embedding_status = 'pending',
                            chunk_count = 0,
                            indexed_at = NULL,
                            error_message = NULL,
                            updated_at = NOW()
                        WHERE file_path = $4
                    """, content_hash, file_size, modified_at, relative_path)

                    # Queue for re-embedding with high priority
                    await conn.execute("""
                        INSERT INTO embedding_queue (document_type, document_id, priority, status)
                        VALUES ('ragbot', $1, 10, 'pending')
                    """, existing['id'])

                    logger.info("reembedding_queued", path=relative_path, document_id=str(existing['id']))

                else:
                    # New file - create record and queue for embedding
                    logger.info("new_file_detected", path=relative_path, size=file_size, hash=content_hash[:16])

                    # Insert document record
                    document_id = await conn.fetchval("""
                        INSERT INTO ragbot_documents (
                            file_path, content_hash, file_size, modified_at,
                            embedding_status, metadata, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, 'pending', $5, NOW(), NOW())
                        RETURNING id
                    """, relative_path, content_hash, file_size, modified_at, {
                        'detected_by': 'file_watcher',
                        'first_seen': datetime.now().isoformat()
                    })

                    # Queue for embedding
                    await conn.execute("""
                        INSERT INTO embedding_queue (document_type, document_id, priority, status)
                        VALUES ('ragbot', $1, 10, 'pending')
                    """, document_id)

                    logger.info("new_file_queued", path=relative_path, document_id=str(document_id))

        except Exception as e:
            logger.error("process_file_change_failed", path=file_path, error=str(e), exc_info=True)

    async def _process_file_deletion(self, file_path: str) -> None:
        """Process file deletion."""
        try:
            relative_path = self._get_relative_path(file_path)

            # Remove from cache
            self.file_hashes.pop(relative_path, None)

            # Mark as deleted in database
            async with self.db_pool.acquire() as conn:
                result = await conn.execute("""
                    UPDATE ragbot_documents
                    SET embedding_status = 'deleted',
                        updated_at = NOW()
                    WHERE file_path = $1
                """, relative_path)

                if result == "UPDATE 1":
                    logger.info("file_marked_deleted", path=relative_path)
                else:
                    logger.debug("deleted_file_not_in_db", path=relative_path)

        except Exception as e:
            logger.error("process_file_deletion_failed", path=file_path, error=str(e))


async def scan_existing_files(db_pool: asyncpg.Pool) -> None:
    """Scan existing files in ragbot-data on startup."""
    logger.info("scanning_existing_files", path=str(settings.RAGBOT_DATA_PATH))

    file_count = 0
    for root, dirs, files in os.walk(settings.RAGBOT_DATA_PATH):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in settings.EXCLUDE_PATTERNS]

        for file in files:
            if not any(file.endswith(ext) for ext in settings.INCLUDE_EXTENSIONS):
                continue

            full_path = os.path.join(root, file)
            relative_path = str(Path(full_path).relative_to(settings.RAGBOT_DATA_PATH))

            try:
                # Get file info
                file_stat = os.stat(full_path)
                file_size = file_stat.st_size
                modified_at = datetime.fromtimestamp(file_stat.st_mtime)

                # Compute hash
                sha256_hash = hashlib.sha256()
                with open(full_path, "rb") as f:
                    for byte_block in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(byte_block)
                content_hash = sha256_hash.hexdigest()

                # Check if exists in database
                async with db_pool.acquire() as conn:
                    existing = await conn.fetchrow(
                        "SELECT id, content_hash FROM ragbot_documents WHERE file_path = $1",
                        relative_path
                    )

                    if not existing:
                        # New file - insert and queue
                        document_id = await conn.fetchval("""
                            INSERT INTO ragbot_documents (
                                file_path, content_hash, file_size, modified_at,
                                embedding_status, metadata, created_at, updated_at
                            )
                            VALUES ($1, $2, $3, $4, 'pending', $5, NOW(), NOW())
                            RETURNING id
                        """, relative_path, content_hash, file_size, modified_at, {
                            'detected_by': 'initial_scan',
                            'scanned_at': datetime.now().isoformat()
                        })

                        await conn.execute("""
                            INSERT INTO embedding_queue (document_type, document_id, priority, status)
                            VALUES ('ragbot', $1, 5, 'pending')
                        """, document_id)

                        logger.debug("file_discovered", path=relative_path)
                        file_count += 1

                    elif existing['content_hash'] != content_hash:
                        # File changed - update and requeue
                        await conn.execute("""
                            UPDATE ragbot_documents
                            SET content_hash = $1,
                                file_size = $2,
                                modified_at = $3,
                                embedding_status = 'pending',
                                chunk_count = 0,
                                indexed_at = NULL,
                                error_message = NULL,
                                updated_at = NOW()
                            WHERE file_path = $4
                        """, content_hash, file_size, modified_at, relative_path)

                        await conn.execute("""
                            INSERT INTO embedding_queue (document_type, document_id, priority, status)
                            VALUES ('ragbot', $1, 5, 'pending')
                        """, existing['id'])

                        logger.debug("file_changed_on_startup", path=relative_path)
                        file_count += 1

            except Exception as e:
                logger.error("scan_file_failed", path=relative_path, error=str(e))

    logger.info("initial_scan_complete", files_queued=file_count)


async def main() -> None:
    """Main entry point for file watcher service."""
    logger.info(
        "file_watcher_starting",
        data_path=str(settings.RAGBOT_DATA_PATH),
        polling_interval=settings.POLLING_INTERVAL
    )

    # Verify ragbot-data path exists
    if not settings.RAGBOT_DATA_PATH.exists():
        logger.error("ragbot_data_path_not_found", path=str(settings.RAGBOT_DATA_PATH))
        sys.exit(1)

    # Create database connection pool
    try:
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=5
        )
        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        sys.exit(1)

    # Scan existing files on startup
    await scan_existing_files(db_pool)

    # Create event handler and observer
    event_handler = RagbotDataWatcher(db_pool)
    observer = PollingObserver(timeout=settings.POLLING_INTERVAL)
    observer.schedule(event_handler, str(settings.RAGBOT_DATA_PATH), recursive=True)
    observer.start()

    logger.info(
        "file_watcher_running",
        watching=str(settings.RAGBOT_DATA_PATH),
        polling_interval=f"{settings.POLLING_INTERVAL}s"
    )

    try:
        # Keep running
        while True:
            await asyncio.sleep(60)  # Wake up every minute to check health
            logger.debug("file_watcher_heartbeat", watching=str(settings.RAGBOT_DATA_PATH))
    except KeyboardInterrupt:
        logger.info("file_watcher_stopping")
        observer.stop()
        observer.join()
        await db_pool.close()
        logger.info("file_watcher_stopped")


if __name__ == "__main__":
    asyncio.run(main())
