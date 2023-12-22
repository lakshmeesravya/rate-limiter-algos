"""An implementation of the sliding window log algorithm for rate limiting"""
import time
import threading

class SlidingWindowLog(object):
    
        def __init__(self, capacity, time_window):
            self.capacity = capacity
            self.time_window = time_window
            self.window = []
            self.lock = threading.Lock()
    
        def add_request(self):
            with self.lock:
                self.window = [t for t in self.window if t > time.time() - self.time_window]
                if len(self.window) >= self.capacity:
                    return False
                else:
                    self.window.append(time.time())
                    return True
                
        def get_capacity(self):
            return self.capacity   
    
        def get_window_size(self):
            with self.lock:
                return len(self.window)
            

class RateLimiter(object):

    def __init__(self):
        self.lock = threading.Lock()
        self.ratelimiterMap = {}

    def add_user(self, user_id, capacity, time_window):
        with self.lock:
            if user_id not in self.ratelimiterMap:
                self.ratelimiterMap[user_id] = SlidingWindowLog(capacity, time_window)
            else:
                print("User already exists")

    def remove_user(self, user_id):
        with self.lock:
            if user_id in self.ratelimiterMap:
                del self.ratelimiterMap[user_id]
            else:
                print("User does not exist")

    def shouldAllowServiceCall(self, request_id, user_id):
        with self.lock:
            if user_id in self.ratelimiterMap:
                return self.ratelimiterMap[user_id].add_request()
            else:
                print("User does not exist")
                return False
            
# Test the rate limiter

def worker(limiter, request_id, user_id):
    if limiter.shouldAllowServiceCall(request_id, user_id):
        print(f"Service call allowed for {request_id}. Current window size is {limiter.ratelimiterMap[user_id].get_window_size()}.")
    else:
        print(f"Service call denied for {request_id}. Current window size is {limiter.ratelimiterMap[user_id].get_window_size()}.")

def test_concurrent_requests():
    
        # Create a rate limiter
        limiter = RateLimiter()
    
        # Add a user
        limiter.add_user("user1", 5, 1)

        # Create worker threads that will try to add requests to the queue concurrently
        threads = [threading.Thread(target=worker, args=(limiter, f"request{i}", "user1")) for i in range(8)]

        # Start the threads
        for thread in threads:
            thread.start() 

        for thread in threads:
            thread.join()

        time.sleep(1)

        more_threads = [threading.Thread(target=worker, args=(limiter, f"request{i}", "user1")) for i in range(8, 12)]

        for thread in more_threads:
            thread.start()

        for thread in more_threads: 
            thread.join()


test_concurrent_requests()