import asyncio
from logging import Logger
from typing import AsyncGenerator

from qhelper.devices import Device


class Broker:
    def __init__(self, logger: Logger) -> None:
        """
        connections = {
            user_id: {
                device_id: connection
            }
        }

        Every managed device has its own connection.
        Managing devices publish messages to connections of managed devices
        """
        self.logger = logger
        self.connections = dict()

    async def publish(self, device_from: Device, device_to_id: str, message: str) -> None:
        curr_user_id = str(device_from.user_id)
        if curr_user_id not in self.connections:
            return
        if device_to_id not in self.connections[curr_user_id]:
            return
        await self.connections[curr_user_id][device_to_id].put(message)
        self.logger.debug(f"Successfully published message, device_from: {device_from.type}{device_from.id}")

    async def subscribe(self, device_from: Device, device_to_id: str) -> AsyncGenerator[str, None]:
        connection = asyncio.Queue()
        user_id = str(device_from.user_id)
        if user_id not in self.connections:
            self.connections[user_id] = dict()
        self.connections[user_id][device_to_id] = connection
        self.logger.debug(f"Successfully subscribed, "
                          f"device: {device_from.type}{device_from.id}, "
                          f"channel: {device_from.user_id}|{device_to_id}")
        try:
            while True:
                yield await connection.get()
        finally:
            if str(device_from.id) == device_to_id:
                self.connections[user_id].pop(device_to_id, None)
            self.logger.debug(f"Unsubscribed, "
                              f"device: {device_from.type}{device_from.id}, "
                              f"channel: {device_from.user_id}|{device_to_id}")
