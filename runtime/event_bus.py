# -*- coding: utf-8 -*-
"""
Event Bus Module.
Facilitates asynchronous messaging and state updates between agents.
"""
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EventBus")

class EventBus:
    def __init__(self):
        self.listeners = defaultdict(list)

    def subscribe(self, event_type: str, callback) -> None:
        """
        Subscribes a listener to a specific event type.
        """
        logger.info(f"Subscribing to event: {event_type}")
        self.listeners[event_type].append(callback)

    def publish(self, event_type: str, data: dict) -> None:
        """
        Publishes event data to all subscribed listeners.
        """
        logger.info(f"Publishing event: {event_type}")
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event callback: {str(e)}")
