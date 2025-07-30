class Register:
    def __init__(self, offset, *, client = None, path):
        self._offset = offset
        self._client = client
        self.width = 8
        self.path = path
    
    async def read(self):
        return await self._client.read(self._offset)
    
    async def write(self, value):
        await self._client.write(self._offset, value)

class _PartialName:
    def __init__(self, parent, name, path):
        self._parent = parent
        self._name = name
        self.path = path

    def __iter__(self):
        return self._parent._iter_prefix(self._name)

    def __getitem__(self, name):
        if isinstance(name, int):
            name = str(name)
        if not isinstance(name, tuple):
            name = (name,)
        
        return self._parent[*self._name, *name]

    def __getattr__(self, name):
        return self[name]

class MemoryMap:
    __schema = 'https://amaranth-lang.org/schema/amaranth-soc/0.1/memory/memory-map.json'

    def __init__(self, annotations, *, offset = 0, client = None, path = ()):
        assert self.__schema in annotations

        self.annotations = annotations
        self._offset = offset
        self._client = client
        self.path = path

    def _iter_prefix(self, prefix = ()):
        emitted = set()
        for window in self.annotations[self.__schema]['windows']:
            window_name = tuple(window['name'])
            if not window_name[:len(prefix)] == prefix:
                continue
            name = window_name[len(prefix)]
            if name not in emitted:
                emitted.add(name)
                yield self[name]
        for resource in self.annotations[self.__schema]['resources']:
            resource_name = tuple(resource['name'])
            if not resource_name[:len(prefix)] == prefix:
                continue
            name = resource_name[len(prefix)]
            if name not in emitted:
                emitted.add(name)
                yield self[name]

    def __iter__(self):
        return self._iter_prefix()

    def __getitem__(self, name):
        if isinstance(name, int):
            name = str(name)
        if not isinstance(name, tuple):
            name = (name,)
        
        for window in self.annotations[self.__schema]['windows']:
            window_name = tuple(window['name'])
            if name == window_name:
                assert window['ratio'] == 1
                offset = self._offset + window['start']
                return MemoryMap(window['annotations'], offset = offset, client = self._client, path = self.path + name)
            elif name == window_name[:len(name)]:
                return _PartialName(self, name, path = self.path + name)

        for resource in self.annotations[self.__schema]['resources']:
            resource_name = tuple(resource['name'])
            if name == resource_name:
                offset = self._offset + resource['start']
                return Register(offset = offset, client = self._client, path = self.path + name)
            elif name == resource_name[:len(name)]:
                return _PartialName(self, name, path = self.path + name)

    def __getattr__(self, name):
        return self[name]

class Client(MemoryMap):
    __schema = 'https://amaranth-lang.org/schema/amaranth-soc/0.1/csr/bus.json'

    def __init__(self, annotations, *, bus_client):
        assert self.__schema in annotations

        self._addr_width = annotations[self.__schema]['addr_width']
        self._data_width = annotations[self.__schema]['data_width']

        assert self._data_width == 8

        self._bus_client = bus_client

        super().__init__(annotations, client = self)
    
    async def read(self, addr):
        buf = await self._bus_client.read_8b(addr)
        return buf[0]

    async def write(self, addr, value):
        await self._bus_client.write_8b(addr, [value])
