import random
import time
import os
import string
import threading
from contextlib import contextmanager
RED = "\033[38;2;204;103;102m"
RESET = "\033[0m"
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')
def generate_random_code():
    first = random.choice(string.digits + string.ascii_uppercase)
    second = random.choice(string.digits + string.ascii_uppercase)
    return f"{first}{second}"
def generate_random_matrix():
    return [[generate_random_code() for _ in range(4)] for _ in range(5)]
def display_matrix():
    matrix = generate_random_matrix()
    for row in matrix:
        for cell in row:
            if random.random() < 0.3:
                print(f"\033[43m\033[93m{cell:^4}\033[0m", end=" ")
            else:
                print(f"{RED}{cell:^4}{RESET}", end=" ")
        print()
    print()
def loading_simulation(duration=5):
    start_time = time.time()
    while time.time() - start_time < duration:
        display_matrix()
        time.sleep(0.2)
if __name__ == "__main__":
    loading_simulation()
def show_loading_screen(loading_message=None, duration=None, print_ascii_art=None, YELLOW="\033[93m"):
    import sys
    start_time = time.time()
    while time.time() - start_time < (duration if duration is not None else 2):
        clear_screen()
        if print_ascii_art:
            print_ascii_art()
        if loading_message:
            print(f"\n{YELLOW}[~] {loading_message}{RESET}\n")
        matrix = generate_random_matrix()
        for row in matrix:
            for cell in row:
                if random.random() < 0.3:
                    print(f"\033[43m\033[93m{cell:^4}\033[0m", end=" ")
                else:
                    print(f"{RED}{cell:^4}{RESET}", end=" ")
            print()
        print()
        sys.stdout.flush()
        time.sleep(0.2)
@contextmanager
def loading_state(message=None, duration=2, print_ascii_art=None):
    stop_flag = [False]
    def animate():
        while not stop_flag[0]:
            show_loading_screen(loading_message=message, duration=0.8, print_ascii_art=print_ascii_art)
    t = threading.Thread(target=animate)
    t.start()
    try:
        yield
    finally:
        stop_flag[0] = True
        t.join()
        clear_screen()
        if print_ascii_art:
            print_ascii_art()