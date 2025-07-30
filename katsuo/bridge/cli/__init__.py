import click
import functools
import asyncio

from . import options

def async_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(func(*args, **kwargs))
    return wrapper

@click.group()
@click.version_option(package_name = 'katsuo-bridge')
@options.add_common
def main():
    pass

from . import csr

@main.command()
@options.bus_client
@async_command
async def capabilities(bus_client):
    capabilities = await bus_client.get_capabilities()
    print(capabilities)
