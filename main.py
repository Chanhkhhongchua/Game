import pygame
from pygame.locals import *
from pygame import mixer
import pickle
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60
screen_width = 1000
screen_height = 750

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Platformer')

# định nghĩa font chữ
font = pygame.font.SysFont('Bold', 50)
font_score = pygame.font.SysFont('Bold', 40)
font = pygame.font.SysFont('Bold 93', 70)



# định nghĩa các biến trò chơi
tile_size = 50
game_over = 0
main_menu = True
level = 1
level_menu = False  # Biến mới để xử lý menu chọn màn
max_levels = 7
score = 0
lives = 3
max_lives = 3

# định nghĩa màu sắc
white = (255, 255, 255)
blue = (0, 0, 255)

# tải hình ảnh
bg_img = pygame.image.load('img/bsky4.png')
restart_img = pygame.image.load('img/restart_btn.png')
start_img = pygame.image.load('img/start_btn.png')
exit_img = pygame.image.load('img/exit_btn.png')
close_img = pygame.image.load('level/close.png')  # Tải hình ảnh nút thoát
volume_img = pygame.image.load('img/Volume.png')
next_img = pygame.image.load('img/next.png')  # Tải hình ảnh nút "Next"
previous_img = pygame.image.load('img/previous.png')  # Tải hình ảnh nút "Previous"


# Tải hình ảnh các màn chơi
level_images = []
for i in range(1, max_levels + 1):
    level_images.append(pygame.image.load(f'level/0{i}.png'))

# tải âm thanh
pygame.mixer.music.load('img/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('img/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('img/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('img/game_over.wav')
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))

# hàm để khởi động lại cấp độ
def reset_level(level):
    global lives
    player.reset(100, screen_height - 130)
    blob_group.empty()
    platform_group.empty()
    coin_group.empty()
    lava_group.empty()
    exit_group.empty()
    heart_group.empty()

    # tải dữ liệu cấp độ và tạo thế giới
    if path.exists(f'level{level}_data'):
        with open(f'level{level}_data', 'rb') as pickle_in:
            world_data = pickle.load(pickle_in)
    world = World(world_data)
    lives = 3

    

    return world

class Button():
    def __init__(self, x, y, image,text=''):
        self.image = pygame.transform.scale(image, (100, 100))  # Tăng kích thước nút lên 100x100
        self.image = image
        self.rect = self.image.get_rect()
        self.text = text
        self.rect.x = x
        self.rect.y = y
        self.clicked = False
        self.font = pygame.font.SysFont('bold', 30)  # Điều chỉnh kích thước font theo nhu cầu


    def draw(self):
        action = False
        # lấy vị trí chuột
        pos = pygame.mouse.get_pos()

        # kiểm tra điều kiện di chuột và nhấn chuột
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                action = True
                self.clicked = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        

        # Tính toán và vẽ văn bản phía sau nút
        text_surface = self.font.render(self.text, True, (128, 0, 0))  # Màu trắng
        text_rect = text_surface.get_rect()
        text_rect.midright = (self.rect.left - 10, self.rect.centery)  # Đặt vị trí nằm bên phải của nút
  
        

        screen.blit(text_surface, text_rect)
        # Vẽ hình ảnh nút lên màn hình
        screen.blit(self.image, self.rect)

        return action
    
mute_button_image = pygame.image.load('img/Volume-1.png').convert_alpha()
mute_button_rect = mute_button_image.get_rect()

    
class VolumeButton(pygame.sprite.Sprite):
    def __init__(self, image, position):
        super().__init__()
        self.image = pygame.image.load(image)
        self.rect = self.image.get_rect(topleft=position)
        self.clicked = False
        self.sound_on = True

    def toggle_sound(self):
        if self.sound_on:
            pygame.mixer.music.set_volume(0.0)
            self.image = mute_button_image  # Thay đổi hình ảnh khi âm thanh tắt
            mute_button_image.get_rect()
        else:
            pygame.mixer.music.set_volume(1.0)
            self.image = pygame.image.load('img/Volume.png')  # Đổi lại hình ảnh khi âm thanh bật
        self.sound_on = not self.sound_on

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if not self.clicked:
                    self.clicked = True
                    self.toggle_sound()
                else:
                    self.clicked = False
        if event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)


class Player():
    def __init__(self, x, y):
        self.reset(x, y)
    
    

    def update(self, game_over):
        global lives  # Đảm bảo biến lives được truy cập chính xác
        dx = 0
        dy = 0
        walk_cooldown = 5
        col_thresh = 20
        start_x, start_y = self.rect.x, self.rect.y

        if game_over == 0:
            # lấy các phím bấm
            key = pygame.key.get_pressed()
            if key[pygame.K_UP] and not self.jumped and not self.in_air:
                jump_fx.play()
                self.vel_y = -16
                self.jumped = True
            if not key[pygame.K_UP]:
                self.jumped = False
            if key[pygame.K_LEFT]:
                dx -= 5
                self.counter += 1
                self.direction = -1
            if key[pygame.K_RIGHT]:
                dx += 5
                self.counter += 1
                self.direction = 1
            if not key[pygame.K_LEFT] and not key[pygame.K_RIGHT]:
                self.counter = 0
                self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # xử lý hoạt ảnh
            if self.counter > walk_cooldown:
                self.counter = 0
                self.index += 1
                if self.index >= len(self.images_right):
                    self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

            # thêm trọng lực
            self.vel_y += 1
            if self.vel_y > 10:
                self.vel_y = 10
            dy += self.vel_y

            # kiểm tra va chạm
            self.in_air = True
            for tile in world.tile_list:
                # kiểm tra va chạm theo hướng x
                if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # kiểm tra va chạm theo hướng y
                if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # kiểm tra nếu bên dưới mặt đất, tức là đang nhảy
                    if self.vel_y < 0:
                        dy = tile[1].bottom - self.rect.top
                        self.vel_y = 0
                    # kiểm tra nếu bên trên mặt đất, tức là đang rơi
                    elif self.vel_y >= 0:
                        dy = tile[1].top - self.rect.bottom
                        self.vel_y = 0
                        self.in_air = False
                # kiểm tra va chạm với kẻ thù
                if pygame.sprite.spritecollide(self, blob_group, False):
                    if not self.hit:
                        self.hit = True
                        self.hit_time = pygame.time.get_ticks()
                        lives -= 1
                        if lives <= 0:
                            game_over = -1
                            game_over_fx.play()
                        else:
                            # Điều chỉnh hướng bay ngược lại dựa trên hướng của nhân vật
                            dy = -30  # Nhân vật bay lên
                            if self.direction == 1:  # Nếu đang nhìn về bên phải
                                dx = -30  # Lùi ra sau về bên trái
                            else:  # Nếu đang nhìn về bên trái
                                dx = 30  # Lùi ra sau về bên phải


			 # Kiểm tra thời gian trúng đòn
            if self.hit and pygame.time.get_ticks() - self.hit_time > 1000:  # 1 giây sau khi trúng đòn
                self.hit = False

            # kiểm tra va chạm với dung nham
            if pygame.sprite.spritecollide(self, lava_group, False):
                lives -= 1
                if lives > 0:
                    self.reset(start_x, start_y)
                else:
                    game_over = -1
                    game_over_fx.play()

            # kiểm tra va chạm với lối ra
            if pygame.sprite.spritecollide(self, exit_group, False):
                game_over = 1

            # kiểm tra va chạm với trái tim
            if pygame.sprite.spritecollide(self, heart_group, True):
                if lives < max_lives:
                    lives += 1

            # kiểm tra va chạm với nền tảng
            for platform in platform_group:
                # va chạm theo hướng x
                if platform.rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                    dx = 0
                # va chạm theo hướng y
                if platform.rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                    # kiểm tra nếu bên dưới nền tảng
                    if abs((self.rect.top + dy) - platform.rect.bottom) < col_thresh:
                        self.vel_y = 0
                        dy = platform.rect.bottom - self.rect.top
                    # kiểm tra nếu bên trên nền tảng
                    elif abs((self.rect.bottom + dy) - platform.rect.top) < col_thresh:
                        self.rect.bottom = platform.rect.top - 1
                        self.in_air = False
                        dy = 0
                    # di chuyển theo chiều ngang với nền tảng
                    if platform.move_x != 0:
                        self.rect.x += platform.move_direction

            # cập nhật tọa độ người chơi
            self.rect.x += dx
            self.rect.y += dy
            # Chuyển đổi hình ảnh nếu đang nhảy
            if self.in_air and self.vel_y != 0:  # Kiểm tra nếu nhân vật đang di chuyển lên hoặc xuống
                if self.direction == 1:
                    self.image = self.double_jump_images_right[self.index % len(self.double_jump_images_right)]
                elif self.direction == -1:
                    self.image = self.double_jump_images_left[self.index % len(self.double_jump_images_left)]
                self.counter += 1
            else:
                if self.counter > walk_cooldown:
                    self.counter = 0
                    self.index += 1
                    if self.index >= len(self.images_right):
                        self.index = 0
                if self.direction == 1:
                    self.image = self.images_right[self.index]
                if self.direction == -1:
                    self.image = self.images_left[self.index]

        elif game_over == -1:
            self.image = self.dead_image
            draw_text('GAME OVER!', font, blue, (screen_width // 2) - 100, screen_height // 2)
            if self.rect.y > 200:
                self.rect.y -= 5

        # vẽ người chơi lên màn hình
        screen.blit(self.image, self.rect)

        return game_over

    def reset(self, x, y):
        self.images_right = []
        self.images_left = []
        self.index = 0
        self.counter = 0
        for num in range(0, 12):
            img_right = pygame.image.load(f'img/run/pink{num}.png')
            img_right = pygame.transform.scale(img_right, (60, 70))
            img_left = pygame.transform.flip(img_right, True, False)
            self.images_right.append(img_right)
            self.images_left.append(img_left)
         # Tải hình ảnh nhảy (double jump)
        self.double_jump_images_right = []
        self.double_jump_images_left = []

        for num in range(0, 4):  # Giả sử có 6 hình cho nhảy
            img_right = pygame.image.load(f'double_jump/pink_{num}.png')
            img_right = pygame.transform.scale(img_right, (60, 70))
            img_left = pygame.transform.flip(img_right, True, False)
            self.double_jump_images_right.append(img_right)
            self.double_jump_images_left.append(img_left)
       
        self.dead_image = pygame.image.load('img/ghost.png')
        self.dead_image = pygame.transform.scale(self.dead_image, (80, 100))
        self.image = self.images_right[self.index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.vel_y = 0
        self.jumped = False
        self.direction = 0
        self.in_air = True
        self.hit=False
        self.hit_time=0

class World():
    def __init__(self, data):
        self.tile_list = []

        # tải hình ảnh
        dirt_img = pygame.image.load('img/dirt2.png')
        grass_img = pygame.image.load('img/dat.png')

        row_count = 0
        for row in data:
            col_count = 0
            for tile in row:
                if tile == 1:
                    img = pygame.transform.scale(dirt_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 2:
                    img = pygame.transform.scale(grass_img, (tile_size, tile_size))
                    img_rect = img.get_rect()
                    img_rect.x = col_count * tile_size
                    img_rect.y = row_count * tile_size
                    tile = (img, img_rect)
                    self.tile_list.append(tile)
                if tile == 3:
                    blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
                    blob_group.add(blob)
                if tile == 4:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 1, 0)
                    platform_group.add(platform)
                if tile == 5:
                    platform = Platform(col_count * tile_size, row_count * tile_size, 0, 1)
                    platform_group.add(platform)
                if tile == 6:
                    lava = Lava(col_count * tile_size, row_count * tile_size + (tile_size // 2))
                    lava_group.add(lava)
                if tile == 7:
                    coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    coin_group.add(coin)
                if tile == 8:
                    exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
                    exit_group.add(exit)
                if tile == 9:
                    heart = Heart(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
                    heart_group.add(heart)
                col_count += 1
            row_count += 1

    def draw(self):
        for tile in self.tile_list:
            screen.blit(tile[0], tile[1])

    
    

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load('img/qvat0.png')
        self.image = pygame.transform.scale(self.image, (tile_size, int(tile_size * 0.75)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_direction = 1
        self.move_counter = 0

    def update(self):
        self.rect.x += self.move_direction
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, move_x, move_y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/platform.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.move_counter = 0
        self.move_direction = 1
        self.move_x = move_x
        self.move_y = move_y

    def update(self):
        self.rect.x += self.move_direction * self.move_x
        self.rect.y += self.move_direction * self.move_y
        self.move_counter += 1
        if abs(self.move_counter) > 50:
            self.move_direction *= -1
            self.move_counter *= -1

class Lava(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/lava.png')
        self.image = pygame.transform.scale(img, (tile_size, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/coin.png')
        self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

class Exit(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/exit.png')
        self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Heart(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        img = pygame.image.load('img/heart.png')
        self.image = pygame.transform.scale(img, (tile_size , tile_size ))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

# Tạo các nhóm sprite
blob_group = pygame.sprite.Group()
platform_group = pygame.sprite.Group()
lava_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()
heart_group = pygame.sprite.Group()

# Tạo người chơi
player = Player(100, screen_height - 130)

# Tạo thế giới
if path.exists(f'level{level}_data'):
    with open(f'level{level}_data', 'rb') as pickle_in:
        world_data = pickle.load(pickle_in)
world = World(world_data)

def draw_text(text, font, color, x, y):
    img = font.render(text, True, color)
    screen.blit(img, (x, y))




# Tạo các nút
# Tạo các nút
restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)
volume_button = VolumeButton('img/Volume.png', (0, 10))
close_button = Button(screen_width // 2 - 20, 550, close_img, text='Close')
next_button = Button(550, 10, next_img)
previous_button = Button(450, 10, previous_img)


# Tạo các nút chọn màn
level_buttons = []
for i in range(max_levels):
    level_buttons.append(Button(screen_width // 2 - 20, 200 + 50 * i, level_images[i],f'Màn {i+1}'))  # Cách nhau 120 pixels theo chiều dọc
    


# Hàm vòng lặp chính
run = True
while run:
    clock.tick(fps)
    screen.blit(bg_img, (0, 0))

    

    if main_menu:
        if exit_button.draw():
            run = False
        if start_button.draw():
            main_menu = False
            level_menu = True  # Mở menu chọn màn

    elif level_menu:  # Menu chọn màn
        draw_text('Main Menu', font, blue, screen_width // 2 - 150, 100)
        for i, button in enumerate(level_buttons):
            if button.draw():
                level = i + 1
                world_data = []
                if path.exists(f'level{level}_data'):
                    with open(f'level{level}_data', 'rb') as pickle_in:
                        world_data = pickle.load(pickle_in)
                    
                            # Reset các nhóm sprite
                blob_group.empty()
                platform_group.empty()
                coin_group.empty()
                lava_group.empty()
                exit_group.empty()
                heart_group.empty()
                world = World(world_data)
                main_menu = False
                level_menu = False
                game_over = 0
        if close_button.draw():
            level_menu = False
            main_menu = True
        
    else:
        world.draw()
        if game_over == 0:
            blob_group.update()
            platform_group.update()
            game_over = player.update(game_over)
            if pygame.sprite.spritecollide(player, coin_group, True):
                coin_fx.play()
                score += 1
            draw_text('COIN: ' + str(score), font_score, blue,  70, 10)
       # Vẽ hình trái tim ở góc trên bên phải màn hình trước dòng "X3"
            heart = pygame.image.load('img/heart.png')
            heart = pygame.transform.scale(heart, (tile_size, tile_size))
            screen.blit(heart, (screen_width - tile_size * 3, 0))
            draw_text('X ' + str(lives), font_score, blue, screen_width - tile_size * 2, 10)

    
        # Hiển thị nút "Tiếp theo" và xử lý hành động khi nhấp vào nó
        if game_over == 1:  # Nếu người chơi hoàn thành màn chơi hiện tại
            if next_button.draw():
                level += 1
                if level <= max_levels:
                    world_data = []
                    if path.exists(f'level{level}_data'):
                        with open(f'level{level}_data', 'rb') as pickle_in:
                            world_data = pickle.load(pickle_in)
                    # Reset các nhóm sprite và tạo lại thế giới mới
                    blob_group.empty()
                    platform_group.empty()
                    coin_group.empty()
                    lava_group.empty()
                    exit_group.empty()
                    heart_group.empty()
                    world = World(world_data)
                    game_over = 0
                else:
                    # Nếu người chơi đã hoàn thành tất cả các màn chơi
                    draw_text('YOU WIN!', font, blue, (screen_width // 2) - 100, screen_height // 2)
                    if restart_button.draw():
                        level = 1
                        world_data = []
                        if path.exists(f'level{level}_data'):
                            with open(f'level{level}_data', 'rb') as pickle_in:
                                world_data = pickle.load(pickle_in)
                        world = World(world_data)
                        game_over = 0

        elif game_over == -1:  # Nếu người chơi thua cuộc
            if restart_button.draw():
                world = reset_level(level)
                game_over = 0

        # Hiển thị nút "Trước đó" và xử lý hành động khi nhấp vào nó
        if level > 1:  # Chỉ hiển thị nút "Trước đó" nếu không phải ở màn chơi đầu tiên
            if previous_button.draw():
                level -= 1
                world_data = []
                if path.exists(f'level{level}_data'):
                    with open(f'level{level}_data', 'rb') as pickle_in:
                        world_data = pickle.load(pickle_in)
                # Reset các nhóm sprite và tạo lại thế giới mới
                blob_group.empty()
                platform_group.empty()
                coin_group.empty()
                lava_group.empty()
                exit_group.empty()
                heart_group.empty()
                world = World(world_data)
                game_over = 0

        # Vẽ các nhóm sprite lên màn hình
        blob_group.draw(screen)
        platform_group.draw(screen)
        lava_group.draw(screen)
        coin_group.draw(screen)
        exit_group.draw(screen)
        heart_group.draw(screen)

    # Xử lý sự kiện cho các nút âm thanh và cập nhật màn hình
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        volume_button.handle_event(event)

    volume_button.draw(screen)
    pygame.display.update()

pygame.quit()