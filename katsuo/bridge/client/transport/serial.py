from serial_asyncio_fast import open_serial_connection

class Transport:
    def __init__(self, port):
        self.port = port
        self.reader, self.writer = None, None

    async def open(self):
        self.reader, self.writer = await open_serial_connection(url = self.port)

    async def send(self, data: bytes):
        if self.writer is None:
            await self.open()

        self.writer.write(data)

    async def recv(self, length = 1):
        if self.reader is None:
            await self.open()

        return await self.reader.readexactly(length)
