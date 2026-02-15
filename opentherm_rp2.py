import machine
import rp2
import time
from lib import manchester_encode, frame_encode, manchester_decode, frame_decode
import asyncio


# PIO Program Configuration
# These constants are exported for testing and documentation
PIO_TX_FREQ = 4000  # 4kHz -> 250µs per tick -> 500µs per Manchester bit
PIO_RX_FREQ = 60000  # 60kHz -> 16.67µs per tick -> ~700µs timeout
PIO_RX_TIMEOUT_LOOPS = 14  # Number of loops before timeout


# opentherm tx - transmit pre-manchester-encoded-bits. Automatically sends start and stop bits.
# note that the hardware is inverted for transmission - HIGH = 0, LOW = 1
#
# PIO Configuration:
# - autopush=True: Automatically push ISR to FIFO when full
# - set_init=OUT_HIGH, out_init=OUT_HIGH: Initialize pins HIGH (inverted LOW)
# - autopull=True: Automatically pull from FIFO to OSR when empty
# - out_shiftdir=SHIFT_LEFT: Shift OSR left (MSB first)
# - freq=4000: 250µs per tick, 500µs per Manchester bit
@rp2.asm_pio(autopush=True, set_init=rp2.PIO.OUT_HIGH, out_init=rp2.PIO.OUT_HIGH, autopull=True, out_shiftdir=rp2.PIO.SHIFT_LEFT)
def opentherm_tx():
    # counter for bit writing loop
    set(x, 31)

    # write start bit (hardware bits are inverted!)
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

    # write stop bit (hardware bits are inverted!)
    set(pins, 0)
    nop()
    set(pins, 1)
    nop()

    # indicate that we're done!
    in_(x, 32)
    label("loop")
    jmp("loop")


# opentherm rx - receive manchester-encoded-bits, waiting for initial start bit
#
# PIO Configuration:
# - autopush=True: Automatically push ISR to FIFO when full
# - in_shiftdir=SHIFT_LEFT: Shift ISR left (MSB first)
# - freq=60000: 16.67µs per tick for fine-grained sampling
@rp2.asm_pio(autopush=True, in_shiftdir=rp2.PIO.SHIFT_LEFT)
def opentherm_rx():
    # wait for start bit
    wait(1, pin, 0)
    wait(0, pin, 0)

    # kick off initial bit read
    set(x, 14)  # 14 loops, ~3 ticks per loop, 60kHz == ~700µs timeout
    jmp("wait_for_bit_currently_0")

    # read the current bit from the GPIO
    label("read_next_bit")
    in_(pins, 1)
    set(x, 14)  # 14 loops, ~3 ticks per loop, 60kHz == ~700µs timeout
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


# Initialize state machines
sm_opentherm_tx = rp2.StateMachine(0, opentherm_tx, freq=PIO_TX_FREQ, set_base=machine.Pin(0), out_base=machine.Pin(0))
sm_opentherm_rx = rp2.StateMachine(1, opentherm_rx, freq=PIO_RX_FREQ, in_base=machine.Pin(1), jmp_pin=machine.Pin(1))


async def opentherm_exchange(msg_type: int, data_id: int, data_value: int, timeout_ms: int = 1000, debug: bool=False) -> tuple[int, int, int]:
    """Perform an OpenTherm request-response exchange via PIO state machines.

    Hardware interface notes:
    - TX uses inverted Manchester encoding because the PIO output is hardware-inverted
      (see opentherm_tx PIO definition line 10: "hardware is inverted for transmission")
    - RX does NOT invert because it reads the raw pin state directly
    - This asymmetry is intentional and matches the OpenTherm electrical interface
    """
    f = frame_encode(msg_type, data_id, data_value)
    m = manchester_encode(f, invert=True)  # Invert for TX hardware
    if debug:
        print(f"> {f:08x} {(m >> 48) & 0xffff:016b} {(m >> 32) & 0xffff:016b} {(m >> 16) & 0xffff:016b} {m & 0xffff:016b}")

    # setup pio
    sm_opentherm_tx.active(0)
    sm_opentherm_rx.active(0)
    while sm_opentherm_rx.rx_fifo():
        sm_opentherm_rx.get()
    while sm_opentherm_tx.rx_fifo():
        sm_opentherm_tx.get()

    # send the data using the transmitter pio
    sm_opentherm_tx.put(int(m) >> 32)
    sm_opentherm_tx.put(int(m))
    sm_opentherm_tx.restart()
    sm_opentherm_tx.active(1)
    # wait for the pio to finish - don't care about value
    while not sm_opentherm_tx.rx_fifo():
        await asyncio.sleep_ms(1)
    sm_opentherm_tx.get()
    sm_opentherm_tx.active(0)

    # OT spec 4.3.1: slave response must arrive between 20ms and 400ms after request (v4.2; was 800ms in v2.2)
    await asyncio.sleep_ms(20)

    # wait for response
    sm_opentherm_rx.restart()
    sm_opentherm_rx.active(1)
    timeout = time.ticks_ms() + timeout_ms
    while sm_opentherm_rx.rx_fifo() < 2 and time.ticks_ms() < timeout:
        await asyncio.sleep_ms(10)
    sm_opentherm_rx.active(0)

    # check we didn't time out
    if sm_opentherm_rx.rx_fifo() < 2:
        raise Exception("Timeout waiting for response")

    # decode it (no inversion needed - RX reads raw pin state)
    a = sm_opentherm_rx.get()
    b = sm_opentherm_rx.get()
    m2 = (a << 32) | b
    f2 = 0
    try:
        f2 = manchester_decode(m2)  # No inversion for RX
    finally:
        if debug:
            print(f"< {f2:08x} {(m2 >> 48) & 0xffff:016b} {(m2 >> 32) & 0xffff:016b} {(m2 >> 16) & 0xffff:016b} {m2 & 0xffff:016b}")
    return frame_decode(f2)
