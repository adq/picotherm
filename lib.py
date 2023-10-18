
def manchester_encode(frame: int) -> int:
    """
    Manchester encodes a 32 bit frame into a 64 bit integer.
    """

    mframe = 0
    mask = 0x80000000
    while mask:
        if frame & mask:
            mframe <<= 2
            mframe |= 2
        else:
            mframe <<= 2
            mframe |= 1
        mask >>= 1

    return mframe


def manchester_decode(mframe: int) -> int:
    """
    Manchester decodes a 64 bit integer into a 32 bit frame.

    Will raise ValueError if decoding fails.
    """

    frame = 0
    mask = 0x8000000000000000
    mask2 = 0x4000000000000000
    for i in range(32):
        if mframe & mask:
            if mframe & mask2:
                raise ValueError("Manchester decoding error")
            frame <<= 1
            frame |= 1

        else:
            if not (mframe & mask2):
                raise ValueError("Manchester decoding error")
            frame <<= 1
            frame |= 0
        mask >>= 2
        mask2 >>= 2

    return frame


def frame_encode(msg_type: int, data_id: int, data_value: int) -> int:
    """
    Encodes opentherm info into a 32 bit frame
    """

    frame = 0
    frame |= (msg_type & 0x07) << 1
    frame |= (data_id & 0xff) << 8
    frame |= (data_value & 0xffff) << 16
    frame |= (bin(frame).count("1") & 1) # parity bit
    return frame


def frame_decode(frame: int) -> tuple[int, int, int]:
    """
    Decodes a 32 bit frame into opentherm info.

    Will raise ValueError if parity bit is incorrect.
    """

    parity = bin(frame).count("1")
    if parity & 1:
        raise ValueError("Parity bit error")

    msg_type = (frame >> 1) & 0x07
    data_id = (frame >> 8) & 0xff
    data_value = (frame >> 16) & 0xffff
    return msg_type, data_id, data_value
