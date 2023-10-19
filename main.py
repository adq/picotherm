import machine
import rp2
import time
from lib import manchester_encode, frame_encode, manchester_decode, frame_decode


# opentherm tx - transmit pre-manchester-encoded-bits. Automatically sends start and stop bits.
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW, autopull=True, out_shiftdir=rp2.PIO.SHIFT_RIGHT)
def opentherm_tx():
    # counter for bit writing loop
    set(x, 31)

    # write start bit
    set(pins, 1)
    nop()
    set(pins, 0)
    nop()

    # write the manchester encoded data
    label("write_bits")
    out(pins, 1)
    nop()
    out(pins, 1)
    jmp(x_dec, "write_bits")

    # write stop bit
    set(pins, 1)
    nop()
    set(pins, 0)
    nop()

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
    set(x, 12)  # 13 loops, 3 ticks per loop, 60kHz == 650uS
    jmp("wait_for_bit_currently_0")

    # read the current bit from the GPIO
    label("read_next_bit")
    in_(pins, 1)
    set(x, 12)  # 13 loops, 3 ticks per loop, 60kHz == 650uS
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


sm_opentherm_rx.active(1)
sm_opentherm_tx.active(1)


print("HEYY")
while True:
    x = (0x06, 0xbb, 0xccdd)
    f = frame_encode(*x)
    m = manchester_encode(f)

    sm_opentherm_rx.active(0)
    while sm_opentherm_rx.rx_fifo():
        sm_opentherm_rx.get()
    sm_opentherm_rx.restart()
    sm_opentherm_rx.active(1)

    sm_opentherm_tx.active(0)
    sm_opentherm_tx.put(m)
    sm_opentherm_tx.put(m >> 32)
    sm_opentherm_tx.restart()
    sm_opentherm_tx.active(1)

    m2 = sm_opentherm_rx.get() | (sm_opentherm_rx.get() << 32)

    f2 = manchester_decode(m2)
    x2 = frame_decode(f2)

    assert x == x2

    # print(bin(sm_opentherm_rx.get())) # , hex(sm_opentherm_rx.get()))
    # print("sleep")
    # time.sleep(1)

    # time.sleep(5)



# # Continually start and stop state machine
# while True:
#     print("Starting state machine...")
#     sm.active(1)
#     sm_opentherm_tx.put()
#     utime.sleep(1)
#     print("Stopping state machine...")
#     sm.active(0)
#     utime.sleep(1)
