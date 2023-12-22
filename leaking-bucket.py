"""An implementation of the leaking bucket algorithm for rate limiting"""
import time
import threading

class LeakingBucket(object):

    # capacity is the queue size in requests
    # process_rate is the rate in requests/second that the requests from the queue will be processed in
    def __init__(self, capacity, process_rate):
        self.capacity = capacity
        self.queue = []
        self.process_rate = process_rate
        self.timestamp = time.time()
        self.lock = threading.Lock()

        # Start a separate thread that processes requests from the queue at a fixed rate
        self._process_thread = threading.Thread(target=self._process_request)
        self._process_thread.daemon = True
        self._process_thread.start()

    def _process_request(self):
        while True:
            with self.lock:
                if self.queue:
                    self.queue.pop(0)
            time.sleep(1/self.process_rate)

    def add_request(self, request_id):
        with self.lock:
            if len(self.queue) < self.capacity:
                self.queue.append(str(time.time()) + '_' + request_id)
                return True
            else:
                return False
        
    def get_capacity(self):
        return self.capacity
    
    def get_queue_size(self):
        with self.lock:
            return len(self.queue)
    

class RateLimiter(object):
    
    def __init__(self):
        self.lock = threading.Lock()
        self.ratelimiterMap = {}

    def add_user(self, user_id, capacity, process_rate):
        with self.lock:
            if user_id not in self.ratelimiterMap:
                self.ratelimiterMap[user_id] = LeakingBucket(capacity, process_rate)
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
                return self.ratelimiterMap[user_id].add_request(request_id)
            else:
                print("User does not exist")
                return False
            

    

# Test the rate limiter            

def worker(limiter, request_id, user_id):
    if limiter.shouldAllowServiceCall(request_id, user_id):
        print(f"Service call allowed for {request_id}. Current queue size is {limiter.ratelimiterMap[user_id].get_queue_size()}.")
    else:
        print(f"Service call denied for {request_id}.")

def test_concurrent_requests():

    # Create a rate limiter
    limiter = RateLimiter()

    # Add a user with a capacity of 5 tokens and a fill rate of 2 tokens/second
    limiter.add_user("user1", 5, 2)

    # Create 5 worker threads that will try to add requests to the queue concurrently
    threads = [threading.Thread(target=worker, args=(limiter, str(i), "user1")) for i in range(5)]

    # Start the threads
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Wait for 2 seconds
    time.sleep(2)

    more_threads = [threading.Thread(target=worker, args=(limiter, str(i), "user1")) for i in range(5, 10)]

    # Start the threads again
    for thread in more_threads:
        thread.start()

    for thread in more_threads:
        thread.join()

test_concurrent_requests()