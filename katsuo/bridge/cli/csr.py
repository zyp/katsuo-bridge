from . import main, options, async_command

from ..client.csr import Register

import click

def print_recursive(element, level = 0):
    print(f'{' ' * level}{element.path[-1] if element.path else '*'}: ', end = '')
    match element:
        case Register():
            print('reg')
        case _:
            print()
            for child in element:
                print_recursive(child, level + 1)

@main.group()
def csr():
    pass

@csr.command()
@options.memory_map
def list(memory_map):
    """List CSR registers."""

    print_recursive(memory_map)

@csr.command()
@options.csr_bridge
@click.argument('register', type = str, required = True)
@async_command
async def read(csr_bridge, register):
    # Look up the register.
    node = csr_bridge
    for name in register.split('.'):
        node = node[name]
    
    if not isinstance(node, Register):
        raise click.UsageError(f'Invalid register: {register}')
    
    value = await node.read()
    print(f'{register}: {value:#x}')

@csr.command()
@options.csr_bridge
@click.argument('register', type = str, required = True)
@click.argument('value', type = int, required = True)
@async_command
async def write(csr_bridge, register, value):
    # Look up the register.
    node = csr_bridge
    for name in register.split('.'):
        node = node[name]
    
    if not isinstance(node, Register):
        raise click.UsageError(f'Invalid register: {register}')
    
    await node.write(value)
