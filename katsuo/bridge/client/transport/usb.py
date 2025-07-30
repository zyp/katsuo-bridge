import nusb

class UsbTransport:
    def __init__(self):
        devices = [info for info in nusb.list_devices() if info.vendor_id == 0x1209 and info.product_id == 0x3443]
        assert len(devices) == 1
        info, = devices

        interfaces = [iface for iface in info.interfaces if iface.interface_string == 'katsuo.bridge']
        assert len(interfaces) == 1
        interface_info, = interfaces

        device = info.open()
        self._interface = device.claim_interface(interface_info.interface_number)
        self._in_ep = 0x81 # FIXME
        self._out_ep = 0x01 # FIXME
        self._rx_buffer = bytearray()

    async def send(self, data: bytes):
        await self._interface.bulk_out(self._out_ep, data)

    async def recv(self, length = 1):
        #return b'\0' * length
        while len(self._rx_buffer) < length:
            data = await self._interface.bulk_in(self._in_ep, 512)
            self._rx_buffer.extend(data)

        res, self._rx_buffer = self._rx_buffer[:length], self._rx_buffer[length:]
        return res
