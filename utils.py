from datetime import datetime
import multiprocessing
import threading

def print_safe(lock, message: str) -> None:
    with lock:
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")