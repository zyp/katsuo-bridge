from amaranth.lib import meta, wiring

from amaranth_soc.csr.bus import Interface, Signature, Element

def annotations(self, interface, /):
    """Get annotations of a compatible CSR bus interface.

    Parameters
    ----------
    interface : :class:`Interface`
        A CSR bus interface compatible with this signature.

    Returns
    -------
    iterator of :class:`meta.Annotation`
        Annotations attached to ``interface``.

    Raises
    ------
    :exc:`TypeError`
        If ``interface`` is not an :class:`Interface` object.
    :exc:`ValueError`
        If ``interface.signature`` is not equal to ``self``.
    """
    if isinstance(interface, wiring.FlippedInterface):
        interface = wiring.flipped(interface)
    if not isinstance(interface, Interface):
        raise TypeError(f"Interface must be a csr.Interface object, not {interface!r}")
    if interface.signature != self:
        raise ValueError(f"Interface signature is not equal to this signature")
    annotations = [Annotation(interface.signature)]
    if interface._memory_map is not None:
        annotations.extend(interface._memory_map.annotations())
    return annotations

Signature.annotations = annotations

class Annotation(meta.Annotation):
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://amaranth-lang.org/schema/amaranth-soc/0.1/csr/bus.json",
        "type": "object",
        "properties": {
            "addr_width": {
                "type": "integer",
                "minimum": 0,
            },
            "data_width": {
                "type": "integer",
                "minimum": 0,
            },
        },
        "additionalProperties": False,
        "required": [
            "addr_width",
            "data_width",
        ],
    }

    """CPU-side CSR signature annotation.

    Parameters
    ----------
    origin : :class:`Signature`
        The signature described by this annotation instance.

    Raises
    ------
    :exc:`TypeError`
        If ``origin`` is not a :class:`Signature`.
    """
    def __init__(self, origin):
        if not isinstance(origin, Signature):
            raise TypeError(f"Origin must be a csr.Signature object, not {origin!r}")
        self._origin = origin

    @property
    def origin(self):
        return self._origin

    def as_json(self):
        """Translate to JSON.

        Returns
        -------
        :class:`dict`
            A JSON representation of :attr:`~Annotation.origin`, describing its address width
            and data width.
        """
        instance = {
            "addr_width": self.origin.addr_width,
            "data_width": self.origin.data_width,
        }
        self.validate(instance)
        return instance

def element_annotations(self, element, /):
    """Get annotations of a compatible CSR element.

    Parameters
    ----------
    element : :class:`Element`
        A CSR element compatible with this signature.

    Returns
    -------
    iterator of :class:`meta.Annotation`
        Annotations attached to ``element``.

    Raises
    ------
    :exc:`TypeError`
        If ``element`` is not an :class:`Element` object.
    :exc:`ValueError`
        If ``element.signature`` is not equal to ``self``.
    """
    if not isinstance(element, Element):
        raise TypeError(f"Element must be a csr.Element object, not {element!r}")
    if element.signature != self:
        raise ValueError(f"Element signature is not equal to this signature")
    return (ElementAnnotation(element.signature))
