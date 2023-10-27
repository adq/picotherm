import machine
import rp2
import time
from lib import manchester_encode, frame_encode, manchester_decode, frame_decode


# opentherm tx - transmit pre-manchester-encoded-bits. Automatically sends start and stop bits.
@rp2.asm_pio(autopush=True, set_init=rp2.PIO.OUT_HIGH, out_init=rp2.PIO.OUT_HIGH, autopull=True, out_shiftdir=rp2.PIO.SHIFT_LEFT)
def opentherm_tx():
    # counter for bit writing loop
    set(x, 31)

    # write start bit
    set(pins, 0)
    nop()
    set(pins, 1)
    nop()

    # write the manchester encoded data
    label("write_bits")
    out(pins, 1)
    nop()
    out(pins, 1)
    jmp(x_dec, "write_bits")

    # write stop bit
    set(pins, 0)
    nop()
    set(pins, 1)
    nop()

    # indicate that we're done!
    in_(x, 32)
    label("loop")
    jmp("loop")

sm_opentherm_tx = rp2.StateMachine(0, opentherm_tx, freq=4000, set_base=machine.Pin(0), out_base=machine.Pin(0)) # each tick is 250uS


# opentherm rx - receive manchester-encoded-bits, waiting for initial start bit
@rp2.asm_pio(autopush=True, in_shiftdir=rp2.PIO.SHIFT_RIGHT)
def opentherm_rx():
    # wait for start bit
    wait(1, pin, 0)
    wait(0, pin, 0)

    # kick off initial bit read
    set(x, 14)  # 13 loops, 3 ticks per loop, 60kHz == 650uS
    jmp("wait_for_bit_currently_0")

    # read the current bit from the GPIO
    label("read_next_bit")
    in_(pins, 1)
    set(x, 14)  # 13 loops, 3 ticks per loop, 60kHz == 650uS
    jmp(pin, "wait_for_bit_currently_1")

    # wait for a bit change from 0->1 or timeout
    label("wait_for_bit_currently_0")
    nop()
    jmp(pin, "read_next_bit")
    jmp(x_dec, "wait_for_bit_currently_0")
    jmp("read_next_bit")

    # wait for a bit change from 1->0 or timeout
    label("wait_for_bit_currently_1")
    jmp(pin, "was_still_1")
    jmp("read_next_bit")
    label("was_still_1")
    jmp(x_dec, "wait_for_bit_currently_1")
    jmp("read_next_bit")

sm_opentherm_rx = rp2.StateMachine(4, opentherm_rx, freq=60000, in_base=machine.Pin(1), jmp_pin=machine.Pin(1)) # each tick is 17uS


def opentherm_exchange(msg_type: int, data_id: int, data_value: int, timeout_ms: int = 1000, debug: bool=True) -> tuple[int, int, int]:
    f = frame_encode(msg_type, data_id, data_value)
    m = manchester_encode(f, invert=True)
    if debug:
        print(f"> {f:08x} {m:064b}")

    # setup pio
    sm_opentherm_tx.active(0)
    sm_opentherm_rx.active(0)
    while sm_opentherm_rx.rx_fifo():
        sm_opentherm_rx.get()

    # send the data using the transmitter pio
    sm_opentherm_tx.put(int(m) >> 32)
    sm_opentherm_tx.put(int(m))
    sm_opentherm_tx.restart()
    sm_opentherm_tx.active(1)
    sm_opentherm_tx.get()
    # time.sleep_ms(40)  # FIXME: wait for the above to finish somehow
    sm_opentherm_tx.active(0)

    # wait for response
    sm_opentherm_rx.restart()
    sm_opentherm_rx.active(1)
    timeout = time.ticks_ms() + timeout_ms
    while sm_opentherm_rx.rx_fifo() < 2 and time.ticks_ms() < timeout:
        time.sleep_ms(50)
    sm_opentherm_rx.active(0)

    # check we didn't time out
    if sm_opentherm_rx.rx_fifo() < 2:
        raise Exception("Timeout waiting for response")

    # decode it
    a = sm_opentherm_rx.get()
    b = sm_opentherm_rx.get()
    m2 = (a << 32) | b
    f2 = manchester_decode(m2)
    if debug:
        print(f"< {f2:08x} {m2:064b}")
    return frame_decode(f2)
