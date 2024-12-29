import pygame
import os
import random
import time
import keyboard
import concurrent.futures
import TwitchPlays_Connection  # Import your Twitch connection module here
import pyttsx3  # Import the TTS library

# Initialize pygame
pygame.init()

# Load images
image_files = ['images/image1.png', 'images/image2.png', 'images/image3.png', 'images/image4.png', 'images/image5.png', 'images/image6.png']  # Replace with your image filenames
images = [pygame.image.load(file) for file in image_files]
# Resize all images to the same size (300 by 300 pixels)
image_size = (300, 300)
images = [pygame.transform.scale(image, image_size) for image in images]

# Load font
font = pygame.font.Font(None, 36)

# Set up the pygame display window
SCREEN_WIDTH = 800  # Adjust as needed
SCREEN_HEIGHT = 600  # Adjust as needed
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Chat and Image Viewer')  # Adjust the title as needed

# Initialize TTS engine
tts_engine = pyttsx3.init()

# Twitch-related variables
TWITCH_CHANNEL = 'averygreenbanana'  # Replace with your Twitch username. Must be all lowercase.
USER_INFO = {
    'averygreenbanana': {'image_index': 1, 'image': images[0], 'message': None, 'last_tts_time': 0},
    'hitoyorumisa': {'image_index': 2, 'image': images[1], 'message': None, 'last_tts_time': 0},
    'rollinsealvt': {'image_index': 3, 'image': images[2], 'message': None, 'last_tts_time': 0},
    'yomitsu_u': {'image_index': 4, 'image': images[3], 'message': None, 'last_tts_time': 0},
    'dinollion': {'image_index': 5, 'image': images[4], 'message': None, 'last_tts_time': 0},
    'zodiacktv': {'image_index': 6, 'image': images[4], 'message': None, 'last_tts_time': 0},
}
MESSAGE_RATE = 0.5
TTS_COOLDOWN = 40  # 20-second cooldown for TTS
MAX_QUEUE_LENGTH = 50
MAX_WORKERS = 100
last_time = time.time()
message_queue = []
thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
active_tasks = []

# An optional count down before starting, so you have time to load up the game
countdown = 0
while countdown > 0:
    print(countdown)
    countdown -= 1
    time.sleep(1)

# Initialize Twitch connection (assumed to be in the TwitchPlays_Connection module)
t = TwitchPlays_Connection.Twitch()
t.twitch_connect(TWITCH_CHANNEL)

def handle_message(message):
    username = message['username'].lower()

    if username in USER_INFO:
        user_info = USER_INFO[username]
        user_info['message'] = message['message']

        # Check TTS cooldown
        current_time = time.time()
        if current_time - user_info['last_tts_time'] >= TTS_COOLDOWN:
            # Display the text
            text = user_info['message']
            text_surface = font.render(text, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))

            # Clear the screen
            screen.fill((255, 0, 128))
            # Draw the text and image
            screen.blit(text_surface, text_rect)
            image_rect = user_info['image'].get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
            screen.blit(user_info['image'], image_rect)
            pygame.display.flip()

            # Read out the message using TTS
            tts_engine.say(text)
            tts_engine.runAndWait()

            # Update last TTS time
            user_info['last_tts_time'] = current_time

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Check for new messages
    new_messages = t.twitch_receive_messages()
    if new_messages:
        message_queue += new_messages
        message_queue = message_queue[-MAX_QUEUE_LENGTH:]

    messages_to_handle = []
    if not message_queue:
        last_time = time.time()
    else:
        r = 1 if MESSAGE_RATE == 0 else (time.time() - last_time) / MESSAGE_RATE
        n = int(r * len(message_queue))
        if n > 0:
            messages_to_handle = message_queue[0:n]
            del message_queue[0:n]
            last_time = time.time()

    # If user presses Shift+Backspace, automatically end the program
    if keyboard.is_pressed('shift+backspace'):
        exit()

    # Handle Twitch chat messages
    if not messages_to_handle:
        continue
    else:
        for message in messages_to_handle:
            if len(active_tasks) <= MAX_WORKERS:
                active_tasks.append(thread_pool.submit(handle_message, message))
            else:
                print(f'WARNING: active tasks ({len(active_tasks)}) exceeds number of workers ({MAX_WORKERS}). ({len(message_queue)} messages in the queue)')

            # Control the frame rate
            pygame.time.Clock().tick(30)  # Limit to 30 frames per second

# Quit pygame
pygame.quit()
