
class Signal(object):
    r"""
    Represents a signl belonging to a :class:`Frame <dbcparser.Frame>`.

    .. doctest::

        # Load demo dbc content
        >>> import dbcparser
        >>> dbc = dbcparser.loads()
        >>> dbc = dbcparser.loads(dbcparser.parser.demo_content)

        # Get a signal from a frame
        >>> sig = dbc.frames['abc'].signal['xyz']
        >>> sig.name
        'xyz'
        >>> sig.frame
        <Frame: CAN1:abc 0x123>
        >>> (sig.factor, sig.offset)
        (1.0, 0.0)
        >>> sig.signed
        False
        >>> (sig.min, sig.max)
        (0, 255)
        >>> (sig.startbit, sig.length)
        (0, 8)

        # Masking
        >>> sig.frame.dlc
        4
        >>> sig.mask
        [255, 0, 0, 0]

        # Setting Value
        >>> sig.value
        0
        >>> sig.set_from_data([1, 2, 3, 4])

    :param name: signal name
    :type name: :class:`str`
    :param startbit: first bit of signal (0-63)
    :type startbit: :class:`int`
    :param length: number of bits in signal
    :type length: :class:`int`
    :param little_endian: if ``True``, signal's data is little endian
    :type little_endian: :class:`bool`
    :param signed: if ``True``, signal is signed
    :type signed: :class:`bool`
    :param factor: signal factor (see conversion below)
    :type factor: :class:`float`
    :param offset: signal offset (see conversion below)
    :type offset: :class:`float`
    :param minimum: minimum value (in ``unit``)
    :type minimum: :class:`float`
    :param maximum: maximum value (in ``unit``)
    :type maximum: :class:`float`
    :param unit: signal unit
    :type unit: :class:`str`
    :param receivers: list of receiving nodes
    :type receivers: :class:`list` of :class:`Node <dbcparser.Node>`
    :param frame: container frame
    :type frame: :class:`Frme <dbcparser.Frame>`

    **Value Conversion**

    Values are transmitted as fixed-point:

    .. math::

        phys = (raw \times factor) + offset

        raw = \frac{phys - offset}{factor}

    *where:*

    - :math:`raw` : value transmitted (as :class:`int`)
    - :math:`phys` : scaled & offset value in the signal's ``unit`` (as :class:`float`)
    """
    def __init__(self, name, startbit, length,
                 little_endian, signed,
                 factor, offset, minimum, maximum, unit,
                 receivers=[], frame=None):
        self.name = name
        self.startbit = startbit
        self.length = length
        self.little_endian = little_endian
        self.signed = signed
        self.factor = factor
        self.offset = offset
        self.minimum = minimum
        self.maximum = maximum
        self.unit = unit
        self.receivers = receivers
        self.frame = frame
