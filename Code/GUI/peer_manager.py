"""Peer list and online/offline state management."""

from __future__ import annotations

from typing import Callable, Dict, Optional


class PeerManager:
    def __init__(self, on_change: Optional[Callable[[Dict[str, dict]], None]] = None):
        self.peers: Dict[str, dict] = {}
        self.on_change = on_change

    def upsert(self, info: dict) -> None:
        peer_id = info["peer_id"]
        current = self.peers.get(peer_id, {})
        current.update(info)
        self.peers[peer_id] = current
        self._notify()

    def set_status(self, peer_id: str, status: str, **extra) -> None:
        current = self.peers.get(peer_id, {"peer_id": peer_id})
        current.update(extra)
        current["status"] = status
        self.peers[peer_id] = current
        self._notify()

    def remove(self, peer_id: str) -> None:
        self.peers.pop(peer_id, None)
        self._notify()

    def online_peers(self):
        return [p for p in self.peers.values() if p.get("status") == "online"]

    def get(self, peer_id: str):
        return self.peers.get(peer_id)

    def _notify(self):
        if self.on_change:
            self.on_change(self.peers)
