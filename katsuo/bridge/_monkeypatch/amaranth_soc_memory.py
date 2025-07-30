from amaranth.lib import meta

from amaranth_soc.memory import MemoryMap

#@property
#def annotation(self):
#    return MemoryMapAnnotation(self)
#
#MemoryMap.annotation = annotation

def annotations(self):
    annotations = [MemoryMapAnnotation(self)]
    if hasattr(self, '_annotations'):
        annotations.extend(self._annotations)
    return annotations

MemoryMap.annotations = annotations

def add_annotation(self, annotation):
    #assert not self._frozen # Ideally we should have this check, but when constructed from a csr.Builder, the memory map is frozen before we get a chance to call this method.
    if not hasattr(self, '_annotations'):
        self._annotations = []
    self._annotations.append(annotation)

MemoryMap.add_annotation = add_annotation

class MemoryMapAnnotation(meta.Annotation):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://amaranth-lang.org/schema/amaranth-soc/0.1/memory/memory-map.json",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
            },
            "addr_width": {
                "type": "integer",
                "minimum": 0,
            },
            "data_width": {
                "type": "integer",
                "minimum": 0,
            },
            "alignment": {
                "type": "integer",
                "minimum": 0,
            },
            "windows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                        },
                        "start": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "end": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "ratio": {
                            "type": "integer",
                            "minimum": 1,
                        },
                        "annotations": {
                            "type": "object",
                            "patternProperties": {
                                "^.+$": { "$ref": "#" },
                            },
                        },
                    },
                    "additionalProperties": False,
                    "required": [
                        "start",
                        "end",
                        "ratio",
                        "annotations",
                    ],
                },
            },
            "resources": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "array",
                            "items": {
                                "type": "string",
                            },
                        },
                        "start": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "end": {
                            "type": "integer",
                            "minimum": 0,
                        },
                        "annotations": {
                            "type": "object",
                            "patternProperties": {
                                "^.+$": { "type": "object" },
                            },
                        },
                    },
                    "additionalProperties": False,
                    "required": [
                        "name",
                        "start",
                        "end",
                        "annotations",
                    ],
                },
            },
        },
        "additionalProperties": False,
        "required": [
            "addr_width",
            "data_width",
            "alignment",
            "windows",
            "resources",
        ],
    }

    """Memory map annotation.

    Parameters
    ----------
    origin : :class:`MemoryMap`
        The memory map described by this annotation instance. It is frozen as a side-effect of
        this instantiation.

    Raises
    ------
    :exc:`TypeError`
        If ``origin`` is not a :class:`MemoryMap`.
    """
    def __init__(self, origin):
        if not isinstance(origin, MemoryMap):
            raise TypeError(f"Origin must be a MemoryMap object, not {origin!r}")
        origin.freeze()
        self._origin = origin

    @property
    def origin(self):
        return self._origin

    def as_json(self):
        """Translate to JSON.

        Returns
        -------
        :class:`dict`
            A JSON representation of :attr:`~MemoryMapAnnotation.origin`, describing its address width,
            data width, address range alignment, and a hierarchical description of its local windows
            and resources.
        """
        instance = {}
        instance.update({
            "addr_width": self.origin.addr_width,
            "data_width": self.origin.data_width,
            "alignment": self.origin.alignment,
            "windows": [
                {
                    "name": window_name,
                    "start": start,
                    "end": end,
                    "ratio": ratio,
                    "annotations": {
                        #window.annotation.schema["$id"]: window.annotation.as_json()
                        annotation.schema["$id"]: annotation.as_json()
                        for annotation in window.annotations()
                    },
                } for window, window_name, (start, end, ratio) in self.origin.windows()
            ],
            "resources": [
                {
                    "name": name,
                    "start": start,
                    "end": end,
                    "annotations": {
                        annotation.schema["$id"]: annotation.as_json()
                        for annotation in resource.signature.annotations(resource)
                    },
                } for resource, name, (start, end) in self.origin.resources()
            ],
        })
        self.validate(instance)
        return instance
