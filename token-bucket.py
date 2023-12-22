"""An implementation of the token bucket algorithm for rate limiting"""

import time
import threading

class TokenBucket(object):
    # capacity is the bucket size in tokens
    # fill_rate is the rate in tokens/second that the bucket will be refilled
    def __init__(self, capacity, fill_rate):
        self.capacity = capacity
        self._tokens = capacity
        self.fill_rate = fill_rate
        self.timestamp = time.time()
        self.lock = threading.Lock()

        # Start a separate thread that refills the bucket
        self._refill_thread = threading.Thread(target=self._refill)
        self._refill_thread.daemon = True
        self._refill_thread.start()

    def _refill(self):
        while True:
            with self.lock:
                if self._tokens < self.capacity:
                    self._tokens += self.fill_rate
                    self._tokens = min(self._tokens, self.capacity)
            time.sleep(1)

    def consume_token(self):
        with self.lock:
            if self._tokens > 0:
                self._tokens -= 1
                return True
            else:
                return False

    def get_tokens(self):
        with self.lock:
            return self._tokens

    def get_capacity(self):
        return self.capacity
    

class RateLimiter(object):
    
    def __init__(self):
        self.lock = threading.Lock()
        self.ratelimiterMap = {}

    def add_user(self, user_id, capacity, fill_rate):
        with self.lock:
            if user_id not in self.ratelimiterMap:
                self.ratelimiterMap[user_id] = TokenBucket(capacity, fill_rate)
            else:
                print("User already exists")

    def remove_user(self, user_id):
        with self.lock:
            if user_id in self.ratelimiterMap:
                del self.ratelimiterMap[user_id]
            else:
                print("User does not exist")

    def shouldAllowServiceCall(self, user_id):
        with self.lock:
            if user_id in self.ratelimiterMap:
                return self.ratelimiterMap[user_id].consume_token()
            else:
                print("User does not exist")
                return False
            

# Test the rate limiter            

def worker(limiter, user_id):
    if limiter.shouldAllowServiceCall(user_id):
        print(f"Service call allowed for {user_id}. {limiter.ratelimiterMap[user_id].get_tokens()} tokens left")
    else:
        print(f"Service call denied for {user_id}. {limiter.ratelimiterMap[user_id].get_tokens()} tokens left")

def test_concurrency():
    # Create a rate limiter
    limiter = RateLimiter()

    # Add a user with a capacity of 5 tokens and a fill rate of 2 tokens/second
    limiter.add_user("user1", 5, 2)

    # Create 10 worker threads that will make service calls concurrently
    threads = [threading.Thread(target=worker, args=(limiter, "user1")) for _ in range(5)]

    # Start the threads
    for thread in threads:
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Wait for 2 seconds
    time.sleep(2)

    more_threads = [threading.Thread(target=worker, args=(limiter, "user1")) for i in range(5, 10)]

    # Start the threads again
    for thread in more_threads:
        thread.start()

    for thread in more_threads:
        thread.join()

test_concurrency()