import machine
import rp2
import time


# opentherm tx - transmit pre-manchester-encoded-bits. Automatically sends start and stop bits.
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW, out_init=rp2.PIO.OUT_LOW, autopull=True)
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


# # opentherm rx - receive manchester-encoded-bits, waiting for initial start bit
# @rp2.asm_pio(autopush=True)
# def opentherm_rx():
#     # wait for start bit
#     wait(1, pins, 0)
#     wait(0, pins, 0)
#     jmp("wait_for_bit_currently_0")

#     # read the current bit from the GPIO
#     label("read_next_bit")
#     in_(pins, 1)
#     set(x, 12)  # 13 loops, 4 ticks per loop, 80kHz == 650uS
#     jmp(pins, "wait_for_bit_currently_1")

#     # wait for a bit change from 0->1 or timeout
#     label("wait_for_bit_currently_0")
#     mov(y, invert(pins))
#     jmp(y_dec, "read_next_bit")
#     jmp(dec_x, "wait_for_bit_currently_0")
#     jmp("read_next_bit")

#     # wait for a bit change from 1->0 or timeout
#     label("wait_for_bit_currently_1")
#     mov(y, pins)
#     jmp(y_dec, "read_next_bit")
#     jmp(x_dec, "wait_for_bit_currently_1")
#     jmp("read_next_bit")

# sm_opentherm_rx = rp2.StateMachine(1, opentherm_rx, freq=80000, in_base=machine.Pin(1), jmp_pin=machine.Pin(1)) # each tick is 12.5uS


def manchester_encode(frame):
    """
    Manchester encodes a 32 bit frame into a 64 bit integer
    """

    mframe = 0
    mask = 0x8000000
    for i in range(32):
        if frame & mask:
            mframe <<= 2
            mframe |= 2
        else:
            mframe <<= 2
            mframe |= 1
        mask >>= 1

    return mframe


def frame_encode(msg_type, data_id, data_value):
    """
    Encodes opentherm info into a 32 bit frame
    """

    frame = 0
    frame |= (msg_type & 0x07) << 1
    frame |= (data_id & 0xff) << 8
    frame |= (data_value & 0xffff) << 16
    frame |= (bin(frame).count("1") & 1) # parity bit
    return frame


# p = machine.Pin(0, mode=machine.Pin.OUT)
# p.on()


print("HEYY")
while True:
    # p.on()
    # time.sleep(1)
    # p.off()
    # time.sleep(1)

    f = frame_encode(0x06, 0xbb, 0xccdd)
    m = manchester_encode(f)
    print(f"{f:032b} {m:064b}")

    sm_opentherm_tx.restart()
    sm_opentherm_tx.active(1)
    sm_opentherm_tx.put(0)
    sm_opentherm_tx.put(0)
    # sm_opentherm_tx.put(m & 0xffffffff)
    # sm_opentherm_tx.put(m >> 32)
    print("sleep")
    time.sleep(1)

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
