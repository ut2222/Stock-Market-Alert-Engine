class SegmentTree:
    """
    Answers range min/max queries on a fixed array in O(log n).

    Use case in this project: given 100 days of closing prices,
    instantly answer "what was the highest close between day 20 and day 50?"
    without scanning those 30 elements every time.

    Structure: a binary tree stored as a flat array.
    - Node at index i covers a range of the original array.
    - Its left child is at 2*i, right child at 2*i+1.
    - Leaf nodes hold individual prices.
    - Internal nodes hold the min/max of their children's ranges.

    Building the tree: O(n)
    Querying any range: O(log n)
    """

    def __init__(self, data: list, mode: str = "max"):
        """
        data: list of floats (e.g. closing prices, oldest first)
        mode: 'max' or 'min'
        """
        if mode not in ("max", "min"):
            raise ValueError("mode must be 'max' or 'min'")

        self.n = len(data)
        self.mode = mode
        self.tree = [0.0] * (4 * self.n)  # 4n is safe upper bound for tree size
        self._build(data, 1, 0, self.n - 1)

    def _combine(self, a: float, b: float) -> float:
        return max(a, b) if self.mode == "max" else min(a, b)

    def _build(self, data, node, start, end):
        """Recursively build the tree bottom-up."""
        if start == end:
            self.tree[node] = data[start]
        else:
            mid = (start + end) // 2
            self._build(data, 2 * node,     start, mid)
            self._build(data, 2 * node + 1, mid + 1, end)
            self.tree[node] = self._combine(
                self.tree[2 * node],
                self.tree[2 * node + 1]
            )

    def query(self, left: int, right: int) -> float:
        """
        Return the max (or min) value between indices left and right inclusive.
        Both indices are 0-based relative to the original data array.
        O(log n).
        """
        if left < 0 or right >= self.n or left > right:
            raise ValueError(f"Invalid range [{left}, {right}] for n={self.n}")
        return self._query(1, 0, self.n - 1, left, right)

    def _query(self, node, start, end, left, right):
        """Recursive range query."""
        if right < start or end < left:
            # This node's range is completely outside the query range
            return float('-inf') if self.mode == "max" else float('inf')

        if left <= start and end <= right:
            # This node's range is completely inside the query range
            return self.tree[node]

        # Partial overlap — recurse into both children
        mid = (start + end) // 2
        left_result  = self._query(2 * node,     start, mid,     left, right)
        right_result = self._query(2 * node + 1, mid + 1, end,   left, right)
        return self._combine(left_result, right_result)