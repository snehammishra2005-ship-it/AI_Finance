import unittest

from backend.services.rate_limiter import RateLimiter


class _Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class RateLimiterTests(unittest.TestCase):
    def test_allows_up_to_capacity_then_denies(self):
        clk = _Clock()
        rl = RateLimiter(capacity=3, refill_per_sec=0, time_func=clk)
        for _ in range(3):
            self.assertTrue(rl.check("k")[0])
        allowed, retry = rl.check("k")
        self.assertFalse(allowed)
        self.assertGreater(retry, 0)

    def test_refills_over_time(self):
        clk = _Clock()
        rl = RateLimiter(capacity=2, refill_per_sec=1.0, time_func=clk)
        self.assertTrue(rl.check("k")[0])
        self.assertTrue(rl.check("k")[0])
        self.assertFalse(rl.check("k")[0])  # exhausted
        clk.advance(1.1)  # ~1 token back
        self.assertTrue(rl.check("k")[0])

    def test_keys_are_independent(self):
        clk = _Clock()
        rl = RateLimiter(capacity=1, refill_per_sec=0, time_func=clk)
        self.assertTrue(rl.check("a")[0])
        self.assertFalse(rl.check("a")[0])
        self.assertTrue(rl.check("b")[0])  # a different key is unaffected

    def test_retry_after_reflects_refill_rate(self):
        clk = _Clock()
        rl = RateLimiter(capacity=1, refill_per_sec=0.5, time_func=clk)  # 1 token / 2s
        self.assertTrue(rl.check("k")[0])
        allowed, retry = rl.check("k")
        self.assertFalse(allowed)
        self.assertAlmostEqual(retry, 2.0, delta=0.05)

    def test_lru_eviction_bounds_memory(self):
        clk = _Clock()
        rl = RateLimiter(capacity=1, refill_per_sec=0, max_keys=2, time_func=clk)
        rl.check("a")
        rl.check("b")
        rl.check("c")  # exceeds max_keys -> evicts least-recently-used ("a")
        self.assertLessEqual(len(rl._buckets), 2)
        # "a" was evicted, so it starts fresh and is allowed again.
        self.assertTrue(rl.check("a")[0])


if __name__ == "__main__":
    unittest.main()
