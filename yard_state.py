"""
Yard state store: entity registration, state transitions, and audit log.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class YardEvent:
    """Represents a single state-change event in the yard audit log."""

    def __init__(self, event_type: str, entity_id: str, payload: Dict):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.entity_id = entity_id
        self.timestamp = datetime.utcnow().isoformat()
        self.payload = payload

    def serialize(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "entity_id": self.entity_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }


class YardStateStore:
    """
    In-memory store for yard entities and their current states.
    Maintains a full audit log of all state transitions.
    """

    ALLOWED_TRAILER_STATES = {
        "STAGED_DROPPED", "IN_TRANSIT", "DOCKED",
        "MAINTENANCE_HOLD", "GATE_IN", "GATE_OUT",
    }

    def __init__(self):
        self.docks: Dict[str, Dict] = {}
        self.trailers: Dict[str, Dict] = {}
        self.jockeys: Dict[str, Dict] = {}
        self.pending_requests: Dict[str, Dict] = {}
        self.events: List[YardEvent] = []

    def register_dock(self, dock_data: Dict) -> None:
        """Validate and store a dock entity."""
        required = {"dock_id", "location", "status", "compatible_types", "capacity_feet"}
        missing = required - dock_data.keys()
        if missing:
            raise ValueError(f"Dock registration missing fields: {missing}")
        self.docks[dock_data["dock_id"]] = dict(dock_data)
        self.emit_event("DOCK_REGISTERED", dock_data["dock_id"], dock_data)

    def register_trailer(self, trailer_data: Dict) -> None:
        """Validate and store a trailer entity with initial state."""
        required = {"trailer_id", "trailer_type", "length_feet", "carrier_id"}
        missing = required - trailer_data.keys()
        if missing:
            raise ValueError(f"Trailer registration missing fields: {missing}")
        trailer_data.setdefault("state", "GATE_IN")
        self.trailers[trailer_data["trailer_id"]] = dict(trailer_data)
        self.emit_event("TRAILER_REGISTERED", trailer_data["trailer_id"], trailer_data)

    def register_jockey(self, jockey_data: Dict) -> None:
        """Validate and store a jockey entity."""
        required = {"jockey_id", "location", "status"}
        missing = required - jockey_data.keys()
        if missing:
            raise ValueError(f"Jockey registration missing fields: {missing}")
        self.jockeys[jockey_data["jockey_id"]] = dict(jockey_data)
        self.emit_event("JOCKEY_REGISTERED", jockey_data["jockey_id"], jockey_data)

    def emit_event(self, event_type: str, entity_id: str, payload: Dict) -> YardEvent:
        """Create and record a yard event."""
        event = YardEvent(event_type, entity_id, payload)
        self.events.append(event)
        return event

    def get_trailer_state(self, trailer_id: str) -> Optional[str]:
        """Return the current state string for a trailer."""
        trailer = self.trailers.get(trailer_id)
        return trailer.get("state") if trailer else None

    def transition_trailer_state(self, trailer_id: str, new_state: str, triggered_by: str) -> None:
        """
        Validate and apply a state transition for a trailer.
        Records the transition as a yard event.
        """
        if new_state not in self.ALLOWED_TRAILER_STATES:
            raise ValueError(f"Invalid trailer state: {new_state}")
        if trailer_id not in self.trailers:
            raise KeyError(f"Trailer {trailer_id} not registered")
        old_state = self.trailers[trailer_id].get("state")
        self.trailers[trailer_id]["state"] = new_state
        self.emit_event(
            "TRAILER_STATE_CHANGED",
            trailer_id,
            {"old_state": old_state, "new_state": new_state, "triggered_by": triggered_by},
        )

    def get_dock_occupancy_rate(self) -> float:
        """Return fraction of docks that are currently occupied."""
        if not self.docks:
            return 0.0
        occupied = sum(1 for d in self.docks.values() if d.get("status") == "occupied")
        return occupied / len(self.docks)

    def get_audit_log(self, since_minutes: int = 60) -> List[Dict]:
        """Return events within the last N minutes, serialized."""
        cutoff = datetime.utcnow() - timedelta(minutes=since_minutes)
        return [
            e.serialize()
            for e in self.events
            if datetime.fromisoformat(e.timestamp) >= cutoff
        ]

    def export_snapshot(self) -> Dict:
        """Return a serializable dict representing the full yard state."""
        return {
            "snapshot_at": datetime.utcnow().isoformat(),
            "docks": dict(self.docks),
            "trailers": dict(self.trailers),
            "jockeys": dict(self.jockeys),
            "pending_requests": dict(self.pending_requests),
            "total_events": len(self.events),
        }


if __name__ == "__main__":
    store = YardStateStore()
    store.register_dock({
        "dock_id": "D1", "location": [10.0, 0.0],
        "status": "empty", "compatible_types": ["reefer", "dry_van"], "capacity_feet": 53,
    })
    store.register_trailer({
        "trailer_id": "T1", "trailer_type": "reefer",
        "length_feet": 53, "carrier_id": "CARRIER_A",
    })
    store.transition_trailer_state("T1", "IN_TRANSIT", triggered_by="router.assign_move_request")
    store.transition_trailer_state("T1", "DOCKED", triggered_by="jockey.J1.complete")

    print("Occupancy rate:", store.get_dock_occupancy_rate())
    print("Audit log entries:", len(store.get_audit_log()))
    snapshot = store.export_snapshot()
    print("Snapshot trailers:", snapshot["trailers"])
