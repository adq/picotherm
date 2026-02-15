# Picotherm - OpenTherm Boiler Controller

## Project Overview

**Picotherm** is a MicroPython-based OpenTherm boiler controller designed to run on a Raspberry Pi Pico (RP2040). It acts as a bridge between an OpenTherm-compatible boiler and a home automation system (Home Assistant) via MQTT, enabling remote monitoring and control of central heating (CH) and domestic hot water (DHW) systems.

### Key Capabilities
- OpenTherm protocol implementation for boiler communication
- MQTT integration with Home Assistant auto-discovery
- WiFi connectivity for remote access
- Real-time monitoring of boiler temperatures, pressures, and status
- Remote control of heating and hot water setpoints
- Fault detection and reporting
- Low-level PIO (Programmable I/O) for reliable Manchester encoding/decoding

---

## Architecture

### System Components

```
[Boiler with OpenTherm] <--> [Raspberry Pi Pico] <--> [WiFi] <--> [MQTT Broker] <--> [Home Assistant]
                              - GPIO 0: TX
                              - GPIO 1: RX
```

### High-Level Flow

1. **Initialization**: Pico connects to WiFi, establishes MQTT connection
2. **Status Loop**: Every ~900ms, exchanges status with boiler via OpenTherm
3. **Detailed Polling**: Every 10s, reads detailed sensor data (temperatures, pressures, etc.)
4. **MQTT Publishing**: Every 10s, publishes all data to Home Assistant
5. **Settings Sync**: Every 10s, writes any changed setpoints to the boiler
6. **MQTT Commands**: Listens for control commands from Home Assistant

---

## File Structure

```
picotherm/
├── main.py                    # Main application entry point
├── opentherm_app.py          # High-level OpenTherm application layer
├── opentherm_rp2.py          # Low-level RP2040 PIO implementation
├── lib.py                    # Encoding/decoding utilities
├── mqtt_async.py             # Async MQTT client implementation
├── cfgsecrets_template.py    # WiFi/MQTT credentials template
├── debug.py                  # Debug utilities
├── deploy                    # Deployment script using rshell
├── docs/
│   ├── Opentherm Protocol v2-2.pdf
│   └── OpenTherm-Function-Matrix-v1_0.xls
├── baxi600.txt              # Boiler-specific data ID scan results
└── unittests/
    ├── test_lib.py
    └── test_opentherm_app.py
```

---

## Core Modules

### 1. `main.py` - Application Entry Point

**Purpose**: Orchestrates the main application loops for boiler control and MQTT communication.

**Key Classes**:
- `BoilerValues`: Data class holding all boiler state (temperatures, pressures, flags, setpoints)

**Key Functions**:
- `boiler_loop()`: Main control loop - status exchange, sensor reading, setpoint writing
- `boiler()`: Outer loop handling reconnection and initialization
- `mqtt()`: MQTT connection management and publishing loop
- `msg_callback()`: Handles incoming MQTT commands from Home Assistant
- `conn_callback()`: Subscribes to MQTT command topics on connection
- `main()`: Async entry point launching both coroutines

**Data Flow**:
```
boiler_values (shared state)
    ↑         ↓
boiler()   mqtt()
    ↑         ↓
OpenTherm   MQTT Broker
```

**Home Assistant Integration**:
- Auto-discovery via MQTT: Publishes device configuration on connect
- Sensors: temperatures, pressures, flow rates, modulation, fan speed
- Binary sensors: flame active, faults (water pressure, flame, air pressure)
- Switches: CH/DHW enable
- Numbers: CH/DHW setpoint controls

---

### 2. `opentherm_app.py` - OpenTherm Protocol Layer

**Purpose**: Implements the OpenTherm protocol application layer with high-level functions for reading/writing boiler data.

**Key Functions**:

#### Status & Control
- `status_exchange()`: Primary status exchange (must be called regularly per spec)
- `send_primary_configuration()`: Sends controller configuration to boiler
- `send_primary_opentherm_version()`: Advertises OpenTherm version support

#### Temperature Control
- `control_ch_setpoint()` / `read_ch_setpoint()`: Central heating setpoint (0-100°C)
- `control_dhw_setpoint()` / `read_dhw_setpoint()`: Hot water setpoint (0-100°C)
- `control_room_setpoint()` / `read_room_setpoint()`: Room temperature setpoint
- `control_maxch_setpoint()` / `read_maxch_setpoint()`: Maximum CH setpoint

#### Sensor Readings
- `read_boiler_flow_temperature()`: Boiler flow temperature
- `read_boiler_return_water_temperature()`: Return water temperature
- `read_dhw_temperature()`: Hot water temperature
- `read_exhaust_temperature()`: Exhaust gas temperature (s16 format)
- `read_outside_temperature()`: Outside temperature sensor
- `read_fan_speed()`: Boiler fan RPM
- `read_relative_modulation_level()`: Current modulation (0-100%)
- `read_ch_water_pressure()`: Central heating pressure (bar)
- `read_dhw_flow_rate()`: Hot water flow rate (l/min)

#### Configuration & Diagnostics
- `read_secondary_configuration()`: Boiler capabilities and config
- `read_dhw_setpoint_range()`: Min/max DHW setpoint limits
- `read_maxch_setpoint_range()`: Min/max CH setpoint limits
- `read_capacity_and_min_modulation()`: Boiler capacity (kW) and min modulation
- `read_fault_flags()`: Fault status (water pressure, flame, air pressure, etc.)
- `read_oem_long_code()`: OEM diagnostic code
- `read_extra_boiler_params_support()`: Check what's readable/writable

#### Statistics
- `read_burner_starts()` / `read_burner_operation_hours()`
- `read_ch_pump_starts()` / `read_ch_pump_operation_hours()`
- `read_dhw_pump_starts()` / `read_dhw_pump_operation_hours()`

**Error Handling**: All functions use `opentherm_exchange_retry()` with automatic retry (up to 10 attempts) since OpenTherm over serial lines can be unreliable.

---

### 3. `opentherm_rp2.py` - Hardware Layer

**Purpose**: Implements low-level OpenTherm communication using RP2040 PIO (Programmable I/O) for reliable Manchester encoding/decoding.

**Hardware Configuration**:
- GPIO 0: TX (OpenTherm transmit, inverted logic: HIGH=0, LOW=1)
- GPIO 1: RX (OpenTherm receive)
- Timing: 1ms per bit (1kHz), Manchester encoded to 2kHz signal

**PIO State Machines**:

#### `opentherm_tx` (StateMachine 0)
- **Frequency**: 4 kHz (250µs per tick)
- **Function**: Transmits Manchester-encoded OpenTherm frames
- **Sequence**:
  1. Send start bit (LOW→HIGH, hardware inverted)
  2. Send 32 Manchester-encoded data bits (64 transitions)
  3. Send stop bit (LOW→HIGH, hardware inverted)
  4. Signal completion via FIFO

#### `opentherm_rx` (StateMachine 4)
- **Frequency**: 60 kHz (17µs per tick)
- **Function**: Receives Manchester-encoded frames
- **Sequence**:
  1. Wait for start bit (HIGH→LOW transition)
  2. Read bits using Manchester decoding with timeout
  3. Edge detection: waits for transitions or 650µs timeout
  4. Pushes received bits to RX FIFO

**Key Function**:
- `opentherm_exchange(msg_type, data_id, data_value, timeout_ms)`:
  - Encodes and transmits OpenTherm frame
  - Waits for response with timeout
  - Decodes and validates response
  - Returns (msg_type, data_id, data_value) tuple
  - Raises exception on timeout or decoding error

---

### 4. `lib.py` - Encoding/Decoding Utilities

**Purpose**: Provides low-level OpenTherm frame encoding/decoding and data type conversions.

**Manchester Encoding**:
- `manchester_encode(frame, invert)`: Converts 32-bit frame to 64-bit Manchester-encoded
  - Inverted mode: 1→01, 0→10 (for transmission)
  - Normal mode: 1→10, 0→01 (for reception)
- `manchester_decode(mframe, invert)`: Decodes 64-bit to 32-bit, validates transitions

**Frame Encoding/Decoding**:
- `frame_encode(msg_type, data_id, data_value)`: Creates OpenTherm frame with parity
  - Format: `[P|MMM|XXXX|DDDDDDDD|VVVVVVVVVVVVVVVV]` (32 bits)
  - P: parity bit (odd parity)
  - MMM: message type (3 bits)
  - XXXX: spare (4 bits)
  - DDDDDDDD: data ID (8 bits)
  - VVVVVVVVVVVVVVVV: data value (16 bits)
- `frame_decode(frame)`: Extracts message type, data ID, value; validates parity

**Data Type Conversions**:
- `s8(x)`: Signed 8-bit conversion
- `s16(x)`: Signed 16-bit conversion
- `f88(x)`: Fixed-point 8.8 format to float (divide by 256)

---

### 5. `mqtt_async.py` - MQTT Client

**Purpose**: Full-featured async MQTT client for MicroPython with auto-reconnection.

**Features**:
- Async/await using MicroPython's `uasyncio`
- QoS 0 and 1 support (not QoS 2)
- Auto-reconnection for both WiFi and MQTT
- Last will and testament support
- Subscription management
- Publish with sync/async options

**Key Classes**:
- `MQTTMessage`: Message container (topic, payload, retain, qos, pid)
- `MQTTProto`: Low-level MQTT protocol implementation
- `MQTTClient`: High-level client with connection management

**Configuration** (via `config` dict):
- Server, port, credentials
- Response time, keepalive interval
- WiFi credentials (SSID, password)
- Callbacks: `subs_cb`, `wifi_coro`, `connect_coro`
- Clean session flag

**Auto-Reconnection Strategy**:
1. Detect connection failure (timeout or error)
2. Try MQTT reconnect (if WiFi up)
3. If fails, disconnect and reconnect WiFi
4. Retry DNS lookup if needed
5. Continue indefinitely until manual disconnect

**Power Management**: Disables WiFi power save (`pm = 0xa11140`) for reliable operation

---

## OpenTherm Protocol Details

### Message Types
- `0x0` (READ_DATA): Request data from boiler
- `0x1` (WRITE_DATA): Write data to boiler
- `0x4` (READ_ACK): Boiler acknowledges read with data
- `0x5` (WRITE_ACK): Boiler acknowledges write
- `0x6` (DATA_INVALID): Boiler reports invalid data
- `0x7` (UNKNOWN_DATA_ID): Boiler doesn't support this data ID

### Important Data IDs
- `0` (STATUS): Master/slave status flags
- `1` (TSET): CH water setpoint
- `5` (ASF_FAULT): Application-specific fault flags
- `17` (REL_MOD_LEVEL): Relative modulation level
- `18` (CH_PRESSURE): CH water pressure
- `25` (TBOILER): Boiler water temperature
- `26` (TDHW): DHW temperature
- `28` (TRET): Return water temperature
- `33` (TEXHAUST): Exhaust temperature
- `56` (TDHWSET): DHW setpoint
- `57` (MAXTSET): Max CH water setpoint

### Timing Requirements
- Status exchange must occur at least once per second
- Each exchange is a request-response pair
- Typical response timeout: 1000ms
- Errors are common and expected - retry logic is essential

---

## Boiler-Specific Information

### Baxi 600 Combi (Example)

The included `baxi600.txt` shows a scan of supported data IDs for this specific boiler model:

**Readable Standard IDs**: Status, temperature setpoints, fault flags, modulation, pressure, flow rate, temperatures, fan speed, capacity, OEM codes

**Writable IDs**: Temperature setpoints (CH, DHW, room), max setpoints, modulation limit

**Non-standard IDs**: 128-214 (manufacturer-specific, undocumented)

---

## Deployment & Development

### Hardware Requirements
- Raspberry Pi Pico (or any RP2040 board)
- OpenTherm adapter/interface circuit (not included in this repo)
- 3.3V ↔ OpenTherm voltage level conversion

### Software Dependencies
- MicroPython for RP2040 (tested with v1.19+)
- No external libraries required (all included)

### Deployment Process
1. Create `cfgsecrets.py` from template with WiFi/MQTT credentials
2. Run `./deploy` script (uses `rshell` to copy files to Pico)
3. Reset Pico - `main.py` runs automatically

### Configuration
Edit `main.py` constants:
- `STATUS_LOOP_DELAY_MS`: Status exchange interval (default: 900ms)
- `GET_DETAILED_STATS_MS`: Detailed sensor polling interval (default: 10s)
- `WRITE_SETTINGS_MS`: Setpoint sync interval (default: 10s)
- `MQTT_PUBLISH_MS`: MQTT publish interval (default: 10s)

### Testing
```bash
pytest unittests/  # Run unit tests (requires pytest)
```

Tests cover:
- Manchester encoding/decoding
- Frame encoding/decoding with parity
- Data type conversions
- Error handling

---

## Home Assistant Integration

### MQTT Topics

**Configuration** (published on connect):
```
homeassistant/{component}/{entity}/config
```

**State Topics**:
```
homeassistant/sensor/boilerReturnTemperature/state
homeassistant/sensor/boilerExhaustTemperature/state
homeassistant/sensor/boilerFanSpeed/state
homeassistant/sensor/boilerModulationLevel/state
homeassistant/sensor/boilerChPressure/state
homeassistant/binary_sensor/boilerFlameActive/state
homeassistant/binary_sensor/boilerFaultActive/state
... (and many more)
```

**Command Topics**:
```
homeassistant/switch/boilerCHEnabled/command  (ON/OFF)
homeassistant/switch/boilerDHWEnabled/command  (ON/OFF)
homeassistant/number/boilerCHFlowTemperatureSetpoint/command  (numeric)
homeassistant/number/boilerDHWFlowTemperatureSetpoint/command  (numeric)
```

### Device Configuration

All entities are grouped under a single device:
- **Name**: "Boiler"
- **Identifier**: `["boiler"]`

This creates a unified dashboard in Home Assistant with all sensors and controls in one place.

---

## Error Handling & Resilience

### OpenTherm Layer
- Automatic retry (up to 10 attempts) for each exchange
- 100ms delay between retries
- Exceptions propagate for unrecoverable errors

### Main Application
- Outer loop catches all exceptions in `boiler()` and `mqtt()` coroutines
- 5-second delay before retry after error
- Continues indefinitely - no crash on transient errors

### MQTT Layer
- Auto-reconnection for WiFi and MQTT failures
- Ping/keepalive to detect dead connections
- Response timeout detection
- Graceful handling of connection loss

### WiFi Robustness
- Automatic reconnection on disconnect
- Power save disabled for reliability
- DNS re-lookup on reconnection
- Multiple connection attempts with backoff

---

## Known Issues & Limitations

1. **OpenTherm Specification**: Only core protocol implemented, no support for:
   - Cooling control (rarely used)
   - Time/date synchronization
   - Remote parameter access (TSP/FHB)

2. **MQTT QoS**: QoS 2 not supported (rarely needed)

3. **WiFi Stability**: Some Pico WiFi modules have reliability issues:
   - Automatic reset after multiple failed connections
   - Power save disabled to prevent dropouts

4. **Boiler Compatibility**: Not all boilers support all data IDs:
   - Always check `read_extra_boiler_params_support()` first
   - Handle exceptions gracefully for unsupported features

5. **Timing Sensitivity**: PIO timing is critical:
   - GPIO frequency must be exact
   - Clock drift can cause decoding errors

---

## Future Enhancements

Potential improvements:
- [ ] Web interface for local configuration
- [ ] SD card logging for diagnostics
- [ ] Support for multiple heating zones (CH2)
- [ ] PID control loop for temperature regulation
- [ ] Historical data storage and graphing
- [ ] OTA (Over-The-Air) firmware updates
- [ ] Support for other protocols (e.g., EMS, eBUS)

---

## Debugging

### Debug Mode
Set `debug=True` in `opentherm_exchange()` calls to print raw frames:
```
> f2a80100 1010101010101010 1001100110011001 0101010101010101 0101010101010101
< f2a80100 1010101010101010 1001100110011001 0101010101010101 0101010101010101
```

### Common Issues

**"Timeout waiting for response"**:
- Check wiring between Pico and OpenTherm interface
- Verify OpenTherm adapter is powered
- Ensure boiler supports OpenTherm (not just on/off control)

**WiFi connection failures**:
- Check SSID and password in `cfgsecrets.py`
- Verify 2.4 GHz network (Pico doesn't support 5 GHz)
- Move closer to access point
- Check for MAC address filtering

**MQTT connection failures**:
- Verify broker address and port
- Check username/password if required
- Ensure broker allows connections from LAN
- Check firewall rules

**Boiler not responding to setpoint changes**:
- Verify boiler allows remote control (check boiler settings)
- Some boilers prioritize local thermostat over OpenTherm
- Check `read_extra_boiler_params_support()` for write permissions

---

## References

- [OpenTherm Protocol Specification v2.2](docs/Opentherm%20Protocol%20v2-2.pdf)
- [OpenTherm Function Matrix v1.0](docs/OpenTherm-Function-Matrix-v1_0.xls)
- [MicroPython RP2 Documentation](https://docs.micropython.org/en/latest/rp2/quickref.html)
- [RP2040 PIO Guide](https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf)

---

## License

Not specified in repository. Contact author: Andrew de Quincey <adq@lidskialf.net>

---

## Contributing

When modifying this codebase:
1. Test thoroughly - boiler control is safety-critical
2. Maintain OpenTherm protocol compliance
3. Keep timing-critical code in PIO where possible
4. Document any boiler-specific quirks in comments
5. Add unit tests for new encoding/decoding functions

---

*Generated: 2026-02-15*
