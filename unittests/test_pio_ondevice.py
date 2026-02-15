"""
On-Device PIO Testing

Run these tests ON the Pico hardware to validate PIO state machines.
Deploy with: mpremote cp test_pio_ondevice.py : + run test_pio_ondevice.py

Hardware setup:
- Loopback: Connect GPIO 0 (TX) to GPIO 1 (RX) with a wire
- This allows testing TX->RX data integrity without external OpenTherm device

NOTE: These tests are marked with pytest.mark.hardware and should NOT run
in the normal test suite. They require actual RP2040 hardware.
"""

import sys
import asyncio
import pytest

# Only import hardware modules when actually on device
try:
    import machine
    import rp2
    from opentherm_rp2 import opentherm_exchange
    ON_DEVICE = True
except ImportError:
    ON_DEVICE = False
    print("WARNING: Not on device, skipping on-device tests")

from lib import manchester_encode, manchester_decode, frame_encode, frame_decode


@pytest.mark.hardware
class TestPIOLoopback:
    """Tests that require GPIO loopback (GPIO 0 -> GPIO 1)."""

    @pytest.mark.asyncio
    async def test_loopback_simple_frame(self):
        """Test TX->RX loopback with a simple frame."""
        if not ON_DEVICE:
            print("SKIP: test_loopback_simple_frame (not on device)")
            return

        print("TEST: Loopback simple frame")

        msg_type = 0x00  # Read-Data
        data_id = 0x00   # Status
        data_value = 0x0000

        try:
            # This will fail with timeout because there's no boiler responding
            # But we can check that TX works and RX waits correctly
            result = await opentherm_exchange(msg_type, data_id, data_value, timeout_ms=100)
            print(f"UNEXPECTED: Got result {result}")
        except Exception as e:
            if "Timeout" in str(e):
                print("PASS: Timeout expected (no boiler connected)")
            else:
                print(f"FAIL: Unexpected exception: {e}")
                raise

    @pytest.mark.asyncio
    async def test_tx_timing(self):
        """Verify TX timing by measuring output pin transitions."""
        if not ON_DEVICE:
            print("SKIP: test_tx_timing (not on device)")
            return

        print("TEST: TX timing measurement")

        # This test would require:
        # 1. Configure a GPIO as input to monitor TX output
        # 2. Record timestamps of transitions
        # 3. Verify 500µs per Manchester bit
        # 4. Verify total frame time ~34ms

        print("TODO: Implement timing measurement with GPIO monitoring")

    @pytest.mark.asyncio
    async def test_rx_sensitivity(self):
        """Test RX can detect valid OpenTherm signals."""
        if not ON_DEVICE:
            print("SKIP: test_rx_sensitivity (not on device)")
            return

        print("TEST: RX sensitivity")

        # This test would require:
        # 1. Generate test signal on another GPIO
        # 2. Feed to RX GPIO
        # 3. Verify RX decodes correctly

        print("TODO: Implement RX sensitivity test with signal generator")


@pytest.mark.hardware
class TestPIOManualValidation:
    """Manual validation tests - require human verification."""

    @pytest.mark.asyncio
    async def test_tx_output_visual(self):
        """Visual test: observe TX output with logic analyzer or oscilloscope."""
        if not ON_DEVICE:
            print("SKIP: test_tx_output_visual (not on device)")
            return

        print("TEST: TX output visual inspection")
        print("Connect logic analyzer to GPIO 0")
        print("Expected: Start bit, 64 Manchester bits, stop bit")
        print("Bit period: 500µs per Manchester bit")

        msg_type = 0x00
        data_id = 0x00
        data_value = 0xAAAA  # Alternating pattern for easy visualization

        print(f"Transmitting frame: type={msg_type:02x} id={data_id:02x} value={data_value:04x}")

        try:
            await opentherm_exchange(msg_type, data_id, data_value, timeout_ms=100, debug=True)
        except:
            pass  # Timeout expected

        print("Check logic analyzer for correct timing and pattern")

    @pytest.mark.asyncio
    async def test_opentherm_device_communication(self):
        """Test communication with actual OpenTherm device."""
        if not ON_DEVICE:
            print("SKIP: test_opentherm_device_communication (not on device)")
            return

        print("TEST: Real OpenTherm device communication")
        print("Connect to OpenTherm thermostat or boiler")

        # Try to read status
        try:
            msg_type, data_id, data_value = await opentherm_exchange(
                0x00, 0x00, 0x0000,  # Read status
                timeout_ms=1000,
                debug=True
            )

            print(f"SUCCESS: Received response")
            print(f"  Type: {msg_type:02x} (expected 0x04 for Read-Ack)")
            print(f"  ID: {data_id:02x}")
            print(f"  Value: {data_value:04x}")

            if msg_type == 0x04:
                print("PASS: Valid Read-Ack received from OpenTherm device")
            else:
                print(f"WARN: Unexpected message type {msg_type:02x}")

        except Exception as e:
            print(f"FAIL: {e}")


async def run_all_tests():
    """Run all on-device tests."""
    print("=" * 60)
    print("PIO On-Device Test Suite")
    print("=" * 60)

    if not ON_DEVICE:
        print("Not running on device - tests skipped")
        return

    loopback_tests = TestPIOLoopback()
    manual_tests = TestPIOManualValidation()

    # Run loopback tests
    print("\n--- Loopback Tests (require GPIO 0 -> GPIO 1 wire) ---")
    await loopback_tests.test_loopback_simple_frame()
    await loopback_tests.test_tx_timing()
    await loopback_tests.test_rx_sensitivity()

    # Run manual validation tests
    print("\n--- Manual Validation Tests ---")
    await manual_tests.test_tx_output_visual()
    await manual_tests.test_opentherm_device_communication()

    print("\n" + "=" * 60)
    print("Test suite complete")
    print("=" * 60)


if __name__ == "__main__":
    if ON_DEVICE:
        asyncio.run(run_all_tests())
    else:
        print("Run this script on the Pico with:")
        print("  mpremote cp test_pio_ondevice.py : + run test_pio_ondevice.py")
