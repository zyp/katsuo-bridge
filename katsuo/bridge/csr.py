from amaranth import *
from amaranth.lib import wiring, stream

from amaranth_soc import csr

#from ..stream import

class Bridge(wiring.Component):
    input: wiring.In(stream.Signature(8))
    output: wiring.Out(stream.Signature(8))

    def __init__(self, bus: csr.Interface):
        super().__init__()

        assert isinstance(wiring.flipped(bus), csr.Interface)

        self._bus = bus

        assert bus.signature.data_width <= 8, 'Bus width > 8 bits not yet supported'

    def _send_status(self, m, next, status = 0x01):
        m.d.comb += [
            self.output.valid.eq(1),
            self.output.payload.eq(status),
        ]
        with m.If(self.output.ready):
            m.next = next

    def elaborate(self, platform):
        m = Module()

        cmd = Signal(8)

        is_read = Signal()

        buf = Signal(self._bus.signature.data_width)

        with m.FSM() as fsm:
            with m.State('CMD'):
                m.d.comb += self.input.ready.eq(1)

                with m.If(self.input.valid):
                    m.d.sync += cmd.eq(self.input.payload)
                    m.next = 'DECODE'
            
            with m.State('DECODE'):
                with m.Switch(cmd):
                    # No-op
                    with m.Case(0):
                        m.next = 'CMD'

                    # Read
                    with m.Case(0x40):
                        m.d.sync += is_read.eq(1)
                        self._send_status(m, 'ADDR_0')

                    # Write
                    with m.Case(0x80):
                        m.d.sync += is_read.eq(0)
                        self._send_status(m, 'ADDR_0')

                    # Query capabilities
                    with m.Case(0xc0):
                        self._send_status(m, 'CAPABILITIES_0')
                    
                    # Reserved
                    with m.Default():
                        self._send_status(m, 'CMD', 0xff)

            for i in range(0, self._bus.signature.addr_width, 8):
                with m.State(f'ADDR_{i}'):
                    m.d.comb += self.input.ready.eq(1)
                    with m.If(self.input.valid):
                        m.d.sync += self._bus.addr[i:i+8].eq(self.input.payload)
                        if i < len(self._bus.addr) - 8:
                            m.next = f'ADDR_{i+8}'
                        else:
                            with m.If(is_read):
                                m.next = 'READ'
                            with m.Else():
                                m.next = 'WRITE'

            with m.State('READ'):
                m.d.comb += self._bus.r_stb.eq(1)
                m.next = 'READ_CAPTURE'

            with m.State('READ_CAPTURE'):
                m.d.sync += buf.eq(self._bus.r_data)
                m.d.comb += [
                    self.output.valid.eq(1),
                    self.output.payload.eq(self._bus.r_data),
                ]
                with m.If(self.output.ready):
                    m.next = 'CMD'
                with m.Else():
                    m.next = 'READ_WAIT'

            with m.State('READ_WAIT'):
                m.d.comb += [
                    self.output.valid.eq(1),
                    self.output.payload.eq(buf),
                ]
                with m.If(self.output.ready):
                    m.next = 'CMD'

            with m.State('WRITE'):
                m.d.comb += self.input.ready.eq(1)
                with m.If(self.input.valid):
                    m.d.comb += [
                        self._bus.w_data.eq(self.input.payload),
                        self._bus.w_stb.eq(1),
                    ]
                    m.next = 'CMD'

            capabilities = [
                0x80 | 1, # 8b mode
                0x80 | 0,
                0x80 | self._bus.signature.addr_width,
                0x00 | self._bus.signature.data_width,
            ]

            for i, b in enumerate(capabilities):
                with m.State(f'CAPABILITIES_{i}'):
                    m.d.comb += [
                        self.output.valid.eq(1),
                        self.output.payload.eq(b),
                    ]

                    with m.If(self.output.ready):
                        m.next = f'CAPABILITIES_{i+1}' if i < len(capabilities) - 1 else 'CMD'

            with m.State('ERROR'):
                m.d.comb += [
                    self.output.valid.eq(1),
                    self.output.payload.eq(0xff),
                ]

                with m.If(self.output.ready):
                    m.next = 'CMD'

        return m
