import pygame
import random
import psycopg2

pygame.init()

# Colors and sizes
blue = (50, 153, 213)
black = (0, 0, 0)
red = (213, 50, 80)
yellow = (255, 255, 0)
green = (0, 255, 0)
white = (255, 255, 255)
grey = (200, 200, 200)
pink = (255, 105, 180)

width, height = 600, 450
snake_block = 10
food_types = ["red_food", "green_food", "yellow_food"]
button_width, button_height = 80, 30
button_margin = 10

# Screen setup
display = pygame.display.set_mode((width, height))
pygame.display.set_caption("Snake Game")
clock = pygame.time.Clock()
font_style = pygame.font.SysFont("Verdana", 20)

# Database setup
try:
    conn = psycopg2.connect(host="localhost", dbname="postgres", user="postgres", password="inkar10", port=5432)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_score (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        level INTEGER,
        score INTEGER
    )""")
    conn.commit()
except psycopg2.Error as e:
    print(f"Database error: {e}")
    pygame.quit()
    quit()

def save_game():
    if user_id:
        try:
            cur.execute("INSERT INTO user_score (user_id, level, score) VALUES (%s, %s, %s)", (user_id, level, score))
            conn.commit()
            print("Game saved!")
            pygame.quit()
            quit()
        except psycopg2.Error as e:
            print(f"Save error: {e}")

def get_user_name():
    input_box = pygame.Rect(width // 2 - 100, height // 2 - 20, 200, 40)
    text = ''
    active = True
    while active:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    active = False
                    return text
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                else:
                    text += event.unicode

        display.fill(black)
        msg = font_style.render("Enter your name:", True, white)
        display.blit(msg, (width // 2 - msg.get_width() // 2, height // 2 - 60))
        pygame.draw.rect(display, white, input_box, 2)
        txt = font_style.render(text, True, white)
        display.blit(txt, (input_box.x + 5, input_box.y + 5))
        input_box.w = max(200, txt.get_width() + 10)
        pygame.display.flip()

user_name = get_user_name()
user_id = None
level = 1
score = 0
new_score = 0


def draw_button(text, x, y, width, height, color, hover_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    rect = pygame.Rect(x, y, width, height)
    hovered = rect.collidepoint(mouse)
    pygame.draw.rect(display, hover_color if hovered else color, rect)
    button_text = font_style.render(text, True, black)
    text_rect = button_text.get_rect(center=rect.center)
    display.blit(button_text, text_rect)

    if hovered and click[0] == 1 and action is not None:
        pygame.time.delay(200) 
        action()


def print_snake(block, snake_list):
    for segment in snake_list:
        pygame.draw.rect(display, pink, [segment[0], segment[1], block, block])

def generate_food(snake_list):
    while True:
        f_type = random.choice(food_types)
        x = random.randrange(0, width - snake_block, snake_block)
        y = random.randrange(0, height - 2 * button_height - 2 * button_margin, snake_block)
        if [x, y] not in snake_list:
            return x, y, f_type

def pause_screen():
        pause_text = font_style.render("Пауза. Нажмите P чтобы продолжить", True, white)
        display.blit(pause_text, (width // 5, height // 2))
        pygame.display.update()
try:
    cur.execute("SELECT id FROM users WHERE name = %s", (user_name,))
    result = cur.fetchone()
    if result:
        user_id = result[0]
        cur.execute("SELECT level, score FROM user_score WHERE user_id = %s ORDER BY id DESC LIMIT 1", (user_id,))
        last = cur.fetchone()
        if last:
            level, score = last
    else:
        cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING id", (user_name,))
        user_id = cur.fetchone()[0]
        conn.commit()
except psycopg2.Error as e:
    print(f"User error: {e}")
    pygame.quit()
    if conn:
        conn.close()
    quit()

print(f"Welcome, {user_name}! Level: {level}, Score: {score}")

# Game variables
paused = False
running = True
x1, y1 = width / 2, height // 2 - 50
x1_change, y1_change = 0, 0
snake_list = []
snake_length = 1
speed = 10 + (level - 1) * 2
food_x, food_y, food_type = generate_food(snake_list)
timer = pygame.USEREVENT + 1
time_active = False
visible = False

# Save button position
save_button_x = width - button_width - button_margin
save_button_y = button_margin


while running:
    display.fill(black)
    score_text = font_style.render(f"Score: {score}  Level: {level}", True, white)
    display.blit(score_text, [10, 10])
    draw_button("Save", save_button_x, save_button_y, button_width, button_height, grey, white, save_game)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_game()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and x1_change == 0:
                x1_change, y1_change = -snake_block, 0
            elif event.key == pygame.K_RIGHT and x1_change == 0:
                x1_change, y1_change = snake_block, 0
            elif event.key == pygame.K_UP and y1_change == 0:
                x1_change, y1_change = 0, -snake_block
            elif event.key == pygame.K_DOWN and y1_change == 0:
                x1_change, y1_change = 0, snake_block
            elif event.key == pygame.K_p:
                paused = not paused
            elif event.key == pygame.K_s:
                save_game()

    if paused:
        paused_text = font_style.render("Game Paused - Press P to Resume", True, white)
        display.blit(paused_text, (width // 2 - paused_text.get_width() // 2, height // 2))
        pygame.display.update()
        clock.tick(5)
        continue

    # ----- Игровая логика -----
    x1 += x1_change
    y1 += y1_change

    head_rect = pygame.Rect(x1, y1, snake_block, snake_block)
    food_rect = pygame.Rect(food_x, food_y, snake_block, snake_block)
    if head_rect.colliderect(food_rect):
        visible = False
        if food_type == "red_food":
            score += 1
        elif food_type == "yellow_food":
            score += 2
        elif food_type == "green_food":
            score += 3
        snake_length += 1
        food_x, food_y, food_type = generate_food(snake_list)
        visible = True
        time_active = False
        if score - 10 >= new_score:
            level += 1
            speed += 2
            new_score = score

    if food_type == "red_food":
        pygame.draw.rect(display, red, [food_x, food_y, snake_block, snake_block])
    elif food_type == "yellow_food":
        pygame.draw.rect(display, yellow, [food_x, food_y, snake_block, snake_block])
    elif food_type == "green_food":
        pygame.draw.rect(display, green, [food_x, food_y, snake_block, snake_block])

    if x1 < 0 or x1 >= width or y1 < 0 or y1 >= height - 2 * button_height - 2 * button_margin:
        save_game()
        running = False

    snake_head = [x1, y1]
    snake_list.append(snake_head)
    if len(snake_list) > snake_length:
        del snake_list[0]
    if snake_head in snake_list[:-1]:
        save_game()
        running = False

    print_snake(snake_block, snake_list)
    pygame.display.update()
    clock.tick(speed)


pygame.quit()
if conn:
    cur.close()
    conn.close()
