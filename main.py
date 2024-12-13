import pygame
import random
import sys
import sqlite3
import time
import os
USER_STATS_FOLDER = "user_stats"
os.makedirs(USER_STATS_FOLDER, exist_ok=True)


conn_users = sqlite3.connect('users.db')
cursor_users = conn_users.cursor()
cursor_users.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
conn_users.commit()

conn_scores = sqlite3.connect('scores.db')
cursor_scores = conn_scores.cursor()
cursor_scores.execute('''CREATE TABLE IF NOT EXISTS scores (name TEXT, time REAL)''')
conn_scores.commit()

def save_user_stats(username, elapsed_time):
    user_db_path = os.path.join(USER_STATS_FOLDER, f"{username}.db")
    conn_user = sqlite3.connect(user_db_path)
    c_user = conn_user.cursor()
    c_user.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time REAL,
            date TEXT
        )
    ''')
    c_user.execute(
        "INSERT INTO stats (time, date) VALUES (?, ?)",
        (elapsed_time, time.strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn_user.commit()
    conn_user.close()


WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
ROWS, COLS = HEIGHT // TILE_SIZE, WIDTH // TILE_SIZE
MINES_COUNT = 20

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Сапер")
font = pygame.font.Font(None, 36)

flag_image = pygame.image.load('flag.png')
mine_image = pygame.image.load('mine.png')
flag_image = pygame.transform.scale(flag_image, (TILE_SIZE, TILE_SIZE))
mine_image = pygame.transform.scale(mine_image, (TILE_SIZE, TILE_SIZE))


current_user = None

class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mine = False
        self.flagged = False
        self.revealed = False
        self.adjacent_mines = 0


def create_grid():
    grid = [[Tile(x, y) for x in range(COLS)] for y in range(ROWS)]

    mines = random.sample([tile for row in grid for tile in row], MINES_COUNT)
    for mine in mines:
        mine.mine = False

    for row in grid:
        for tile in row:
            if not tile.mine:
                tile.adjacent_mines = sum(
                    1 for i in range(max(0, tile.y - 1), min(ROWS, tile.y + 2))
                    for j in range(max(0, tile.x - 1), min(COLS, tile.x + 2))
                    if grid[i][j].mine
                )
    return grid

def draw_tiles(grid):
    for row in grid:
        for tile in row:
            rect = pygame.Rect(tile.x * TILE_SIZE, tile.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            if tile.revealed:
                pygame.draw.rect(screen, (200, 200, 200), rect)
                if tile.mine:
                    screen.blit(mine_image, rect)
                elif tile.adjacent_mines > 0:
                    text = font.render(str(tile.adjacent_mines), True, (0, 0, 0))
                    screen.blit(text, text.get_rect(center=rect.center))
            else:
                pygame.draw.rect(screen, (100, 100, 100), rect)
                if tile.flagged:
                    screen.blit(flag_image, rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

def reveal_tile(grid, x, y):
    tile = grid[y][x]
    if not tile.revealed and not tile.flagged:
        tile.revealed = True
        if tile.mine:
            game_over(grid)
        elif tile.adjacent_mines == 0:
            for i in range(max(0, y - 1), min(ROWS, y + 2)):
                for j in range(max(0, x - 1), min(COLS, x + 2)):
                    reveal_tile(grid, j, i)


def game_over(grid):
    for row in grid:
        for tile in row:
            if tile.mine:
                tile.revealed = True
    draw_tiles(grid)
    show_message("Вы попали на мину! Игра окончена.", (255, 0, 0))
    pygame.time.wait(2000)
    main_menu()

def win_game(grid, player_name, start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    save_score(player_name, elapsed_time)
    if player_name:
        save_user_stats(player_name, elapsed_time)
    draw_tiles(grid)
    show_message(f"Вы победили! Время: {elapsed_time:.2f} секунд.", (0, 255, 0))
    pygame.time.wait(2000)
    main_menu()


def save_score(name, time):
    conn_scores = sqlite3.connect('scores.db')
    c_scores = conn_scores.cursor()
    c_scores.execute("SELECT time FROM scores WHERE name = ?", (name,))
    result = c_scores.fetchone()

    if result:
        current_best_time = result[0]
        if time < current_best_time:
            c_scores.execute("UPDATE scores SET time = ? WHERE name = ?", (time, name))
    else:
        c_scores.execute("INSERT INTO scores (name, time) VALUES (?, ?)", (name, time))

    conn_scores.commit()
    conn_scores.close()



def show_message(message, color):
    text = font.render(message, True, color)
    screen.blit(text, ((WIDTH - text.get_width()) // 2, HEIGHT // 2))
    pygame.display.flip()

def main_menu():
    global current_user
    while True:
        screen.fill((255, 255, 255))
        title = font.render("Сапер", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        play_button = font.render("Играть", True, (0, 0, 0))
        play_rect = play_button.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(play_button, play_rect)

        scores_button = font.render("Рейтинги", True, (0, 0, 0))
        scores_rect = scores_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(scores_button, scores_rect)

        if current_user:
            personal_button = font.render(f"Личный кабинет ({current_user})", True, (0, 0, 0))
            personal_rect = personal_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
            screen.blit(personal_button, personal_rect)
        else:
            personal_rect = pygame.Rect(0, 0, 0, 0)

        exit_button = font.render("Выйти из игры", True, (0, 0, 0))
        exit_rect = exit_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        screen.blit(exit_button, exit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    game_loop(current_user)
                elif scores_rect.collidepoint(event.pos):
                    scores_menu()
                elif personal_rect.collidepoint(event.pos) and current_user:
                    personal_cabinet()
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()


def scores_menu():
    conn_scores = sqlite3.connect('scores.db')
    cursor_scores = conn_scores.cursor()
    cursor_scores.execute('SELECT * FROM scores ORDER BY time ASC')
    scores = cursor_scores.fetchall()
    conn_scores.close()

    while True:
        screen.fill((255, 255, 255))
        title = font.render("Рейтинги:", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        for i, (name, score) in enumerate(scores):
            score_text = font.render(f"{i + 1}. {name} - {score:.2f} секунд", True, (0, 0, 0))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + i * 30))

        back_button = font.render("Назад", True, (0, 0, 0))
        back_rect = back_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        screen.blit(back_button, back_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    main_menu()

        pygame.display.flip()

def game_loop(player_name):
    grid = create_grid()
    start_time = time.time()
    while True:
        screen.fill((255, 255, 255))
        draw_tiles(grid)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0] // TILE_SIZE, event.pos[1] // TILE_SIZE
                if event.button == 1:
                    reveal_tile(grid, x, y)
                elif event.button == 3:
                    tile = grid[y][x]
                    tile.flagged = not tile.flagged

        pygame.display.flip()

        if all(tile.revealed or tile.mine for row in grid for tile in row):
            win_game(grid, player_name, start_time)




def draw_text_input(rect, text, active):
    pygame.draw.rect(screen, (0, 0, 0), rect, 2)
    color = (200, 200, 200) if active else (255, 255, 255)
    pygame.draw.rect(screen, color, rect.inflate(-4, -4))
    text_surface = font.render(text, True, (0, 0, 0))
    screen.blit(text_surface, (rect.x + 5, rect.y + 5))


def personal_cabinet():
    global current_user
    user_db_path = os.path.join(USER_STATS_FOLDER, f"{current_user}.db")
    conn_user = sqlite3.connect(user_db_path)
    c_user = conn_user.cursor()
    c_user.execute("SELECT * FROM stats ORDER BY date DESC")
    stats = c_user.fetchall()
    conn_user.close()

    while True:
        screen.fill((255, 255, 255))
        title = font.render(f"Личный кабинет: {current_user}", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        y_offset = HEIGHT // 2 - 100
        for stat in stats[:10]:
            stat_text = font.render(f"{stat[2]} - {stat[1]:.2f} секунд", True, (0, 0, 0))
            screen.blit(stat_text, (WIDTH // 2 - stat_text.get_width() // 2, y_offset))
            y_offset += 30

        back_button = font.render("Назад", True, (0, 0, 0))
        back_rect = back_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        screen.blit(back_button, back_rect)

        logout_button = font.render("Выйти из аккаунта", True, (0, 0, 0))
        logout_rect = logout_button.get_rect(center=(WIDTH // 2, y_offset + 50))
        screen.blit(logout_button, logout_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if logout_rect.collidepoint(event.pos):
                    current_user = None
                    auth_menu()
                elif back_rect.collidepoint(event.pos):
                    main_menu()

        pygame.display.flip()

def auth_menu():
    while True:
        screen.fill((255, 255, 255))
        title = font.render("Авторизация", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        login_button = font.render("Войти", True, (0, 0, 0))
        login_rect = login_button.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(login_button, login_rect)

        register_button = font.render("Регистрация", True, (0, 0, 0))
        register_rect = register_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50))
        screen.blit(register_button, register_rect)

        exit_button = font.render("Выход", True, (0, 0, 0))
        exit_rect = exit_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        screen.blit(exit_button, exit_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if login_rect.collidepoint(event.pos):
                    login()
                elif register_rect.collidepoint(event.pos):
                    register()
                elif exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        pygame.display.flip()

def login():
    global current_user
    username = ""
    password = ""
    active_field = None

    username_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 40)
    password_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 40)
    back_button_rect = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 100, 100, 40)

    while True:
        screen.fill((255, 255, 255))
        title = font.render("Вход", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        draw_text_input(username_rect, username, active_field == "username")
        draw_text_input(password_rect, "*" * len(password), active_field == "password")

        back_button = font.render("Назад", True, (0, 0, 0))
        pygame.draw.rect(screen, (0, 0, 0), back_button_rect, 2)
        screen.blit(back_button, back_button_rect.topleft)


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if username_rect.collidepoint(event.pos):
                    active_field = "username"
                elif password_rect.collidepoint(event.pos):
                    active_field = "password"
                elif back_button_rect.collidepoint(event.pos):
                    auth_menu()
            elif event.type == pygame.KEYDOWN:
                if active_field == "username":
                    if event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
                elif active_field == "password":
                    if event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode
                if event.key == pygame.K_RETURN:
                    conn_users = sqlite3.connect('users.db')
                    cursor_users = conn_users.cursor()
                    cursor_users.execute(
                        "SELECT * FROM users WHERE username = ? AND password = ?",
                        (username, password)
                    )
                    if cursor_users.fetchone():
                        current_user = username
                        conn_users.close()
                        main_menu()
                    else:
                        conn_users.close()
                        show_message("Неверное имя пользователя или пароль.", (255, 0, 0))

        pygame.display.flip()

def register():
    username = ""
    password = ""
    active_field = None

    username_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 50, 200, 40)
    password_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2, 200, 40)
    back_button_rect = pygame.Rect(WIDTH // 2 - 50, HEIGHT // 2 + 100, 100, 40)

    while True:
        screen.fill((255, 255, 255))
        title = font.render("Регистрация", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        draw_text_input(username_rect, username, active_field == "username")
        draw_text_input(password_rect, "*" * len(password), active_field == "password")


        back_button = font.render("Назад", True, (0, 0, 0))
        pygame.draw.rect(screen, (0, 0, 0), back_button_rect, 2)
        screen.blit(back_button, back_button_rect.topleft)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if username_rect.collidepoint(event.pos):
                    active_field = "username"
                elif password_rect.collidepoint(event.pos):
                    active_field = "password"
                elif back_button_rect.collidepoint(event.pos):
                    auth_menu()
            elif event.type == pygame.KEYDOWN:
                if active_field == "username":
                    if event.key == pygame.K_BACKSPACE:
                        username = username[:-1]
                    else:
                        username += event.unicode
                elif active_field == "password":
                    if event.key == pygame.K_BACKSPACE:
                        password = password[:-1]
                    else:
                        password += event.unicode
                if event.key == pygame.K_RETURN:
                    conn_users.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                    conn_users.commit()
                    show_message("Регистрация успешна! Войдите в систему.", (0, 255, 0))
                    auth_menu()

        pygame.display.flip()

def show_message(message, color):
    text = font.render(message, True, color)
    screen.fill((255, 255, 255))
    screen.blit(text, ((WIDTH - text.get_width()) // 2, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(2000)

auth_menu()
main_menu()