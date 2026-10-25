"""
Lightweight mock hardware module used by the GUI when not running on a Raspberry Pi.
This mirrors the behaviour of the original mock but is quiet by default. Set VERBOSE = True
at the top of this file to see debug prints during development.
"""
import os

# Toggle verbose output for debugging
VERBOSE = False

class MockGPIO:
    """A mock GPIO class to simulate RPi.GPIO functionality on a non-Pi machine."""
    BCM = 11
    OUT = 1
    LOW = 0
    HIGH = 1

    def __init__(self):
        self.pin_states = {}
        self.output_history = []
        self.cleaned_up = False

    def setmode(self, mode):
        if VERBOSE:
            print(f"[MockGPIO] Set mode to BCM")

    def setwarnings(self, flag):
        if VERBOSE:
            print(f"[MockGPIO] Set warnings to {flag}")

    def setup(self, pin, mode):
        self.pin_states.setdefault(pin, self.LOW)
        if VERBOSE:
            print(f"[MockGPIO] Setup pin {pin} as OUT")

    def output(self, pin, state):
        self.pin_states[pin] = state
        self.output_history.append((pin, state))
        if VERBOSE:
            status = "HIGH" if state == self.HIGH else "LOW"
            print(f"[MockGPIO] Set pin {pin} to {status}")

    def cleanup(self):
        self.cleaned_up = True
        for pin in list(self.pin_states):
            self.pin_states[pin] = self.LOW
        if VERBOSE:
            print("[MockGPIO] Cleanup called")


class MockTCA9548A:
    """Mocks the I2C multiplexer."""
    def select_channel(self, channel):
        if VERBOSE:
            print(f"[MockTCA9548A] Switched to I2C channel {channel}")


class MockBH1750:
    """Deterministic synthetic readings, selected without hardware access."""
    def __init__(self, channel):
        self._channel = channel
        if VERBOSE:
            print(f"[MockBH1750] Initialized on virtual channel {channel}")

    def measure_high_res(self):
        """Return fixed lux values; these are not measurements or production data."""
        scenarios = {
            "pass": (60.0, 65.0, 70.0, 75.0),
            "fail": (140.0, 65.0, 70.0, 75.0),
            "lid-open": (650.0, 650.0, 650.0, 650.0),
        }
        scenario = os.environ.get("WTT_DEMO_SCENARIO", "pass")
        if scenario not in scenarios:
            raise ValueError("WTT_DEMO_SCENARIO must be pass, fail, or lid-open")
        return scenarios[scenario][self._channel]
