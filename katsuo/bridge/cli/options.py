import click
import functools
import pathlib
import json

from ..client.transport import open_url
from ..client import bridge, csr

def add_common(func):
    @click.option('-t', '--transport', type = str)
    @click.option('-m', '--metadata', type = click.Path(exists = True, dir_okay = False, path_type = pathlib.Path))
    @click.pass_context
    @functools.wraps(func)
    def wrapper(ctx, transport, metadata, **kwargs):
        class Common:
            @functools.cached_property
            def transport(self):
                if transport is None:
                    raise click.UsageError('No transport provided.')

                return open_url(transport)

            @functools.cached_property
            def bus_client(self):
                return bridge.Client(self.transport)

            @functools.cached_property
            def annotations(self):
                if metadata is None:
                    raise click.UsageError('No metadata file provided.')

                with metadata.open('r') as f:
                    data = json.load(f)
                return data['interface']['members']['bus']['annotations']

            @functools.cached_property
            def memory_map(self):
                return csr.MemoryMap(self.annotations)

            @functools.cached_property
            def csr_bridge(self):
                return csr.Client(self.annotations, bus_client = self.bus_client)

        ctx.obj = Common()

        ctx.invoke(func, **kwargs)

    return wrapper

def bus_client(func):
    @click.pass_context
    @functools.wraps(func)
    def wrapper(ctx, **kwargs):
        return ctx.invoke(func, bus_client = ctx.obj.bus_client, **kwargs)

    return wrapper

def memory_map(func):
    @click.pass_context
    @functools.wraps(func)
    def wrapper(ctx, **kwargs):
        return ctx.invoke(func, memory_map = ctx.obj.memory_map, **kwargs)

    return wrapper

def csr_bridge(func):
    @click.pass_context
    @functools.wraps(func)
    def wrapper(ctx, **kwargs):
        return ctx.invoke(func, csr_bridge = ctx.obj.csr_bridge, **kwargs)

    return wrapper
