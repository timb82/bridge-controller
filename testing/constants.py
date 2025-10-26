from micropython import const
import gc
from time import ticks_us, ticks_diff

# Define constants using different conventions
CONST1 = 5
CONST2 = const(5)
_CONST3 = const(5)


def measure_memory(iterations=10):
    """Measure memory usage for each constant over multiple iterations
    Args:
        iterations: Number of iterations to run (default 1000)
    Returns:
        tuple: Average memory usage (bytes) for each constant type
    """
    total_mem1 = total_mem2 = total_mem3 = 0

    for _ in range(iterations):
        gc.collect()
        mem_start = gc.mem_free()

        # Create list of constants to force memory allocation
        test1 = [CONST1 for _ in range(100)]
        mem1 = mem_start - gc.mem_free()
        total_mem1 += mem1
        del test1

        gc.collect()
        mem_start = gc.mem_free()
        test2 = [CONST2 for _ in range(100)]
        mem2 = mem_start - gc.mem_free()
        total_mem2 += mem2
        del test2

        gc.collect()
        mem_start = gc.mem_free()
        test3 = [_CONST3 for _ in range(100)]
        mem3 = mem_start - gc.mem_free()
        total_mem3 += mem3
        del test3

    # Calculate averages
    avg_mem1 = total_mem1 // iterations
    avg_mem2 = total_mem2 // iterations
    avg_mem3 = total_mem3 // iterations

    return avg_mem1, avg_mem2, avg_mem3


def measure_access_time(iterations=10000):
    """Measure access time for each constant"""
    results = []

    # Test CONST1
    start = ticks_us()
    for _ in range(iterations):
        x = CONST1
    time1 = ticks_diff(ticks_us(), start)

    # Test CONST2
    start = ticks_us()
    for _ in range(iterations):
        x = CONST2
    time2 = ticks_diff(ticks_us(), start)

    # Test _CONST3
    start = ticks_us()
    for _ in range(iterations):
        x = _CONST3
    time3 = ticks_diff(ticks_us(), start)

    return time1, time2, time3


def run_tests():
    # Memory usage test
    mem1, mem2, mem3 = measure_memory()
    print("\nMemory Usage (bytes):")
    print(f"CONST1 = 5:        {mem1:4d}")
    print(f"CONST2 = const(5): {mem2:4d}")
    print(f"_CONST3 = const(5):{mem3:4d}")

    # Access time test
    time1, time2, time3 = measure_access_time()
    print("\nAccess Time (microseconds for 10000 accesses):")
    print(f"CONST1 = 5:        {time1:4d}")
    print(f"CONST2 = const(5): {time2:4d}")
    print(f"_CONST3 = const(5):{time3:4d}")


if __name__ == "__main__":
    run_tests()
