from dataclasses import dataclass

__all__ = ['Client']

@dataclass
class Capabilities:
    access_8b: bool = False
    access_16b: bool = False
    access_32b: bool = False
    access_64b: bool = False
    burst_nonincr: bool = False
    burst_incr: bool = False
    no_addr: bool = False
    burst_width: int = 0
    addr_width: int = 0
    data_width: int = 0

class Client:
    def __init__(self, transport):
        self.transport = transport
        self.capabilities = None

    async def read_8b(self, addr: int, length: int = 1):
        if self.capabilities is None:
            await self.get_capabilities()

        assert self.capabilities.access_8b
        assert length == 1 # TODO: Relax this

        addr_bytes = (self.capabilities.addr_width + 7) // 8

        await self.transport.send(bytes([0x40]) + addr.to_bytes(addr_bytes, 'little'))
        assert await self.transport.recv(1) == bytes([0x01])
        return list(await self.transport.recv(length))

    async def write_8b(self, addr: int, data: bytes | list, *, increment = True):
        if self.capabilities is None:
            await self.get_capabilities()

        assert self.capabilities.access_8b

        addr_bytes = (self.capabilities.addr_width + 7) // 8

        for b in data:
            await self.transport.send(bytes([0x80]) + addr.to_bytes(addr_bytes, 'little') + bytes([b]))
            assert await self.transport.recv(1) == bytes([0x01])
            if increment:
                addr += 1

    async def get_capabilities(self):
        await self.transport.send(bytes([0xc0]))
        assert await self.transport.recv(1) == bytes([0x01])
        buf = bytearray()
        while True:
            byte = await self.transport.recv(1)
            buf.extend(byte)
            if not byte[0] & 0x80:
                break

        capabilities = Capabilities()

        for i, b in enumerate(buf):
            match i:
                case 0:
                    capabilities.access_8b = bool(b & 0x01)
                    capabilities.access_16b = bool(b & 0x02)
                    capabilities.access_32b = bool(b & 0x04)
                    capabilities.access_64b = bool(b & 0x08)
                    capabilities.burst_nonincr = bool(b & 0x10)
                    capabilities.burst_incr = bool(b & 0x20)
                    capabilities.no_addr = bool(b & 0x40)
                case 1:
                    capabilities.burst_width = b & 0x7f
                case 2:
                    capabilities.addr_width = b & 0x7f
                case 3:
                    capabilities.data_width = b & 0x7f

        self.capabilities = capabilities
        return capabilities
