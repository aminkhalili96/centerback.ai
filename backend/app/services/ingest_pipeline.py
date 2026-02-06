"""Background ingestion queue processor."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select, update

from app.config import settings
from app.db import db_session
from app.models.entities import IngestionMessage, QueueStatus
from app.services.classifier import ClassifierService
from app.services.detection_service import detection_service

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Processes queued ingestion messages into classification events."""

    def __init__(self) -> None:
        self._classifier = ClassifierService()
        self._task: asyncio.Task | None = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop(), name="ingestion-pipeline")
        logger.info("Ingestion pipeline started")

    async def stop(self) -> None:
        self._running = False
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None
        logger.info("Ingestion pipeline stopped")

    async def _run_loop(self) -> None:
        while self._running:
            processed = await asyncio.to_thread(self._process_batch)
            if processed == 0:
                await asyncio.sleep(settings.ingest_poll_interval_seconds)

    def _process_batch(self) -> int:
        processed = 0
        with db_session() as db:
            candidate_ids = db.execute(
                select(IngestionMessage.id)
                .where(IngestionMessage.status.in_([QueueStatus.queued.value, QueueStatus.failed.value]))
                .where(IngestionMessage.attempts < settings.ingest_max_attempts)
                .order_by(IngestionMessage.created_at)
                .limit(settings.ingest_batch_size)
            ).scalars().all()

            for message_id in candidate_ids:
                claimed = db.execute(
                    update(IngestionMessage)
                    .where(IngestionMessage.id == message_id)
                    .where(IngestionMessage.status.in_([QueueStatus.queued.value, QueueStatus.failed.value]))
                    .values(
                        status=QueueStatus.processing.value,
                        attempts=IngestionMessage.attempts + 1,
                    )
                )
                if claimed.rowcount == 0:
                    continue

                message = db.get(IngestionMessage, message_id)
                if message is None:
                    continue
                processed += 1

                try:
                    payload = message.payload or {}
                    features = payload.get("features")
                    if not isinstance(features, list) or len(features) != 78:
                        raise ValueError("Invalid features payload. Expected list of 78 floats.")

                    prediction = self._classifier.predict_single(features)
                    detection_service.record_classification(
                        db=db,
                        prediction=prediction["prediction"],
                        confidence=float(prediction["confidence"]),
                        is_threat=bool(prediction["is_threat"]),
                        source=str(payload.get("source", message.source)),
                        source_ip=str(payload.get("source_ip", "unknown")),
                        destination_ip=str(payload.get("destination_ip", "unknown")),
                        features=[float(v) for v in features],
                        model_version=prediction.get("model_version"),
                        extra_metadata={
                            "flow_id": payload.get("flow_id"),
                            "ingestion_message_id": message.id,
                        },
                    )
                    message.status = QueueStatus.done.value
                    message.last_error = None
                except Exception as exc:
                    message.last_error = str(exc)
                    if message.attempts >= settings.ingest_max_attempts:
                        message.status = QueueStatus.dead_letter.value
                    else:
                        message.status = QueueStatus.failed.value
                    logger.warning("Failed ingestion message %s: %s", message.id, exc)

        return processed


ingestion_pipeline = IngestionPipeline()
