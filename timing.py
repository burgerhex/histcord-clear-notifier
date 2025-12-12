import time


class Timer:
    def __init__(self, loading_message, done_format_func=None):
        self.loading_message = loading_message
        self.done_format_func = done_format_func if done_format_func is not None else lambda d: f"Done in {d:.3f} sec!"
        self.start_time = None

    def __enter__(self):
        print(self.loading_message, end="")
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time

        print(self.done_format_func(duration))

        return False