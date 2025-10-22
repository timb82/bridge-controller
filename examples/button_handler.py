from machine import Pin
import time

class ButtonHandler:
    def __init__(self, button_pins, debounce_ms=50):
        """Initialize button handler with a dictionary of pin numbers and their names
        Args:
            button_pins (dict): Dictionary of button names and their pin numbers
            debounce_ms (int): Debounce time in milliseconds
        """
        self.buttons = {}
        self.led_states = {}
        self.debounce_ms = debounce_ms
        self.last_trigger_time = {}
        self.external_handlers = {}
        
        # Initialize buttons
        for name, pin in button_pins.items():
            self.buttons[name] = Pin(pin, Pin.IN, Pin.PULL_UP)
            self.last_trigger_time[name] = 0
            # Set up the IRQ handler
            self.buttons[name].irq(trigger=Pin.IRQ_FALLING, handler=lambda p, n=name: self._button_handler(n))
            
            # Create an LED for each button (can be modified later)
            self.led_states[name] = {'pin': None, 'state': False}

    def set_led_pin(self, button_name, led_pin):
        """Assign an LED pin to a specific button
        Args:
            button_name (str): Name of the button
            led_pin (int): GPIO pin number for LED
        """
        if button_name in self.buttons:
            self.led_states[button_name]['pin'] = Pin(led_pin, Pin.OUT)
            self.led_states[button_name]['pin'].value(self.led_states[button_name]['state'])

    def add_handler(self, button_name, handler_function):
        """Add an external handler function for a specific button
        Args:
            button_name (str): Name of the button
            handler_function (function): Function to be called when button is pressed
        """
        if button_name in self.buttons:
            self.external_handlers[button_name] = handler_function

    def _button_handler(self, button_name):
        """Internal IRQ handler for button presses
        Args:
            button_name (str): Name of the button that triggered the IRQ
        """
        # Debounce check
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_trigger_time.get(button_name, 0)) < self.debounce_ms:
            return
        
        self.last_trigger_time[button_name] = current_time
        
        # Toggle LED state if LED is assigned
        if self.led_states[button_name]['pin'] is not None:
            self.led_states[button_name]['state'] = not self.led_states[button_name]['state']
            self.led_states[button_name]['pin'].value(self.led_states[button_name]['state'])
        
        # Call external handler if exists
        if button_name in self.external_handlers:
            self.external_handlers[button_name]()

    def get_button_state(self, button_name):
        """Get the current state of a button
        Args:
            button_name (str): Name of the button
        Returns:
            bool: Current button state
        """
        if button_name in self.buttons:
            return not self.buttons[button_name].value()  # Inverted because of PULL_UP
        return False

    def get_led_state(self, button_name):
        """Get the current state of an LED
        Args:
            button_name (str): Name of the button associated with the LED
        Returns:
            bool: Current LED state
        """
        if button_name in self.led_states:
            return self.led_states[button_name]['state']
        return False