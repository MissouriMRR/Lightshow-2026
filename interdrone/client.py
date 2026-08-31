import asyncio
import time
from asyncio.queues import Queue

from drone.json_parser import ConfigParser
from interdrone.json_message_utilities import JsonMessageUtilities
from interdrone.message_types import Message, MessageType


class ClientConnectionError(Exception):
    """Raised when the client cannot connect to or exchange data with a server."""


class Client:
    def __init__(
        self,
        jsonConfigData: ConfigParser,
        clientInData: Queue[Message],
        clientOutData: Queue[Message],
    ):
        self.jsonConfigData: ConfigParser = jsonConfigData
        self.clientInData: Queue[Message] = clientInData
        self.clientOutData: Queue[Message] = clientOutData

        self_id = jsonConfigData.get_self_id()
        if self_id is None:
            raise ValueError("config is missing localInfo.selfId")
        self.droneId: int = int(self_id)

        # Instantiate otherDrones lists
        self.otherDronesIps: list[str] = []
        self.otherDronesPorts: list[int] = []
        self.otherDronesIds: tuple[int, ...] = ()

        # Get actual IDs from JSON
        all_drone_ids = self.jsonConfigData.get_drone_ids()
        tempOtherDronesIds = []

        for droneId in all_drone_ids:
            # Skip self and GS (ID 0)
            if str(droneId) != str(self.droneId) and str(droneId) != "0":
                ip = self.jsonConfigData.get_drone_ip(drone_id=droneId)
                port = self.jsonConfigData.get_drone_port(drone_id=droneId)

                if ip and port:
                    self.otherDronesIps.append(ip)
                    self.otherDronesPorts.append(int(port))
                    tempOtherDronesIds.append(int(droneId))

        self.otherDronesIds = tuple(tempOtherDronesIds)

        # Ground station connection info
        self.gs_ip: str = self.jsonConfigData.get_gs_ip()
        gs_port = self.jsonConfigData.get_gs_port()
        if gs_port is None:
            raise ValueError("config is missing gs.port")
        self.gs_port: int = gs_port

    async def start_client_async(self):
        await self.client_loop()

    async def client_loop(self) -> None:
        clientMessageTasks: set[asyncio.Task[None]] = set()
        while True:
            while not self.clientInData.empty():
                message: Message = await self.clientInData.get()
                clientMessageTask = asyncio.create_task(self.handle_message(message))
                clientMessageTasks.add(clientMessageTask)
                clientMessageTask.add_done_callback(clientMessageTasks.discard)

            await asyncio.sleep(0.001)

    async def handle_message(self, message: Message):
        """Route message to correct destination(s)"""
        destinations = self._determine_destinations(message)

        if not destinations:
            return

        # Message preprocessing
        if message.id == MessageType.SPEED_TEST_REQUEST:
            message.data["initialUploadTime"] = time.perf_counter()

        clientMessageDump: str = JsonMessageUtilities.message_to_json(message=message)

        # Create tasks for all destinations
        messageTasks: list[asyncio.Task[str]] = []

        for _dest_type, dest_ip, dest_port in destinations:
            messageTask = asyncio.create_task(
                self.send_data_async(
                    serverIP=dest_ip,
                    serverPort=dest_port,
                    clientMessageDump=clientMessageDump,
                )
            )
            messageTasks.append(messageTask)

        # Run all tasks concurrently
        _ = await asyncio.gather(*messageTasks, return_exceptions=True)

    def _determine_destinations(self, message: Message) -> list[tuple[str, str, int]]:
        """
        Determine where message should be sent.
        Returns list of (dest_type, ip, port) tuples.
        """
        destinations: list[tuple[str, str, int]] = []

        # Check if message is for ground station (ID 0)
        if message.dronesToSendData == (0,):
            destinations.append(("gs", self.gs_ip, self.gs_port))

        # Check if message has specific drone destinations
        elif message.dronesToSendData != ():
            for target_id in message.dronesToSendData:
                ip, port = self._get_drone_connection(target_id)
                if ip and port:
                    destinations.append(("drone", ip, port))

        # Broadcast to all other drones AND ground station
        else:
            # Send to all other drones
            for i in range(len(self.otherDronesIds)):
                destinations.append(
                    (
                        "drone",
                        self.otherDronesIps[i],
                        self.otherDronesPorts[i],
                    )
                )

            # ALSO send to ground station for broadcasts
            destinations.append(("gs", self.gs_ip, self.gs_port))

        return destinations

    def _get_drone_connection(self, drone_id: int) -> tuple[str | None, int | None]:
        """Get IP and port for a specific drone"""
        try:
            idx = self.otherDronesIds.index(drone_id)
            return self.otherDronesIps[idx], self.otherDronesPorts[idx]
        except ValueError:
            return None, None

    async def send_data_async(
        self,
        serverIP: str,
        serverPort: int,
        clientMessageDump: str,
    ) -> str:
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(serverIP, serverPort), timeout=1.0
            )

            writer.write((clientMessageDump + "\n").encode())
            await writer.drain()

            serverResponseBytes = await asyncio.wait_for(
                reader.readuntil(b"\n"), timeout=2.0
            )
            serverResponseDump: str = serverResponseBytes.decode()

            writer.close()
            await writer.wait_closed()

            await self.process_client_data(
                clientMessageDump, serverResponseDump, serverIP, serverPort
            )

            return serverResponseBytes.decode()

        except TimeoutError as e:
            raise ClientConnectionError(
                f"Timeout connecting to {serverIP}:{serverPort}"
            ) from e
        except ConnectionRefusedError as e:
            raise ClientConnectionError(
                f"Connection refused by {serverIP}:{serverPort}"
            ) from e
        except Exception as e:
            raise ClientConnectionError(
                f"Error connecting to {serverIP}:{serverPort}: {e!s}"
            ) from e

    async def process_client_data(
        self,
        clientMessageDump: str,
        serverResponseDump: str,
        serverIP: str,
        serverPort: int,
    ) -> None:
        clientMessage: Message = JsonMessageUtilities.message_from_json(
            payload=clientMessageDump
        )
        serverResponse: Message = JsonMessageUtilities.message_from_json(
            payload=serverResponseDump
        )

        match serverResponse.id:
            case MessageType.SERVER_DEFAULT_RESPONSE:
                pass

            case MessageType.SPEED_TEST_REQUEST:
                receiveTime = time.perf_counter()
                serverProcessingTime: float = float(
                    serverResponse.data["initialDownloadTime"]
                ) - float(serverResponse.data["finalUploadTime"])
                totalRtt = receiveTime - clientMessage.data["initialUploadTime"]
                networkRtt = totalRtt - serverProcessingTime
                estimatedOneWayTime = networkRtt / 2

                uploadSizeBytes = len(clientMessageDump.encode("utf-8"))
                uploadThroughputKbps = (
                    (uploadSizeBytes * 8 / 1000) / estimatedOneWayTime
                    if estimatedOneWayTime > 0
                    else float("inf")
                )

                downloadSizeBytes = len(serverResponseDump)
                downloadThroughputKbps = (
                    (downloadSizeBytes * 8 / 1000) / estimatedOneWayTime
                    if estimatedOneWayTime > 0
                    else float("inf")
                )

                result: Message = Message.create(
                    id=MessageType.SPEED_TEST_RESPONSE,
                    dronesToSendData=(),
                    data={
                        "target": f"{serverIP}:{serverPort}",
                        "uploadRttMs": round(estimatedOneWayTime * 1000, 2),
                        "uploadThroughputKbps": round(uploadThroughputKbps, 2),
                        "downloadRttMs": round(estimatedOneWayTime * 1000, 2),
                        "downloadThroughputKbps": round(downloadThroughputKbps, 2),
                    },
                )
                await self.clientOutData.put(item=result)

            case _:
                await self.clientOutData.put(item=serverResponse)

    def run(self):
        asyncio.run(self.start_client_async())
