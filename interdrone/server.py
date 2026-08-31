import asyncio
import time
from asyncio import StreamReader, StreamWriter
from asyncio.queues import Queue

from drone.json_parser import ConfigParser
from interdrone.json_message_utilities import JsonMessageUtilities
from interdrone.message_types import Message, MessageType


class Server:
    def __init__(
        self,
        jsonConfigData: ConfigParser,
        serverOutData: Queue[Message],
    ):
        self.jsonConfigData: ConfigParser = jsonConfigData
        self.serverOutData: Queue[Message] = serverOutData
        self_id = jsonConfigData.get_self_id()
        if self_id is None:
            raise ValueError("config is missing localInfo.selfId")
        self.droneId: int = int(self_id)

        # Track active connections to other drones for routing
        self.drone_connections: dict[int, tuple[StreamReader, StreamWriter]] = {}

        self.serverDefaultResponseMessage: Message = Message.create(
            id=MessageType.SERVER_DEFAULT_RESPONSE,
            dronesToSendData=(),
            data={
                "payload": "Server received your message!",
            },
        )

    async def start_server_async(self):
        port = self.jsonConfigData.get_drone_port(str(self.droneId))
        if port is None:
            raise ValueError(f"Drone {self.droneId} port not configured")

        server = await asyncio.start_server(
            self.handle_client,
            "0.0.0.0",
            port,  # Now guaranteed to be int
        )

        try:
            async with server:
                port = self.jsonConfigData.get_drone_port(str(self.droneId))
                print(f"[Drone {self.droneId}] Server listening on 0.0.0.0:{port}")
                await server.serve_forever()
        except KeyboardInterrupt:
            print("Server shutting down.")
        finally:
            server.close()
            await server.wait_closed()

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        try:
            byteMessage = await reader.readuntil(b"\n")
            message: Message = JsonMessageUtilities.message_from_json(
                byteMessage.decode()
            )

            if message:
                # Determine response based on message type
                responseMessage: Message = await self.process_message(message)

                # Send response back to sender
                writer.write(
                    (
                        JsonMessageUtilities.message_to_json(responseMessage) + "\n"
                    ).encode()
                )
                await writer.drain()

        except TimeoutError:
            print("Client timeout - no data received")
        except asyncio.IncompleteReadError:
            print("Client disconnected before sending complete message")
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def process_message(self, message: Message) -> Message:
        """
        Process incoming message and determine appropriate response.
        Routes messages to correct destination and handles confirmations.
        """
        responseMessage = self.serverDefaultResponseMessage

        match message.id:
            # Heartbeat - just forward to app
            case MessageType.HEARTBEAT:
                await self.serverOutData.put(item=message)

            # Incoming commands - forward to command handler
            case (
                MessageType.TAKEOFF
                | MessageType.FRAME_STEP
                | MessageType.LAND
                | MessageType.HALT
                | MessageType.POLL_DRONE
                | MessageType.EMERGENCY_HALT
                | MessageType.ARM
            ):
                await self.serverOutData.put(item=message)

            # Command confirmations/responses - forward to ground station
            case (
                MessageType.TAKEOFF_CONFIRMATION
                | MessageType.FRAME_STEP_CONFIRMATION
                | MessageType.HALT_CONFIRMATION
                | MessageType.LAND_CONFIRMATION
                | MessageType.ARM_RESPONSE
            ):
                await self.serverOutData.put(item=message)

            # Poll response - forward to requester
            case MessageType.POLL_DRONE_RESPONSE:
                await self.serverOutData.put(item=message)

            # Ping messages - forward to app for handling
            case MessageType.PING | MessageType.PING_RESPONSE:
                await self.serverOutData.put(item=message)

            # GS test messages
            case MessageType.GS_TEST:
                await self.serverOutData.put(item=message)

            # Speed test - measure timing
            case MessageType.SPEED_TEST_REQUEST:
                message.data["finalUploadTime"] = time.perf_counter()
                message.data["initialDownloadTime"] = time.perf_counter()
                responseMessage = message

            case _:
                pass

        return responseMessage

    def run(self):
        asyncio.run(self.start_server_async())
