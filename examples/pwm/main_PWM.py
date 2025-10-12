from pwm_pio import PWMController
import time

# Create PWM controller with default settings (20kHz, 75% duty cycle)
pwm = PWMController()

# Start PWM generation
pwm.start()

# Example of changing parameters
try:
    while True:
        time.sleep(2)
        pwm.set_duty_cycle(25)  # Change to 25% duty cycle
        time.sleep(2)
        pwm.set_duty_cycle(75)  # Back to 75% duty cycle
        time.sleep(2)
        pwm.set_frequency(10000)  # Change to 10kHz
        time.sleep(2)
        pwm.set_frequency(20000)  # Back to 20kHz
except KeyboardInterrupt:
    pwm.stop()
