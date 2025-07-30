from amaranth.sim import Simulator, SimulatorContext

from katsuo.stream.sim import stream_put, stream_get

from .client import bridge

async def csr_bus_write(ctx: SimulatorContext, bus, addr, data):
    ctx.set(bus.addr, addr)
    ctx.set(bus.w_data, data)
    ctx.set(bus.w_stb, 1)

    await ctx.tick()

    ctx.set(bus.w_stb, 0)

async def csr_bus_read(ctx: SimulatorContext, bus, addr):
    ctx.set(bus.addr, addr)
    ctx.set(bus.r_stb, 1)

    #*_, data = await ctx.tick().sample(bus.r_data)
    await ctx.tick()
    ctx.set(bus.r_stb, 0)
    data = ctx.get(bus.r_data)

    return data

class SimBusClient:
    def __init__(self, ctx: SimulatorContext, bus):
        self._ctx = ctx
        self._bus = bus
    
    async def read_8b(self, addr: int, length: int = 1):
        assert length == 1 # TODO: Relax this

        return [await csr_bus_read(self._ctx, self._bus, addr)]

    async def write_8b(self, addr: int, data: bytes | list, *, increment = True):
        assert len(data) == 1

        await csr_bus_write(self._ctx, self._bus, addr, data[0])

def tb_with_bridge_client(sim: Simulator, dut, *, input_stream_fc = 0, output_stream_fc = 0):
    def wrapper(f):
        class Transport:
            def __init__(self):
                sim.add_testbench(self._input_testbench, background = True)
                sim.add_testbench(self._output_testbench)
                self.input_queue = []
            
            async def send(self, data: bytes):
                self.input_queue.extend(data)

            async def recv(self, n = 1):
                buf = bytearray()
                for _ in range(n):
                    if output_stream_fc:
                        await self.ctx.tick().repeat(output_stream_fc)
                    buf.append(await stream_get(self.ctx, dut.output))
                return buf
            
            async def _input_testbench(self, ctx: SimulatorContext):
                while True:
                    await ctx.tick()
                    if self.input_queue:
                        with ctx.critical():
                            while self.input_queue:
                                if input_stream_fc:
                                    await ctx.tick().repeat(input_stream_fc)
                                await stream_put(ctx, dut.input, self.input_queue.pop(0))

            async def _output_testbench(self, ctx: SimulatorContext):
                self.ctx = ctx
                await f(ctx, bridge.Client(self))

        transport = Transport()
    
    return wrapper
