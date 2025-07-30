import pytest

from amaranth.sim import Simulator, SimulatorContext

from amaranth import Module, Cat
from amaranth_soc.gpio import Peripheral as GpioPeripheral

from katsuo.bridge.sim import tb_with_bridge_client
from katsuo.bridge.csr import Bridge

@pytest.mark.parametrize(('addr_width', 'input_stream_fc', 'output_stream_fc'), [
    # Test 8 bit addressing with different flow control gaps.
    (8, 0, 0),
    (8, 1, 0),
    (8, 2, 0),
    (8, 0, 1),
    (8, 0, 2),
    (8, 1, 1),
    (8, 2, 2),
    # Ditto for 16-bit addressing.
    (16, 0, 0),
    (16, 1, 0),
    (16, 2, 0),
    (16, 0, 1),
    (16, 0, 2),
    (16, 1, 1),
    (16, 2, 2),
    # 6-bit and 12-bit addressing should be rounded up to 8-bit and 16-bit respectively.
    (6, 0, 0),
    (12, 0, 0),
])
def test_csr_bridge(addr_width, input_stream_fc, output_stream_fc):
    m = Module()

    m.submodules.gpio = gpio = GpioPeripheral(pin_count = 8, addr_width = addr_width, data_width = 8)
    m.submodules.bridge = bridge = Bridge(gpio.bus)

    gpio_i = Cat(pin.i for pin in gpio.pins)
    gpio_o = Cat(pin.o for pin in gpio.pins)
    gpio_oe = Cat(pin.oe for pin in gpio.pins)

    sim = Simulator(m)
    sim.add_clock(1e-6)

    @tb_with_bridge_client(sim, bridge, input_stream_fc = input_stream_fc, output_stream_fc = output_stream_fc)
    async def client_testbench(ctx: SimulatorContext, client):
        await ctx.tick()

        # Read bridge capabilities.
        capabilities = await client.get_capabilities()
        assert capabilities.access_8b == True
        assert capabilities.access_16b == False
        assert capabilities.access_32b == False
        assert capabilities.access_64b == False
        assert capabilities.burst_nonincr == False
        assert capabilities.burst_incr == False
        assert capabilities.no_addr == False
        assert capabilities.burst_width == 0
        assert capabilities.addr_width == addr_width
        assert capabilities.data_width == 8

        # Read GPIO input register
        assert await client.read_8b(0x02) == [0x00]

        ctx.set(gpio_i, 0x55)
        assert await client.read_8b(0x02) == [0x55]

        # Write GPIO output register
        await client.write_8b(0x03, [0xaa])
        await ctx.tick().repeat(10)
        assert ctx.get(gpio_o) == 0xaa

        # Set push-pull mode on GPIO pins 2..5
        await client.write_8b(0x00, [0x50, 0x05])
        await ctx.tick().repeat(10)
        assert ctx.get(gpio_oe) == 0x3c

    @sim.add_process
    async def timeout(ctx: SimulatorContext):
        await ctx.tick().repeat(10_000)
        raise TimeoutError('Simulation timed out')

    sim.run()
