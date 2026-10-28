"""Игра «Изгиб Питона» — классическая змейка на Pygame.

Змейка ползёт по полю, ест яблоки и растёт, проходит сквозь границы
поля, а после самоукуса игра начинается заново. Управление — стрелками,
выход — Esc или закрытие окна.
"""
from random import choice

import pygame

# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Центральная ячейка поля — отсюда змейка начинает движение:
SCREEN_CENTER = (GRID_WIDTH // 2 * GRID_SIZE, GRID_HEIGHT // 2 * GRID_SIZE)

# Все ячейки поля — из свободных выбирается позиция яблока:
ALL_CELLS = {
    (x * GRID_SIZE, y * GRID_SIZE)
    for x in range(GRID_WIDTH)
    for y in range(GRID_HEIGHT)
}

# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Новое направление по нажатой клавише и текущему направлению.
# Развернуться назад змейка не может, поэтому стрелка срабатывает,
# только если змейка движется поперёк неё:
TURNS = {
    (pygame.K_UP, LEFT): UP,
    (pygame.K_UP, RIGHT): UP,
    (pygame.K_DOWN, LEFT): DOWN,
    (pygame.K_DOWN, RIGHT): DOWN,
    (pygame.K_LEFT, UP): LEFT,
    (pygame.K_LEFT, DOWN): LEFT,
    (pygame.K_RIGHT, UP): RIGHT,
    (pygame.K_RIGHT, DOWN): RIGHT,
}

# Сколько первых сегментов, считая голову, змейка не может укусить.
# Чтобы врезаться в своё тело, змейке нужно описать кольцо, а самое
# короткое кольцо из клеток — квадрат 2×2. Поэтому змейка короче пяти
# сегментов укусить себя не может.
SAFE_SEGMENTS = 4

# Цвет фона - черный:
BOARD_BACKGROUND_COLOR = (0, 0, 0)

# Цвет границы ячейки
BORDER_COLOR = (93, 216, 228)

# Цвет яблока
APPLE_COLOR = (255, 0, 0)

# Цвет змейки
SNAKE_COLOR = (0, 255, 0)

# Скорость движения змейки:
SPEED = 20

# Настройка игрового окна:
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pygame.display.set_caption('Змейка')

# Настройка времени:
clock = pygame.time.Clock()


class GameObject:
    """Базовый класс игровых объектов: позиция, цвет и отрисовка."""

    def __init__(self, body_color=None):
        """Ставит объект в центр поля и задаёт ему цвет."""
        self.position = SCREEN_CENTER
        self.body_color = body_color

    def draw(self):
        """Отрисовывает объект. Переопределяется в дочерних классах."""
        pass

    def draw_cell(self, position, color=None, border=True):
        """Закрашивает ячейку поля цветом объекта или переданным цветом.

        Ячейки объектов обводятся рамкой. Чтобы стереть ячейку, её
        заливают цветом фона без рамки.
        """
        rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, color or self.body_color, rect)
        if border:
            pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


class Apple(GameObject):
    """Яблоко — занимает одну случайную ячейку, свободную от змейки."""

    def __init__(self, occupied_positions=()):
        """Задаёт цвет яблока и кладёт его в свободную ячейку."""
        super().__init__(APPLE_COLOR)
        self.randomize_position(occupied_positions)

    def randomize_position(self, occupied_positions=()):
        """Переносит яблоко в случайную ячейку вне занятых позиций."""
        self.position = choice(tuple(ALL_CELLS - set(occupied_positions)))

    def draw(self):
        """Отрисовывает яблоко."""
        self.draw_cell(self.position)


class Snake(GameObject):
    """Змейка — список позиций сегментов, начиная с головы."""

    def __init__(self):
        """Создаёт змейку из одной головы, ползущую вправо."""
        super().__init__(SNAKE_COLOR)
        self.reset(direction=RIGHT)

    def reset(self, direction=None):
        """Возвращает змейку в начальное состояние — голову в центре поля.

        Если направление не задано, оно выбирается случайно.
        """
        self.length = 1
        self.positions = [self.position]
        self.direction = direction or choice((UP, DOWN, LEFT, RIGHT))
        self.next_direction = None
        self.last = None

    def update_direction(self):
        """Применяет направление, выбранное нажатием клавиши."""
        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

    def get_head_position(self):
        """Возвращает позицию головы змейки."""
        return self.positions[0]

    def move(self):
        """Сдвигает змейку на одну ячейку в текущем направлении.

        Новая голова добавляется в начало списка. Если змейка не выросла,
        последний сегмент удаляется и запоминается в last, чтобы стереть
        его с поля. За краем поля змейка появляется с противоположной
        стороны.
        """
        head_x, head_y = self.get_head_position()
        dx, dy = self.direction
        new_head = (
            (head_x + dx * GRID_SIZE) % SCREEN_WIDTH,
            (head_y + dy * GRID_SIZE) % SCREEN_HEIGHT,
        )
        self.positions.insert(0, new_head)
        if len(self.positions) > self.length:
            self.last = self.positions.pop()
        else:
            self.last = None

    def bites_itself(self):
        """Проверяет, врезалась ли голова змейки в её тело."""
        return self.get_head_position() in self.positions[SAFE_SEGMENTS:]

    def draw(self):
        """Стирает след хвоста и рисует голову на новом месте.

        Остальные сегменты нарисованы на прошлых шагах, поэтому всё тело
        не перерисовывается. След стирается первым: голова могла занять
        ячейку, которую только что освободил хвост.
        """
        if self.last:
            self.draw_cell(self.last, BOARD_BACKGROUND_COLOR, border=False)
        self.draw_cell(self.get_head_position())


def handle_keys(game_object):
    """Обрабатывает нажатия клавиш и закрытие окна.

    Стрелки задают змейке следующее направление движения, а Esc
    и закрытие окна завершают игру.
    """
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (
            event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
        ):
            pygame.quit()
            raise SystemExit
        if event.type == pygame.KEYDOWN:
            game_object.next_direction = TURNS.get(
                (event.key, game_object.direction),
                game_object.next_direction
            )


def main():
    """Создаёт игровые объекты и запускает основной цикл игры."""
    # Инициализация PyGame:
    pygame.init()
    snake = Snake()
    apple = Apple(snake.positions)
    record = 0
    screen.fill(BOARD_BACKGROUND_COLOR)

    while True:
        clock.tick(SPEED)
        handle_keys(snake)
        snake.update_direction()
        snake.move()

        if snake.get_head_position() == apple.position:
            snake.length += 1
            apple.randomize_position(snake.positions)
        elif snake.bites_itself():
            snake.reset()
            apple.randomize_position(snake.positions)
            screen.fill(BOARD_BACKGROUND_COLOR)

        if snake.length > record:
            record = snake.length
            pygame.display.set_caption(
                f'Змейка. Рекорд: {record}. Выход: Esc'
            )

        # Яблоко рисуется после змейки: оно может оказаться в ячейке,
        # которую змейка сейчас стирает за хвостом.
        snake.draw()
        apple.draw()
        pygame.display.update()


if __name__ == '__main__':
    main()
