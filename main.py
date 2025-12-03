import pygame
import numpy as np
import librosa
import sys

# ------------------------
# CONSTANTS
# ------------------------
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

COLUMNS = 4
COLUMN_WIDTH = WINDOW_WIDTH // COLUMNS
SHAPE_SIZE = 50
FALL_SPEED = 300
HIT_ZONE_Y = WINDOW_HEIGHT - 100
SPAWN_OFFSET = 1.0  # seconds before beat

KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]  # keys for columns

# ------------------------
# DATA STRUCTURES
# ------------------------
class Queue:
    def __init__(self):
        self.items = []

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        return None

    def peek(self):
        if not self.is_empty():
            return self.items[0]
        return None

    def is_empty(self):
        return len(self.items) == 0

class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def is_empty(self):
        return len(self.items) == 0

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkedList:
    def __init__(self):
        self.head = None

    def add(self, data):
        node = Node(data)
        node.next = self.head
        self.head = node

    def remove(self, target):
        prev = None
        curr = self.head
        while curr:
            if curr.data == target:
                if prev:
                    prev.next = curr.next
                else:
                    self.head = curr.next
                return True
            prev = curr
            curr = curr.next
        return False

    def traverse(self):
        curr = self.head
        while curr:
            yield curr.data
            curr = curr.next

# ------------------------
# LOAD AUDIO AND DETECT BEATS
# ------------------------
AUDIO_FILE = "song.mp3"  # must be in same folder

y, sr = librosa.load(AUDIO_FILE, sr=None)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr)

# ------------------------
# INIT GAME
# ------------------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Music Beat Game")
clock = pygame.time.Clock()

# Play the song
pygame.mixer.music.load(AUDIO_FILE)
pygame.mixer.music.play()

# ------------------------
# INITIALIZE STRUCTURES
# ------------------------
beat_queue = Queue()
for t in beat_times:
    beat_queue.enqueue(t - SPAWN_OFFSET)

player_moves = Stack()
active_shapes = LinkedList()
score = 0
start_time = pygame.time.get_ticks() / 1000

# ------------------------
# MAIN GAME LOOP
# ------------------------
running = True
while running:
    dt = clock.tick(FPS) / 1000  # delta time in seconds
    current_time = pygame.time.get_ticks() / 1000 - start_time

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key in KEYS:
                col_pressed = KEYS.index(event.key)
                hit_shape = None
                for shape in active_shapes.traverse():
                    if (shape["col"] == col_pressed and
                        HIT_ZONE_Y - 50 < shape["rect"].y < HIT_ZONE_Y + 50 and
                        not shape["hit"]):
                        hit_shape = shape
                        break

                if hit_shape:
                    hit_shape["hit"] = True
                    hit_shape["hit_timer"] = 0.2
                    score += 1
                    player_moves.push(("HIT", hit_shape))
                else:
                    player_moves.push(("MISS", None))

            if event.key == pygame.K_u and not player_moves.is_empty():
                last_move = player_moves.pop()
                if last_move[0] == "HIT":
                    score -= 1
                    last_move[1]["hit"] = False

    # ------------------------
    # SPAWN SHAPES FROM BEAT QUEUE
    # ------------------------
    while not beat_queue.is_empty() and beat_queue.peek() <= current_time:
        beat_queue.dequeue()
        col = np.random.randint(0, COLUMNS)
        x = col * COLUMN_WIDTH + COLUMN_WIDTH // 2 - SHAPE_SIZE // 2
        y = -SHAPE_SIZE
        shape = {"rect": pygame.Rect(x, y, SHAPE_SIZE, SHAPE_SIZE),
                 "col": col, "hit": False, "hit_timer": 0}
        active_shapes.add(shape)

    # ------------------------
    # UPDATE SHAPES
    # ------------------------
    to_remove = []
    for shape in active_shapes.traverse():
        shape["rect"].y += int(FALL_SPEED * dt)
        if shape.get("hit"):
            shape["hit_timer"] -= dt
        if shape["rect"].y > WINDOW_HEIGHT or (shape.get("hit") and shape["hit_timer"] <= 0):
            to_remove.append(shape)

    for shape in to_remove:
        active_shapes.remove(shape)

    # ------------------------
    # DRAW
    # ------------------------
    screen.fill((0, 0, 0))

    # Draw columns
    for i in range(1, COLUMNS):
        pygame.draw.line(screen, (50, 50, 50), (i * COLUMN_WIDTH, 0), (i * COLUMN_WIDTH, WINDOW_HEIGHT), 2)
    pygame.draw.line(screen, (255, 255, 255), (0, HIT_ZONE_Y), (WINDOW_WIDTH, HIT_ZONE_Y), 2)

    # Draw shapes
    for shape in active_shapes.traverse():
        color = (0, 255, 0) if shape["hit"] else (0, 0, 255)
        pygame.draw.rect(screen, color, shape["rect"])

    # Draw score
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    screen.blit(score_text, (10, 10))

    pygame.display.flip()

pygame.quit()
sys.exit()
