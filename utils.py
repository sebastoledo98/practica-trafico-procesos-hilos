from datetime import datetime
import multiprocessing

def print_safe(lock: multiprocessing.Lock, message: str) -> None:
    with lock:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
