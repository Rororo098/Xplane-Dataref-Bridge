from __future__ import annotations
import logging
from threading import Lock
from typing import Callable, Dict, List

log = logging.getLogger(__name__)


class DatarefBridge:
    """
    Routes X-Plane dataref updates to registered consumers.
    One writer (X-Plane), many readers (Arduino, HID, etc).
    """
    
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[float], None]]] = {}
        self._lock = Lock()
    
    def subscribe(self, dataref: str, callback: Callable[[float], None]) -> None:
        """Subscribe to updates for a specific dataref."""
        with self._lock:
            if dataref not in self._subscribers:
                self._subscribers[dataref] = []
            self._subscribers[dataref].append(callback)
        
        log.debug("Subscribed to dataref: %s", dataref)
    
    def unsubscribe(self, dataref: str, callback: Callable[[float], None] = None) -> None:
        """Unsubscribe from a dataref. If callback is None, remove all."""
        with self._lock:
            if dataref in self._subscribers:
                if callback is None:
                    del self._subscribers[dataref]
                else:
                    self._subscribers[dataref] = [
                        cb for cb in self._subscribers[dataref] if cb != callback
                    ]
    
    def publish(self, dataref: str, value: float) -> None:
        """Publish a dataref update to all subscribers."""
        with self._lock:
            callbacks = self._subscribers.get(dataref, []).copy()
        
        for callback in callbacks:
            try:
                callback(value)
            except Exception as e:
                log.error("Subscriber error for %s: %s", dataref, e)
    
    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._subscribers.clear()