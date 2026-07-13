from collections import deque


class SlidingWindowMinMax:
    """
    Computes rolling min and max over a window of size k in O(1) per tick.

    The naive approach scans all k elements every tick — O(n*k) total.
    This uses a monotonic deque to do it in O(n) total — a critical
    difference when processing thousands of ticks per second.

    How it works:
    - We keep a deque of indices whose values are in increasing order (for min)
      and decreasing order (for max).
    - When a new value arrives, we pop from the back any values that can never
      be the min/max (they're already beaten by the new value).
    - When the window slides forward, we pop from the front any indices that
      have fallen outside the window.
    - The front of the deque is always the current min/max.
    """

    def __init__(self, window_size: int):
        self.k = window_size
        self.values = []          # all values seen so far
        self.min_deque = deque()  # indices, values increasing front→back
        self.max_deque = deque()  # indices, values decreasing front→back

    def add(self, value: float) -> None:
        """Add a new value to the window."""
        i = len(self.values)
        self.values.append(value)

        # Remove back of min_deque while new value is smaller
        while self.min_deque and self.values[self.min_deque[-1]] >= value:
            self.min_deque.pop()
        self.min_deque.append(i)

        # Remove back of max_deque while new value is larger
        while self.max_deque and self.values[self.max_deque[-1]] <= value:
            self.max_deque.pop()
        self.max_deque.append(i)

        # Remove front if it's outside the window
        if self.min_deque[0] < i - self.k + 1:
            self.min_deque.popleft()
        if self.max_deque[0] < i - self.k + 1:
            self.max_deque.popleft()

    def get_min(self) -> float:
        """Return the minimum value in the current window. O(1)."""
        if not self.min_deque:
            raise ValueError("No values added yet")
        return self.values[self.min_deque[0]]

    def get_max(self) -> float:
        """Return the maximum value in the current window. O(1)."""
        if not self.max_deque:
            raise ValueError("No values added yet")
        return self.values[self.max_deque[0]]

    def get_range(self) -> float:
        """Return max - min for the current window."""
        return self.get_max() - self.get_min()