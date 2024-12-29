import pygame
import os
import random
import time
import keyboard
import concurrent.futures
import TwitchPlays_Connection  # Import your Twitch connection module here

# Initialize pygame
pygame.init()

# Load images
image_files = ['images/image1.png', 'images/image2.png']  # Replace with your image filenames
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

# Twitch-related variables
TWITCH_CHANNEL = 'name here'  # Replace with your Twitch username. Must be all lowercase.
USER_INFO = {
    'name here': {'image_index': 1, 'text': 'Hello, name here!', 'image': images[0], 'first_chat': True},
    'nightbot': {'image_index': 2, 'text': 'Welcome in nightbot. Here is a plaeholder image', 'image': images[1], 'first_chat': True}
}
MESSAGE_RATE = 0.5
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

# Keep track of users who have already chatted
chatted_users = set()

def handle_message(message):
    global chatted_users
    username = message['username'].lower()

    if username in USER_INFO and username not in chatted_users:
        user_info = USER_INFO[username]
        text = user_info['text']
        image = user_info['image']

        if user_info['first_chat']:
            user_info['first_chat'] = False
            chatted_users.add(username)  # Mark the user as having chatted for the first time

        # Display the text
        text_surface = font.render(text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))

        # Clear the screen
        screen.fill((0, 0, 0))
        # Draw the text and image
        screen.blit(text_surface, text_rect)
        image_rect = image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3))
        screen.blit(image, image_rect)
        pygame.display.flip()

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

            # Check if the user has already chatted
            if message['username'].lower() in chatted_users:
                continue

            # Control the frame rate
            pygame.time.Clock().tick(30)  # Limit to 30 frames per second

# Quit pygame
pygame.quit()