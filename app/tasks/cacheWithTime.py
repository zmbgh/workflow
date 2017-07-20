from functools import wraps
import time
def cache(timeout=300):
    def deco(func):
        memo = {}
        times = {}
        @wraps(func)
        def _wrapper(*args):
            res = memo.get(args, None)
            if res is not None and time.time() - times[args] < timeout:
                return res
            else:
                res = func(*args)
                memo[args] = res
                times[args] = time.time()
            return res
        return _wrapper
    return deco



# def a(a):
#     time.sleep(2)
#     print "in function"
#     import os
#     os.system('date')
#     return 10

