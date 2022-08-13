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
        """
        self.logger = logger
        self.connections = dict()

    async def publish(self, device_from: Device, device_to_id: str, message: str) -> None:
        curr_user_id = str(device_from.user_id)
        if curr_user_id not in self.connections:
            return
        if device_to_id not in self.connections[curr_user_id]:
            return
        self.logger.debug("broker.publish\tGot valid publish request. Message: %r", message)
        await self.connections[curr_user_id][device_to_id].put(message)
        self.logger.debug("broker.publish\tAdded message to connections dict")

    async def subscribe(self, device: Device) -> AsyncGenerator[str, None]:
        connection = asyncio.Queue()
        curr_user_id = str(device.user_id)
        if curr_user_id not in self.connections:
            self.connections[curr_user_id] = dict()
        curr_device_id = str(device.id)
        self.connections[curr_user_id][curr_device_id] = connection
        self.logger.debug("broker.subscribe\tGot valid subscription request")
        try:
            while True:
                yield await connection.get()
        finally:
            self.logger.debug("broker.subscribe\tEnding subscription")
            self.connections[curr_user_id].pop(curr_device_id, None)
            self.logger.debug("broker.subscribe\tSubscription deleted")
