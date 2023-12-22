"""An implementation of the fixed window counter algorithm for rate limiting"""
import time
import threading

class FixedWindowCounter(object):

    def __init__(self, capacity, time_window):
        self.capacity = capacity
        self.time_window = time_window
        self.counter = 0
        self.lock = threading.Lock()

        # Start a separate thread that resets the counter every time_window seconds
        self._reset_counter_thread = threading.Thread(target=self._reset_counter)
        self._reset_counter_thread.daemon = True
        self._reset_counter_thread.start()

    def _reset_counter(self):
        while True:
            with self.lock:
                self.counter = 0
            time.sleep(self.time_window)


    def add_request(self):
        with self.lock:
            if self.counter < self.capacity:
                self.counter += 1
                return True
            else:
                return False
            
    def get_capacity(self):
        return self.capacity   

    def get_counter(self):
        with self.lock:
            return self.counter 
    


class RateLimiter(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.ratelimiterMap = {}

    def add_user(self, user_id, capacity, time_window):
        with self.lock:
            if user_id not in self.ratelimiterMap:
                self.ratelimiterMap[user_id] = FixedWindowCounter(capacity, time_window)
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
                return self.ratelimiterMap[user_id].add_request()
            else:
                print("User does not exist")
                return False
            

# Test the rate limiter

def worker(limiter, request_id, user_id):
    if limiter.shouldAllowServiceCall(user_id):
        print(f"Service call allowed for {request_id}. Current counter is {limiter.ratelimiterMap[user_id].get_counter()}.")
    else:
        print(f"Service call denied for {request_id}.")

def test_concurrent_requests():
    limiter = RateLimiter()
    limiter.add_user("user1", 5, 1)

    # Create 5 worker threads that will try to add requests to the queue concurrently
    threads = [threading.Thread(target=worker, args=(limiter, i, "user1")) for i in range(8)]

    # Start the threads
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Wait for 1 second
    time.sleep(1)

    more_threads = [threading.Thread(target=worker, args=(limiter, i, "user1")) for i in range(8, 15)]

    # Start the threads again
    for thread in more_threads:
        thread.start()

    for thread in more_threads:
        thread.join()

test_concurrent_requests()