import pygame
import random
import sys
import mysql.connector
import time
import mysql.connector

# Настройки подключения к MySQL
DB_CONFIG = {
    'host': 'localhost',       # Хост сервера MySQL
    'user': 'root',            # Пользователь MySQL
    'password': '',            # Пароль пользователя
    'database': 'game_db',     # Имя базы данных
    'autocommit': False
}

# Функция для настройки базы данных
def setup_database(conn):
    cursor = None
    try:
        cursor = conn.cursor()

        if not conn.is_connected():
            conn.reconnect()
        conn.commit()
    except mysql.connector.Error as err:
        #print(f"Ошибка: {err}")
        if conn.is_connected():
            conn.rollback()
    finally:
        if cursor:
            cursor.close()


try:
    #подключение к базе
    conn = mysql.connector.connect(**DB_CONFIG)
    setup_database(conn)
    print("Подключено к базе данных:", conn.database)
except mysql.connector.Error as err:
    print(f"Ошибка: {err}")
finally:
    if conn.is_connected():
        conn.close()

"""Функция для подключения к базе данных."""
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    cursor.close()
    conn.close()

    conn.commit()
    cursor.close()
    conn.close()

setup_database(conn)

"""
   Сохраняет статистику игрока в таблице `stats`.
"""
def save_user_stats(username, elapsed_time):

    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        INSERT INTO stats (username, time, date) 
        VALUES (%s, %s, NOW())
    '''
    cursor.execute(query, (username, elapsed_time))

    conn.commit()
    cursor.close()
    conn.close()

"""Получение данных статистики."""
def get_stats_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT username, MIN(time) as best_time
    FROM stats
    GROUP BY username
    ORDER BY best_time ASC
    LIMIT 10;
    """
    cursor.execute(query)
    data = cursor.fetchall()

    cursor.close()
    conn.close()
    return data

def save_user_stats(username, elapsed_time):
    try:
        # подключение к базе
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # создание таблицы если не существует
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL,
                time FLOAT NOT NULL,
                Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            INSERT INTO stats (username, time)
            VALUES (%s, %s)
        ''', (username, elapsed_time))
        conn.commit()

    except mysql.connector.Error as e:
        print(f"Ошибка сохранения статистики: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Настройки игры
WIDTH, HEIGHT = 800, 600
TILE_SIZE = 40
ROWS, COLS = HEIGHT // TILE_SIZE, WIDTH // TILE_SIZE
MINES_COUNT = 50

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Сапер")
font = pygame.font.Font(None, 36)

# Загрузка и изменение размеров изображений
flag_image = pygame.image.load('flag.png')
flag_image = pygame.transform.scale(flag_image, (TILE_SIZE, TILE_SIZE))
mine_image = pygame.image.load('mine.png')
mine_image = pygame.transform.scale(mine_image, (TILE_SIZE, TILE_SIZE))


current_user = None

# Класс плитки
class Tile:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.mine = False
        self.flagged = False
        self.revealed = False
        self.adjacent_mines = 0


def create_empty_grid():
    """Создаёт пустую сетку без мин."""
    return [[Tile(x, y) for x in range(COLS)] for y in range(ROWS)]

def place_mines(grid, first_x, first_y):
    """Генерирует мины на поле, исключая клетку первого клика и соседние клетки."""
    valid_positions = [
        (tile.x, tile.y)
        for row in grid for tile in row
        if abs(tile.x - first_x) > 1 or abs(tile.y - first_y) > 1
    ]
    mines = random.sample(valid_positions, MINES_COUNT)
    for x, y in mines:
        grid[y][x].mine = True

    # Пересчитываем соседние мины
    for row in grid:
        for tile in row:
            if not tile.mine:
                tile.adjacent_mines = sum(
                    1 for i in range(max(0, tile.y - 1), min(ROWS, tile.y + 2))
                    for j in range(max(0, tile.x - 1), min(COLS, tile.x + 2))
                    if grid[i][j].mine
                )

# Функция отрисовки плиток
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

def reveal_tile(grid, x, y, is_first_click):
    """Открывает клетку. При первом клике генерирует мины."""
    global first_click_done

    # Определяем область вокруг первого клика, где не должно
    if is_first_click:
        first_click_done = True
        place_mines(grid, x, y)

    tile = grid[y][x]
    if not tile.revealed and not tile.flagged:
        tile.revealed = True
        if tile.mine:
            game_over(grid)
        elif tile.adjacent_mines == 0:
            for i in range(max(0, y - 1), min(ROWS, y + 2)):
                for j in range(max(0, x - 1), min(COLS, x + 2)):
                    reveal_tile(grid, j, i, False)
# Список всех возможных позиций для мин, исключая безопасную зону

#Создание окна с сообщением о проигрыше
def game_over(grid):
    for row in grid:
        for tile in row:
            if tile.mine:
                tile.revealed = True
    draw_tiles(grid)
    show_message("Вы попали на мину! Игра окончена.", (255, 0, 0))
    pygame.time.wait(1000)
    main_menu()

#Создание окна с сообщением о победе
def win_game(grid, player_name, start_time):
    end_time = time.time()
    elapsed_time = end_time - start_time
    if player_name:
        save_user_stats(player_name, elapsed_time)
    draw_tiles(grid)
    show_message(f"Вы победили! Время: {elapsed_time:.2f} секунд.", (0, 255, 0))
    pygame.time.wait(1000)
    main_menu()

#создание главного меню со всеми функицями
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

        # Обработка событий
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

#меню таблицы лидеров
def scores_menu():
    # Подключение к единой базе данных
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Получение лучшего времени для каждого пользователя из таблицы stats
    cursor.execute('''
        SELECT username, MIN(time) as best_time
        FROM stats
        GROUP BY username
        ORDER BY best_time ASC
    ''')
    scores = cursor.fetchall()
    conn.close()

    while True:
        screen.fill((255, 255, 255))

        # Заголовок "Рейтинги"
        title = font.render("Рейтинги:", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        # Отображение каждого результата
        for i, (username, best_time) in enumerate(scores):
            score_text = font.render(f"{i + 1}. {username} - {best_time:.2f} секунд", True, (0, 0, 0))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + i * 30))

        # Кнопка "Назад"
        back_button = font.render("Назад", True, (0, 0, 0))
        back_rect = back_button.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 150))
        screen.blit(back_button, back_rect)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    main_menu()

        pygame.display.flip()

#создание игрового процесса, логики игры, цикла
def game_loop(player_name):
    global first_click_done
    first_click_done = False

    grid = create_empty_grid()
    start_time = time.time()
    while True:
        screen.fill((255, 255, 255))
        draw_tiles(grid)

        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos[0] // TILE_SIZE, event.pos[1] // TILE_SIZE
                if event.button == 1:
                    reveal_tile(grid, x, y, not first_click_done)
                elif event.button == 3:
                    tile = grid[y][x]
                    tile.flagged = not tile.flagged

        pygame.display.flip()

        # Проверка на завершение игры
        if all(tile.revealed or tile.mine for row in grid for tile in row):
            win_game(grid, player_name, start_time)

#сообщения
def draw_text_input(rect, text, active):
    pygame.draw.rect(screen, (0, 0, 0), rect, 2)
    color = (200, 200, 200) if active else (255, 255, 255)
    pygame.draw.rect(screen, color, rect.inflate(-4, -4))
    text_surface = font.render(text, True, (0, 0, 0))
    screen.blit(text_surface, (rect.x + 5, rect.y + 5))

#личный кабинет со статистикой победных матчей
def personal_cabinet():
    global current_user

    # Подключение к базе данных
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()

    # Получение статистики пользователя
    c.execute("SELECT * FROM stats WHERE username = %s ORDER BY date DESC", (current_user,))
    stats = c.fetchall()
    conn.close()

    while True:
        screen.fill((255, 255, 255))

        title = font.render(f"Личный кабинет: {current_user}", True, (0, 0, 0))
        screen.blit(title, ((WIDTH - title.get_width()) // 2, HEIGHT // 4))

        y_offset = HEIGHT // 2 - 100
        for stat in stats[:9]:
            try:
                time_value = float(stat[2])
                date_value = stat[3]
            except (ValueError, IndexError):
                time_value = 0.0
                date_value = "Неизвестно"

            stat_text = font.render(f"{date_value} - {time_value:.2f} секунд", True, (0, 0, 0))
            screen.blit(stat_text, (WIDTH // 2 - stat_text.get_width() // 2, y_offset))
            y_offset += 30

        back_button = font.render("Назад", True, (0, 0, 0))
        back_rect = back_button.get_rect(center=(WIDTH // 2, y_offset + 80))
        screen.blit(back_button, back_rect)

        logout_button = font.render("Выйти из аккаунта", True, (0, 0, 0))
        logout_rect = logout_button.get_rect(center=(WIDTH // 2, y_offset + 30))
        screen.blit(logout_button, logout_rect)

        # Обработка событий
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

#первоначальное меню входа в аккаунт
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

        # Обработка событий
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

#Вход в аккаунт
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

        # Обработка событий
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
                #проверка полей
                if event.key == pygame.K_RETURN:
                    if not username.strip() or not password.strip():
                        show_message("Оба поля должны быть заполнены.", (255, 0, 0))
                    else:
                        #Подключение к базе данных и создание таблицы если не существует
                        conn = mysql.connector.connect(**DB_CONFIG)
                        cursor = conn.cursor()

                        # создание таблицы если не существует
                        cursor.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            username VARCHAR(255) UNIQUE NOT NULL,
                            password VARCHAR(255) NOT NULL
                        )
                        ''')

                        cursor.execute(
                            "SELECT * FROM users WHERE username = %s AND password = %s",
                            (username, password)
                        )
                        if cursor.fetchone():
                            current_user = username
                            conn.close()
                            main_menu()
                        else:
                            conn.close()
                            show_message("Неверное имя пользователя или пароль.", (255, 0, 0))

        pygame.display.flip()

#регистрация аккаунта
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

        # Обработка событий
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
                # проверка полей
                if event.key == pygame.K_RETURN:
                    if not username.strip() or not password.strip():
                        show_message("Оба поля должны быть заполнены.", (255, 0, 0))
                    else:
                        try:
                            #Подключение к базе данных и создание таблицы если не существует
                            conn = mysql.connector.connect(**DB_CONFIG)
                            cursor = conn.cursor()

                            #создание таблицы если не существует
                            cursor.execute('''
                            CREATE TABLE IF NOT EXISTS users (
                                id INT AUTO_INCREMENT PRIMARY KEY,
                                username VARCHAR(255) UNIQUE NOT NULL,
                                password VARCHAR(255) NOT NULL
                            )
                            ''')

                            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
                            if cursor.fetchone():
                                show_message("Пользователь уже существует.", (255, 0, 0))
                            else:
                                cursor.execute(
                                    "INSERT INTO users (username, password) VALUES (%s, %s)",
                                    (username, password)
                                )
                                conn.commit()
                                show_message("Регистрация успешна! Войдите в систему.", (0, 255, 0))
                                auth_menu()
                        except mysql.connector.Error as err:
                            show_message(f"Ошибка базы данных: {err}", (255, 0, 0))
                        finally:
                            if 'cursor' in locals():
                                cursor.close()
                            if 'conn' in locals() and conn.is_connected():
                                conn.close()

        pygame.display.flip()

# Функция для отображения сообщения
def show_message(message, color):
    text = font.render(message, True, color)
    screen.blit(text, ((WIDTH - text.get_width()) // 2, HEIGHT // 2))
    pygame.display.flip()
    pygame.time.wait(1000)

auth_menu()
main_menu()
