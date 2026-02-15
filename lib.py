import socket
import time


def manchester_encode(frame: int, invert: bool = False) -> int:
    """
    Manchester encodes a 32 bit frame into a 64 bit integer.
    """

    if invert:
        one = 1
        zero = 2
    else:
        one = 2
        zero = 1

    mframe = 0
    mask = 0x80000000
    while mask:
        if frame & mask:
            mframe <<= 2
            mframe |= one
        else:
            mframe <<= 2
            mframe |= zero
        mask >>= 1

    return mframe


def manchester_decode(mframe: int, invert: bool = False) -> int:
    """
    Manchester decodes a 64 bit integer into a 32 bit frame.

    Will raise ValueError if decoding fails.
    """

    if invert:
        one = 0
        zero = 1
    else:
        one = 1
        zero = 0

    frame = 0
    mask = 0x8000000000000000
    mask2 = 0x4000000000000000
    for i in range(32):
        if mframe & mask:
            if mframe & mask2:
                send_syslog(f"ERROR: Manchester decoding error at bit {i}")
                raise ValueError("Manchester decoding error")
            frame <<= 1
            frame |= one

        else:
            if not (mframe & mask2):
                send_syslog(f"ERROR: Manchester decoding error at bit {i}")
                raise ValueError("Manchester decoding error")
            frame <<= 1
            frame |= zero
        mask >>= 2
        mask2 >>= 2

    return frame


def frame_encode(msg_type: int, data_id: int, data_value: int) -> int:
    """
    Encodes opentherm info into a 32 bit network ordered frame
    """

    frame = 0
    frame |= (msg_type & 0x07) << 28
    frame |= (data_id & 0xff) << 16
    frame |= (data_value & 0xffff)
    if bin(frame).count("1") & 1:  # parity bit
        frame |= 0x80000000
    return frame


def frame_decode(frame: int) -> tuple[int, int, int]:
    """
    Decodes a 32 bit frame into opentherm info.

    Will raise ValueError if parity bit is incorrect.
    """

    parity = bin(frame).count("1")
    if parity & 1:
        send_syslog(f"ERROR: Parity bit error, frame: {hex(frame)}")
        raise ValueError("Parity bit error")

    msg_type = (frame >> 28) & 0x07
    data_id = (frame >> 16) & 0xff
    data_value = frame & 0xffff
    return msg_type, data_id, data_value


def s8(x: int) -> int:
    return ((x & 0xff) ^ 0x80) - 0x80


def s16(x: int) -> int:
    return ((x & 0xffff) ^ 0x8000) - 0x8000


def f88(x: int) -> float:
    return s16(x) / 256


def send_syslog(message, port=514, hostname="picopower", appname="main", procid="-", msgid="-"):
    print(message)

    syslog_addr = ('255.255.255.255', port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    pri = 13  # user.notice
    version = 1
    # MicroPython uses time.localtime() instead of strftime
    t = time.localtime()
    # Format: YYYY-MM-DDTHH:MM:SS+00:00
    timestamp = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )
    syslog_msg = f"<{pri}>{version} {timestamp} {hostname} {appname} {procid} {msgid} - {message}\r\n".encode('utf-8')
    try:
        sock.sendto(syslog_msg, syslog_addr)
    except Exception as ex:
        print(f"Syslog send failed: {ex}")
    finally:
        sock.close()

