import pygame
import time
import pygame.mixer

pygame.init()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
world_width = 2100  # Новая ширина мира
world_height = 800  # Новая высота мира
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("платформер")

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.speed = 10
        self.direction = direction

    def update(self, enemies, running):
        if self.direction == 'left':
            self.rect.x -= self.speed
        elif self.direction == 'right':
            self.rect.x += self.speed

        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self, all_sprites, bullets):
        super().__init__()
        width = 100
        height = 100
        new_size = (width, height)
        self.run_animations = [
            pygame.transform.scale(pygame.image.load('pngwing.com.png').convert_alpha(), new_size)]
        self.idx = 0
        self.image = self.run_animations[self.idx]
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = SCREEN_HEIGHT - 100
        self.vx = 0
        self.vy = 0
        self.is_jumping = False
        self.double_jump = False
        self.last_shot_time = 0
        self.shoot_cooldown = 500
        self.health = 100
        self.all_sprites = all_sprites
        self.bullets = bullets
        self.can_double_jump = True
        self.direction = 1
        self.hit_cooldown = 1.0
        self.last_hit_time = 0

    def update(self, enemies, running):
        self.vx = 0
        self.vy += 0.75
        current_time = time.time()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.vx = -10
            self.direction = -1
        if keys[pygame.K_d]:
            self.vx = 10
            self.direction = 1

        elif self.vx == 0:
            self.idx = 0
            if self.direction == -1:
                self.image = pygame.transform.flip(self.run_animations[self.idx], True, False)
            else:
                self.image = self.run_animations[self.idx]
        else:
            self.idx = (self.idx + 1) % len(self.run_animations)
            if self.direction == -1:
                self.image = pygame.transform.flip(self.run_animations[self.idx], True, False)
            else:
                self.image = self.run_animations[self.idx]


        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rect.y >= SCREEN_HEIGHT - 50:
            self.rect.y = SCREEN_HEIGHT - 50
            self.is_jumping = False
            self.can_double_jump = True

        hit_enemies = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in hit_enemies:
            self.health -= 10
            self.last_hit_time = current_time
            if self.health <= 0:
                running[0] = False
                return 'dead'

        self.idx = (self.idx + 1) % len(self.run_animations)
        if self.direction == -1:
            self.image = pygame.transform.flip(self.run_animations[self.idx], True, False)
        else:
            self.image = self.run_animations[self.idx]


class InvisibleWall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height), pygame.SRCALPHA, 32).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))


class PauseMenu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.paused = False
        self.menu_items = ['Continue', 'Quit']
        self.selected = 0

    def display_menu(self):
        self.screen.fill((50, 50, 50))
        for index, item in enumerate(self.menu_items):
            text = self.font.render(item, True, WHITE)
            position = (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + 30 * index)
            self.screen.blit(text, position)
        pygame.display.flip()

    def check_events(self, running):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.paused = False
                running[0] = False
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.menu_items)
                elif event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.menu_items)
                elif event.key == pygame.K_RETURN:
                    if self.selected == 0:  # Continue
                        self.paused = False
                    elif self.selected == 1:  # Quit
                        self.paused = False
                        running[0] = False  # Выставляем флаг для завершения игрового уровня, выхода в меню

    def pause(self, running):
        self.paused = True
        while self.paused:
            self.display_menu()
            self.check_events(running)


class Camera:
    def __init__(self, width, height):
        self.camera_func = self.camera_configure
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, entity):
        return entity.rect.move(self.state.topleft)

    def update(self, target):
        # Центрирование камеры на игроке
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # Ограничение прокрутки по размеру мира
        x = min(0, x)  # Ограничение слева
        y = min(0, y)  # Ограничение сверху
        x = min(max(x, -(self.state.width - SCREEN_WIDTH)), 0)
        y = min(max(y, -(self.state.height - SCREEN_HEIGHT)), 0)

        self.state = pygame.Rect(x, y, self.state.width, self.state.height)

    def camera_configure(self, camera, target_rect):
        l, t, _, _ = target_rect
        _, _, w, h = camera
        l, t = -l + SCREEN_WIDTH / 2, -t + SCREEN_HEIGHT / 2

        # limit scrolling to map size
        l = min(0, l)  # left
        l = max(-(camera.width - SCREEN_WIDTH), l)  # right
        t = max(-(camera.height - SCREEN_HEIGHT), t)  # bottom
        t = min(0, t)  # top

        return pygame.Rect(l, t, w, h)

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.image.load('d7300adb552de6e.png').convert_alpha()  # Загрузка изображения платформы
        self.image = pygame.transform.scale(self.image, (width, height))  # Изменение размера изображения в соответствии с платформой
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        ENEMY_SIZE = (200, 200)
        image = pygame.image.load('ufo_PNG71651.png').convert_alpha()
        self.image = pygame.transform.scale(image, ENEMY_SIZE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed

    def update(self, *args):
        self.rect.x += self.speed
        if self.rect.right > SCREEN_WIDTH or self.rect.left < 0:
            self.speed = -self.speed

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.Font(None, 36)
        self.running = True
        self.selected = 0  # Current selection in the menu
        self.menu_items = ['Level 1', 'Level 2', 'Exit']

    def display_menu(self):
        self.screen.fill(BLACK)
        for index, item in enumerate(self.menu_items):
            if index == self.selected:
                menu_text = self.font.render(f"> {item}", True, WHITE)
            else:
                menu_text = self.font.render(item, True, WHITE)
            self.screen.blit(menu_text, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 30 * index))
        pygame.display.flip()

    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.selected = (self.selected + 1) % len(self.menu_items)
                elif event.key == pygame.K_UP:
                    self.selected = (self.selected - 1) % len(self.menu_items)
                elif event.key == pygame.K_RETURN:
                    return self.menu_items[self.selected]
        return None

def draw_background(screen, image_path, camera):
    background = pygame.image.load('8d1419edf69da59037c58cbbd49c9424.jpg').convert()
    background_rect = background.get_rect()
    background_rect.topleft = (0, 0)

    background_rect = background_rect.move(camera.state.topleft)

    screen.blit(background, background_rect)

def level_1():
    global player
    camera = Camera(world_width, world_height)
    draw_background(screen, '8d1419edf69da59037c58cbbd49c9424.jpg', camera)

    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    pygame.mixer.init()

    player = Player(all_sprites, bullets)
    player.rect.x += 150
    player.rect.y -= 100
    all_sprites.add(player)

    platform1 = Platform(0, SCREEN_HEIGHT - 45 - 100, world_width, 50)
    platform2 = Platform(250, 800 - 100, 500, 20)
    platform3 = Platform(900, 600 - 100, 500, 20)
    platforms.add(platform1, platform2, platform3)
    all_sprites.add(platform1, platform2, platform3)

    left_wall = InvisibleWall(200, 100, 1, world_height)
    right_wall = InvisibleWall(world_width - 200, 100, 1, world_height)

    walls = pygame.sprite.Group()
    walls.add(left_wall, right_wall)

    enemy1 = Enemy(1000, platform1.rect.y - 150, 1)
    enemy2 = Enemy(1500, platform3.rect.y - 30, 1)
    enemies.add(enemy1, enemy2)
    all_sprites.add(enemy1, enemy2)

    running = [True]

    clock = pygame.time.Clock()
    pause_menu = PauseMenu(screen)

    while running[0]:
        screen.fill(BLACK)
        draw_background(screen, '8d1419edf69da59037c58cbbd49c9424.jpg', camera)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running[0] = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_menu.pause(running)
                if event.key == pygame.K_SPACE:
                    if not player.is_jumping:
                        player.vy = -15
                        player.is_jumping = True
                    elif player.can_double_jump:
                        player.vy = -15
                        player.can_double_jump = False

        player_walls_collided = pygame.sprite.spritecollide(player, walls, False)
        for wall in player_walls_collided:
            if player.vx > 0:
                player.rect.right = min(player.rect.right, wall.rect.left)
                player.vx = 0
            elif player.vx < 0:
                player.rect.left = max(player.rect.left, wall.rect.right)
                player.vx = 0

        if pygame.mouse.get_pressed()[0] and time.time() * 1000 - player.last_shot_time > player.shoot_cooldown:
            if player.vx < 0:
                bullet = Bullet(player.rect.left, player.rect.centery, "left")
            else:
                bullet = Bullet(player.rect.right, player.rect.centery, "right")

            player.all_sprites.add(bullet)
            player.bullets.add(bullet)
            player.last_shot_time = time.time() * 1000

            player.all_sprites.add(bullet)
            player.bullets.add(bullet)
            player.last_shot_time = time.time() * 1000
            bullet_sound = pygame.mixer.Sound('bullet_sound.wav.mp3')
            bullet_sound.play()

        all_sprites.update(enemies, running)

        game_outcome = player.update(enemies, running)
        if game_outcome == 'dead':
            return 'main_menu'

        hit_platforms = pygame.sprite.spritecollide(player, platforms, False)
        for platform in hit_platforms:
            if player.vy > 0:
                player.rect.bottom = platform.rect.top
                player.vy = 0
                player.is_jumping = False
                player.can_double_jump = True

        hit_enemies = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for bullet, enemy_list in hit_enemies.items():
            for enemy in enemy_list:
                enemy.kill()

        if not enemies:
            return 'main_menu'


        camera.update(player)

        font = pygame.font.Font(None, 36)
        health_text = font.render(f'Health: {player.health}', True, WHITE)
        screen.blit(health_text, (10, 10))

        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()

def level_2():
    global player
    camera = Camera(world_width, world_height)
    draw_background(screen, '4db57f61-b2fd-45f2-94b0-0fc2c31b10d3_rsz_1mountain_background_png.png', camera)

    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    pygame.mixer.init()

    player = Player(all_sprites, bullets)
    player.rect.x += 300  # сдвигаем позицию игрока вправо на 300 пикселей
    player.rect.y -= 100  # Поднимаем игрока на 100 пикселей вверх
    all_sprites.add(player)

    platform1 = Platform(0, SCREEN_HEIGHT - 45 - 100, world_width, 50)
    platform2 = Platform(400, 700 - 100, 300, 20)
    platform3 = Platform(800, 500 - 100, 400, 20)
    platforms.add(platform1, platform2, platform3)
    all_sprites.add(platform1, platform2, platform3)

    # Создаем невидимые стены
    left_wall = InvisibleWall(200, 100, 1, world_height)  # стена слева
    right_wall = InvisibleWall(world_width - 200, 100, 1, world_height)  # стена справа

    # Создаем группу для стен
    walls = pygame.sprite.Group()
    walls.add(left_wall, right_wall)

    enemy1 = Enemy(1000, platform1.rect.y - 150, 1)
    enemy2 = Enemy(1500, platform3.rect.y - 30, 1)
    enemies.add(enemy1, enemy2)
    all_sprites.add(enemy1, enemy2)


    running = [True]

    clock = pygame.time.Clock()
    pause_menu = PauseMenu(screen)

    while running[0]:
        screen.fill(BLACK)  # Очищаем экран перед перерисовкой
        draw_background(screen, '8d1419edf69da59037c58cbbd49c9424.jpg', camera)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running[0] = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_menu.pause(running)
                if event.key == pygame.K_SPACE:
                    if not player.is_jumping:
                        player.vy = -15
                        player.is_jumping = True
                    elif player.can_double_jump:  # Проверяем, может ли игрок сделать двойной прыжок
                        player.vy = -15
                        player.can_double_jump = False  # Устанавливаем флаг двойного прыжка в False после использования

        # Проверяем столкновения игрока со стенами
        player_walls_collided = pygame.sprite.spritecollide(player, walls, False)
        for wall in player_walls_collided:
            if player.vx > 0:  # двигается вправо
                player.rect.right = min(player.rect.right, wall.rect.left)  # Установливает правый край спрайта игрока до левого края стены
                player.vx = 0
            elif player.vx < 0:  # двигается влево
                player.rect.left = max(player.rect.left, wall.rect.right)  # Установливает левый край спрайта игрока до правого края стены
                player.vx = 0

        # Создание пули
        if pygame.mouse.get_pressed()[0] and time.time() * 1000 - player.last_shot_time > player.shoot_cooldown:
            if player.vx < 0:
                bullet = Bullet(player.rect.left, player.rect.centery, "left")
            else:
                bullet = Bullet(player.rect.right, player.rect.centery, "right")

            player.all_sprites.add(bullet)
            player.bullets.add(bullet)
            player.last_shot_time = time.time() * 1000

            player.all_sprites.add(bullet)
            player.bullets.add(bullet)
            player.last_shot_time = time.time() * 1000
            bullet_sound = pygame.mixer.Sound('bullet_sound.wav.mp3')
            bullet_sound.play()

        all_sprites.update(enemies, running)

        game_outcome = player.update(enemies, running)
        if game_outcome == 'dead':
            return 'main_menu'  # Игрок умер - возвращаемся в главное меню

        # Существующий код для обработки столкновений игрока с платформами
        hit_platforms = pygame.sprite.spritecollide(player, platforms, False)
        for platform in hit_platforms:
            if player.vy > 0:
                player.rect.bottom = platform.rect.top
                player.vy = 0
                player.is_jumping = False
                player.can_double_jump = True  # Сбрасываем возможность двойного прыжка, когда игрок приземляется на платформу

        # Проверка столкновения пуль с врагами
        hit_enemies = pygame.sprite.groupcollide(bullets, enemies, True, False)
        for bullet, enemy_list in hit_enemies.items():
            for enemy in enemy_list:
                # Здесь вы можете добавить логику для обработки столкновения пули с врагом
                enemy.kill()

        if not enemies:  # Если нет врагов, возвращаемся в меню выбора уровня
            return 'main_menu'


        camera.update(player)

        font = pygame.font.Font(None, 36)
        health_text = font.render(f'Health: {player.health}', True, WHITE)
        screen.blit(health_text, (10, 10))

        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))

        pygame.display.flip()
        clock.tick(120)

    pygame.quit()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("платформер")

    menu = Menu(screen)

    while True:
        menu.display_menu()
        chosen_level = menu.check_events()

        if chosen_level == "Exit":
            break
        elif chosen_level == "Level 1":
            level_outcome = level_1()
            if level_outcome == 'main_menu':
                continue
            else:
                break
        elif chosen_level == "Level 2":
            level_outcome = level_2()
            if level_outcome == 'main_menu':
                continue
            else:
                break

    pygame.quit()

if __name__ == "__main__":
    main()
