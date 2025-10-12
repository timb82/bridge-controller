from machine import mem32, PWM, Pin, freq


# --- Constants from RP2040 datasheet ---
PWM_BASE = 0x40050000  # Base address of PWM peripheral
PWM_CHAN_OFFSET = 0x14  # Offset between slices (each slice = 20 bytes = 0x14)
PIN_A = 15
FREQ = 1000


# --- Helper: read 32-bit memory value ---
def reg32(addr):
    return mem32[addr]


# --- Initialize a PWM on some pin ---
pwm = PWM(Pin(PIN_A))
pwm.freq(FREQ)  # Set frequency (this will adjust clkdiv and top internally)

# --- Get slice number ---
slice_num = (PIN_A >> 1) if PIN_A < 16 else ((PIN_A - 16) >> 1)

# --- Register addresses ---
slice_base = PWM_BASE + slice_num * PWM_CHAN_OFFSET
CSR_REG = slice_base + 0x00  # Control/Status register
DIV_REG = slice_base + 0x04  # Clock divider register
CTR_REG = slice_base + 0x08  # Counter register
CC_REG = slice_base + 0x0C  # Compare register
TOP_REG = slice_base + 0x10  # Wrap (TOP) register

# --- Read values from registers ---
top = reg32(TOP_REG)
div_raw = reg32(DIV_REG)

# --- Extract divider (8.4 fixed point) ---
int_part = (div_raw >> 4) & 0xFF
frac_part = div_raw & 0x0F
clkdiv = int_part + frac_part / 16.0

# --- Read system clock frequency ---
fsys = freq()  # get system frequency in Hz

# --- Calculate PWM counter tick time ---
# Each PWM counter increment = clkdiv / fsys seconds
tick_time = clkdiv / fsys


# --- Print results ---
print(f"PWM slice: {slice_num}")
print(f"System clock (f_sys): {fsys} Hz")
print(f"TOP (wrap): {top}")
print(f"Clock divider (clkdiv): {clkdiv:.4f}")
print(f"PWM tick time: {tick_time * 1e9:.3f} ns per tick")
print(f"Effective PWM frequency: {fsys / (clkdiv * (top + 1)):.3f} Hz")
