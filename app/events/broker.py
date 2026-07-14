"""Asynchronous Event Broker and Pydantic event schemas for GxP workflow coordination."""

import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Callable, Any, Awaitable
from pydantic import BaseModel, Field
from enum import Enum

logger = logging.getLogger("app.events")


class QualityEventType(str, Enum):
    """Supported inter-agent coordination event types."""
    URS_MODIFIED = "URS_MODIFIED"
    TEST_FAILED = "TEST_FAILED"
    SIGNATURE_REVOKED = "SIGNATURE_REVOKED"
    GUARDRAIL_TRIPPED = "GUARDRAIL_TRIPPED"
    POLICY_DRIFT_DETECTED = "POLICY_DRIFT_DETECTED"


class QualityEvent(BaseModel):
    """Immutable record representing a system-wide GxP status transition event."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: QualityEventType
    tenant_id: str = Field(..., description="Strictly scopes routing and handler executions.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    triggered_by_user: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Traces cascading actions back to origin.")


# Type hint for asynchronous event subscriber callables
EventHandler = Callable[[QualityEvent], Awaitable[None]]


class QualityEventBroker:
    """Central asynchronous in-memory Pub/Sub event broker."""

    def __init__(self) -> None:
        # Maps event type keys to lists of handler functions
        self._subscribers: Dict[QualityEventType, List[EventHandler]] = {
            t: [] for t in QualityEventType
        }

    def subscribe(self, event_type: QualityEventType, handler: EventHandler) -> None:
        """Registers a listener callback for a specific quality event.

        Args:
            event_type: The event type to listen to.
            handler: Asynchronous callable receiving the published QualityEvent.
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.info(f"EVENT_BUS: Subscribed handler {handler.__name__} to event {event_type.value}.")

    async def publish(self, event: QualityEvent, audit_logger=None) -> None:
        """Dispatches an event asynchronously to all registered subscriber functions.

        Automatically writes a record to the GxP audit log.

        Args:
            event: The QualityEvent instance to publish.
            audit_logger: Optional AuditLogger instance to trace the pub/sub event.
        """
        # Formulate audit log record
        log_msg = (
            f"Event '{event.event_type.value}' published. ID: {event.event_id}, "
            f"Tenant: {event.tenant_id}, Triggered by: {event.triggered_by_user}, "
            f"Correlation ID: {event.correlation_id}."
        )
        logger.info(log_msg)
        if audit_logger:
            audit_logger.log_step("EventBus:Publish", log_msg)

        # Retrieve matching handlers
        handlers = self._subscribers.get(event.event_type, [])
        if not handlers:
            return

        # Trigger handlers asynchronously (non-blocking task scheduling)
        for handler in handlers:
            # We schedule each task on the active event loop to ensure publishing returns instantly
            asyncio.create_task(self._safe_execute_handler(handler, event, audit_logger))

    async def _safe_execute_handler(
        self,
        handler: EventHandler,
        event: QualityEvent,
        audit_logger=None
    ) -> None:
        """Executes a subscriber handler, isolating exceptions to prevent publisher crashes."""
        try:
            await handler(event)
        except Exception as e:
            err_msg = f"EVENT_BUS: Handler '{handler.__name__}' failed on event '{event.event_id}': {e}"
            logger.error(err_msg)
            if audit_logger:
                audit_logger.log_step("EventBus:HandlerError", err_msg)
