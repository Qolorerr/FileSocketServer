import asyncio
import logging
from logging import Logger
from typing import AsyncGenerator

from qhelper.devices import Device


class Broker:
    def __init__(self) -> None:
        """
        connections = {
            user_id: {
                device_id: {
                    from_managed: Queue
                    to_managed: Queue
                }
            }
        }

        Every managed device has its own connection.
        Managing devices publish messages to connections of managed devices

        Managed device sends messages in from_managed and gets new messages from to_managed
        Managing device sends messages in to_managed and gets new messages from from_managed
        """
        self.logger = logging.getLogger("app")
        self.connections = dict()

    async def publish(self, device_from: Device, device_to_id: str, message: str, is_managed: bool) -> None:
        curr_user_id = str(device_from.user_id)
        if curr_user_id not in self.connections:
            return
        if device_to_id not in self.connections[curr_user_id]:
            return
        channel = "from_managed" if is_managed else "to_managed"
        if self.connections[curr_user_id][device_to_id][channel] is None:
            return
        await self.connections[curr_user_id][device_to_id][channel].put(message)
        self.logger.debug(f"Successfully published message, device_from: {device_from.type}{device_from.id}")

    async def subscribe(self, device_from: Device, device_to_id: str, is_managed: bool) -> AsyncGenerator[str, None]:
        connection = asyncio.Queue()
        user_id = str(device_from.user_id)
        if user_id not in self.connections:
            self.connections[user_id] = dict()
        if device_to_id not in self.connections[user_id]:
            self.connections[user_id][device_to_id] = {"from_managed": None, "to_managed": None}
        channel = "to_managed" if is_managed else "from_managed"
        self.connections[user_id][device_to_id][channel] = connection
        self.logger.debug(f"Successfully subscribed, "
                          f"device: {device_from.type}{device_from.id}, "
                          f"channel: {device_from.user_id}|{device_to_id}")
        try:
            while True:
                yield await connection.get()
        finally:
            if is_managed:
                self.connections[user_id].pop(device_to_id, None)
            self.logger.debug(f"Unsubscribed, "
                              f"device: {device_from.type}{device_from.id}, "
                              f"channel: {device_from.user_id}|{device_to_id}")
