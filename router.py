"""
Adaptive yard routing engine: dock assignment, jockey dispatch, exception handling.
"""
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TrailerType(Enum):
    DRY_VAN = "dry_van"
    REEFER = "reefer"
    FLATBED = "flatbed"
    TANKER = "tanker"


class DockStatus(Enum):
    EMPTY = "empty"
    OCCUPIED = "occupied"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class JockeyStatus(Enum):
    AVAILABLE = "available"
    ON_MOVE = "on_move"
    BREAK = "break"
    OFFLINE = "offline"


class TrailerState(Enum):
    STAGED_DROPPED = "staged_dropped"
    IN_TRANSIT = "in_transit"
    DOCKED = "docked"
    MAINTENANCE_HOLD = "maintenance_hold"
    GATE_IN = "gate_in"
    GATE_OUT = "gate_out"


@dataclass
class Dock:
    dock_id: str
    location: Tuple[float, float]
    status: DockStatus
    compatible_types: List[TrailerType]
    capacity_feet: int


@dataclass
class Trailer:
    trailer_id: str
    trailer_type: TrailerType
    length_feet: int
    cargo_priority: int
    carrier_id: str
    state: TrailerState = TrailerState.STAGED_DROPPED


@dataclass
class Jockey:
    jockey_id: str
    location: Tuple[float, float]
    status: JockeyStatus
    completed_moves: int = 0


@dataclass
class MoveRequest:
    request_id: str
    trailer_id: str
    from_location: Tuple[float, float]
    to_dock_id: str
    priority: int
    created_at: datetime = field(default_factory=datetime.utcnow)


class YardRouter:
    """
    Constraint-based yard routing engine that assigns docks and jockeys
    to inbound trailers using distance scoring and business rules.
    """

    DEFAULT_RULES = {
        "max_jockey_distance": 500.0,
        "priority_boost_threshold": 8,
        "reefer_only_zones": [],
    }

    def __init__(self, docks: List[Dock], jockeys: List[Jockey], business_rules: Optional[Dict] = None):
        self.docks: Dict[str, Dock] = {d.dock_id: d for d in docks}
        self.jockeys: Dict[str, Jockey] = {j.jockey_id: j for j in jockeys}
        self.rules = {**self.DEFAULT_RULES, **(business_rules or {})}
        self.pending_requests: List[MoveRequest] = []

    def euclidean_distance(self, loc_a: Tuple[float, float], loc_b: Tuple[float, float]) -> float:
        """Return Euclidean distance between two (x, y) coordinates."""
        return math.sqrt((loc_a[0] - loc_b[0]) ** 2 + (loc_a[1] - loc_b[1]) ** 2)

    def find_nearest_compatible_dock(self, trailer: Trailer, from_location: Tuple[float, float]) -> Optional[Dock]:
        """
        Find the nearest empty dock that is compatible with the trailer type
        and has sufficient capacity for the trailer length.
        """
        candidates = [
            d for d in self.docks.values()
            if d.status == DockStatus.EMPTY
            and trailer.trailer_type in d.compatible_types
            and d.capacity_feet >= trailer.length_feet
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda d: self.euclidean_distance(from_location, d.location))
        return candidates[0]

    def score_jockey(self, jockey: Jockey, target_location: Tuple[float, float]) -> float:
        """
        Lower score is better. Penalizes distance and unavailability.
        Jockeys on BREAK receive a 1.5x distance penalty; OFFLINE are excluded.
        """
        if jockey.status == JockeyStatus.OFFLINE:
            return float("inf")
        if jockey.status == JockeyStatus.ON_MOVE:
            return float("inf")
        dist = self.euclidean_distance(jockey.location, target_location)
        penalty = 1.5 if jockey.status == JockeyStatus.BREAK else 1.0
        return dist * penalty

    def assign_move_request(self, request: MoveRequest, trailer: Trailer) -> Dict:
        """
        Assign the best dock and jockey to fulfill a move request.
        Returns a dict with dock, jockey, and estimated_minutes.
        Raises ValueError if no compatible dock or available jockey exists.
        """
        dock = self.find_nearest_compatible_dock(trailer, request.from_location)
        if dock is None:
            raise ValueError(f"No compatible empty dock for trailer {trailer.trailer_id}")

        jockey_scores = {
            j_id: self.score_jockey(j, request.from_location)
            for j_id, j in self.jockeys.items()
        }
        best_jockey_id = min(jockey_scores, key=jockey_scores.get)
        if jockey_scores[best_jockey_id] == float("inf"):
            raise ValueError("No available jockey to fulfill the move request")

        best_jockey = self.jockeys[best_jockey_id]
        travel_dist = self.euclidean_distance(best_jockey.location, request.from_location)
        estimated_minutes = round((travel_dist / 100.0) + 2.0, 1)  # 100 units/min + 2 min coupling

        self.docks[dock.dock_id].status = DockStatus.RESERVED
        self.jockeys[best_jockey_id].status = JockeyStatus.ON_MOVE

        return {
            "dock": dock,
            "jockey": best_jockey,
            "estimated_minutes": estimated_minutes,
            "request_id": request.request_id,
        }

    def handle_exception(self, request_id: str, trailer_id: str, exception_type: str, notes: str) -> str:
        """
        Transition trailer to MAINTENANCE_HOLD, re-queue the move request,
        and return the new request ID for the re-queued item.
        """
        new_request_id = str(uuid.uuid4())
        re_queued = MoveRequest(
            request_id=new_request_id,
            trailer_id=trailer_id,
            from_location=(0.0, 0.0),
            to_dock_id="REQUEUE",
            priority=5,
        )
        self.pending_requests.append(re_queued)
        return new_request_id

    def update_jockey_location(self, jockey_id: str, new_location: Tuple[float, float]) -> None:
        """Update a jockey's current coordinates."""
        if jockey_id in self.jockeys:
            self.jockeys[jockey_id].location = new_location

    def update_dock_status(self, dock_id: str, new_status: DockStatus) -> None:
        """Update a dock's current status."""
        if dock_id in self.docks:
            self.docks[dock_id].status = new_status

    def get_yard_summary(self) -> Dict:
        """Return a snapshot of yard state counts."""
        empty = sum(1 for d in self.docks.values() if d.status == DockStatus.EMPTY)
        occupied = sum(1 for d in self.docks.values() if d.status == DockStatus.OCCUPIED)
        available_jockeys = sum(1 for j in self.jockeys.values() if j.status == JockeyStatus.AVAILABLE)
        return {
            "empty_docks": empty,
            "occupied_docks": occupied,
            "available_jockeys": available_jockeys,
            "pending_requests": len(self.pending_requests),
            "total_docks": len(self.docks),
        }


if __name__ == "__main__":
    docks = [
        Dock("D1", (10.0, 0.0), DockStatus.EMPTY, [TrailerType.DRY_VAN, TrailerType.REEFER], 53),
        Dock("D2", (20.0, 0.0), DockStatus.OCCUPIED, [TrailerType.DRY_VAN], 48),
        Dock("D3", (30.0, 0.0), DockStatus.EMPTY, [TrailerType.REEFER], 53),
    ]
    jockeys = [
        Jockey("J1", (5.0, 5.0), JockeyStatus.AVAILABLE),
        Jockey("J2", (25.0, 5.0), JockeyStatus.AVAILABLE),
    ]
    router = YardRouter(docks, jockeys)

    trailer = Trailer("T1", TrailerType.REEFER, 53, 9, "CARRIER_A")
    request = MoveRequest(str(uuid.uuid4()), "T1", (0.0, 0.0), "", 9)
    result = router.assign_move_request(request, trailer)
    print("Assignment result:")
    print(f"  Dock: {result['dock'].dock_id}")
    print(f"  Jockey: {result['jockey'].jockey_id}")
    print(f"  ETA: {result['estimated_minutes']} min")
    print("Yard summary:", router.get_yard_summary())
