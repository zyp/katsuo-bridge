from pyftdi.jtag import JtagEngine
from pyftdi.bits import BitSequence

ER1 = BitSequence(0x32, length = 8)
ER2 = BitSequence(0x38, length = 8)

_supported_idcodes = [
    # ECP5:
    0x21111043, # LFE5U-12
    0x41111043, # LFE5U-25
    0x41112043, # LFE5U-45
    0x41113043, # LFE5U-85
    0x01111043, # LFE5UM-25
    0x01112043, # LFE5UM-45
    0x01113043, # LFE5UM-85
    0x81111043, # LFE5UM5G-25
    0x81112043, # LFE5UM5G-45
    0x81113043, # LFE5UM5G-85

    # CertusPro-NX:
    0x010f2043, # LFCPNX-50
    0x010f4043, # LFCPNX-100
]

class FtdiJtagTransport:
    def __init__(self, url):
        self._jtag = JtagEngine(frequency = 1e6)
        self._jtag.configure(url)
        self._jtag.reset()

        idcode = int(self._jtag.read_dr(32))
        assert idcode in _supported_idcodes, f'Unsupported IDCODE: {idcode:08x}'

        self._jtag.write_ir(ER1)
        self._jtag.change_state('shift_dr')

        self._read_buf = BitSequence()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._jtag.go_idle()
        self._jtag.sync()

    def read(self, length):
        buf = bytearray()
        while length:
            # Remove leading zeros.
            for i, b in enumerate(self._read_buf):
                if b:
                    before = len(self._read_buf)
                    self._read_buf = self._read_buf[i:]
                    assert len(self._read_buf) == before - i
                    break
            else:
                self._read_buf = BitSequence()

            # Take a byte from the buffer.
            if len(self._read_buf) >= 9:
                assert self._read_buf[0] == 1
                buf.append(int(self._read_buf[1:9]))
                self._read_buf = self._read_buf[9:]
                length -= 1
                continue

            # Read more if required.
            if len(self._read_buf) < length * 9:
                self._read_buf.append(self._jtag.shift_register(BitSequence(0, length = length * 9 - len(self._read_buf))))
                continue

        return buf

    def write(self, data):
        buf = BitSequence()
        for b in data:
            buf.append(BitSequence(1, length = 1))
            buf.append(BitSequence(b, length = 8))

        buf.append(BitSequence(0, length = 20))

        self._read_buf.append(self._jtag.shift_register(buf))

    async def send(self, data: bytes):
        self.write(data)

    async def recv(self, length = 1):
        return self.read(length)

#def main():
#    with JtagBridge() as jtag:
#        buf = jtag.read(3)
#        print(buf.hex(' '))
#
#        buf = jtag.write(bytes([0x80]))
#
#        buf = jtag.read(16)
#        print(buf.hex(' '))
#
#if __name__ == '__main__':
#    main()
