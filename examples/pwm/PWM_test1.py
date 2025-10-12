from machine import Pin
from rp2 import PIO, StateMachine, asm_pio
from array import array


class SyncPWM:
    """
    Class for generating synchronized PWM signals using PIO state machines.
    One signal is inverted relative to the other.
    """

    @asm_pio(set_init=PIO.OUT_LOW)
    def pwm_prog():
        # Setup
        pull(noblock)  # Get duty value
        mov(y, osr)  # Store duty in y

        wrap_target()
        # High period
        mov(x, y)  # Load duty value
        set(pins, 1)  # Set pin high
        label("high")
        jmp(x_dec, "high")  # Stay high for duty period

        # Low period
        mov(x, invert(y))  # Load inverse of duty for low period
        set(pins, 0)  # Set pin low
        label("low")
        jmp(x_dec, "low")  # Stay low for remaining period

        # End cycle
        irq(0)  # Signal end of cycle
        wrap()  # Loop back

    @asm_pio(set_init=PIO.OUT_HIGH)
    def pwm_prog_inv():
        # Setup
        pull(noblock)  # Get duty value
        mov(y, osr)  # Store duty in y

        wrap_target()
        # Low period (inverted)
        mov(x, y)  # Load duty value
        set(pins, 0)  # Set pin low
        label("low")
        jmp(x_dec, "low")  # Stay low for duty period

        # High period (inverted)
        mov(x, invert(y))  # Load inverse of duty for high period
        set(pins, 1)  # Set pin high
        label("high")
        jmp(x_dec, "high")  # Stay high for remaining period

        # End cycle
        irq(1)  # Signal end of cycle
        wrap()  # Loop back

    @asm_pio()
    def sync_prog():
        # Simple sync program to monitor both PWM outputs
        wrap_target()
        wait(1, irq, 0)  # Wait for PWM1 cycle complete
        wait(1, irq, 1)  # Wait for PWM2 cycle complete
        nop()[31]  # Add delay to ensure stable operation
        wrap()

    def __init__(self, pin1=16, pin2=17, freq=1000, duty=75):
        """
        Initialize the PWM controller with two complementary outputs.

        Args:
            pin1: GPIO pin for first PWM output (default: 16)
            pin2: GPIO pin for second PWM output (default: 17)
            freq: PWM frequency in Hz (default: 1000)
            duty: Duty cycle in percentage (default: 75)
        """
        self.pin1 = Pin(pin1, Pin.OUT)
        self.pin2 = Pin(pin2, Pin.OUT)

        # Initialize state machines
        # Use a lower base frequency for more precise timing
        base_freq = 1_000_000  # 1 MHz base frequency
        self.sm1 = StateMachine(0, self.pwm_prog, freq=base_freq, set_base=self.pin1)
        self.sm2 = StateMachine(1, self.pwm_prog_inv, freq=base_freq, set_base=self.pin2)
        self.sm_sync = StateMachine(2, self.sync_prog, freq=base_freq)

        # Initialize frequency and duty cycle
        self.freq = freq
        self.duty = duty
        self.update_pwm_parameters()

        # Start all state machines
        self.start()

    def update_pwm_parameters(self):
        """Update both frequency and duty cycle parameters"""
        # Calculate the total number of cycles for one period at the desired frequency
        # Each instruction takes 1 clock cycle at the configured frequency
        total_cycles = int(125_000_000 / self.freq)  # Total cycles for period

        # Calculate duty cycle value (scaled 0-65535)
        # This gives us good resolution for the duty cycle
        MAX_COUNT = 65535
        duty_scaled = int((MAX_COUNT * self.duty) / 100)

        # Make sure we never hit 0 or maximum to ensure transitions
        duty_scaled = max(1, min(duty_scaled, MAX_COUNT - 1))

        # Update both state machines with the duty value
        # The PIO programs will handle the timing internally
        self.sm1.put(duty_scaled)
        self.sm2.put(duty_scaled)

    def set_frequency(self, freq):
        """Set PWM frequency in Hz"""
        self.freq = freq
        self.update_pwm_parameters()

    def set_duty_cycle(self, duty):
        """Set duty cycle in percentage (0-100)"""
        self.duty = min(100, max(0, duty))  # Clamp duty cycle between 0-100
        self.update_pwm_parameters()

    def start(self):
        """Start PWM generation"""
        # Ensure outputs are in correct initial states
        self.pin1.value(0)
        self.pin2.value(1)

        # Start state machines
        self.sm1.active(1)
        self.sm2.active(1)
        self.sm_sync.active(1)

    def stop(self):
        """Stop PWM generation"""
        self.sm1.active(0)
        self.sm2.active(0)
        self.sm_sync.active(0)

        # Set outputs to safe states
        self.pin1.value(0)
        self.pin2.value(1)


# Example usage
if __name__ == "__main__":
    # Create PWM instance with default settings (pins 16,17, 1kHz, 75% duty)
    pwm = SyncPWM()

    # The PWM signals will start automatically
    # You can modify frequency and duty cycle on the fly:
    # pwm.set_frequency(2000)  # Change to 2kHz
    # pwm.set_duty_cycle(50)   # Change to 50% duty cycle
while True:
    pass  # Keep the script running to maintain PWM output
