import pygame
import numpy as np
import pandas as pd

#pygame.init()
#pygame.mixer.music.load('env/img/04-castle.mp3')
#pygame.mixer.music.play(-1)
WIDTH = 55
HEIGHT = 45

KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_SPACE = pygame.K_SPACE
KEY_PAUSE = pygame.K_p

GRAVITY = 9.81 * HEIGHT / 20

PLAYER_X = 2 * WIDTH
PLAYER_SPEED_X = WIDTH / 10
PLAYER_SPEED_Y = HEIGHT / 2

WALKER_SPEED_X = WIDTH / 10
DT = 0.1
MUSHROOM_SPEED_X = WIDTH / 10

pygame.font.init()

class GameObject(object):

    def __init__(self, game, sprite):
        self.group = sprite
        self.game = game

    def draw(self, surface):
        self.group.draw(surface)
        #self.scr.blit(tex, (0, 0))


class Moveable(GameObject):

    def __init__(self, game, sprite):
        super(Moveable, self).__init__(game, sprite)
        self.rect = self.group.sprites()[0].rect
        self.old_rect = self.rect.copy()
        self.speed = np.zeros(2)
        self.alive = True

    def update_rect(self, x, bounds=True):
        if bounds:
            if self.rect.x < 0:
                self.rect.x = 0
            w, _ = pygame.display.get_surface().get_size()
            if self.rect.x > (w - WIDTH):
                self.rect.x = w - WIDTH
        self.rect.x -= x
        self.old_rect.x -= x

    def update_speed(self, t):
        self.speed[1] += GRAVITY * t

    def is_visible(self):
        return self.rect.x < self.game.visible_width * WIDTH

    def is_dead(self):
        return (not self.alive) or (self.rect.y > self.game.height * HEIGHT)

    def collided_with(self, old_rect, rect, element):
        with_left = old_rect.right <= element.rect.left and rect.right > element.rect.left
        with_right = old_rect.left >= element.rect.right and rect.left < element.rect.right
        with_top = old_rect.bottom <= element.rect.top and rect.bottom > element.rect.top
        with_bottom = old_rect.top >= element.rect.bottom and rect.top < element.rect.bottom
        return with_left, with_right, with_top, with_bottom

    def handle_obstacle_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        global WALKER_SPEED_X
        global MUSHROOM_SPEED_X
        if t:
            self.rect.bottom = element.rect.top
            self.speed[1] = 0
        elif b:
            self.rect.top = element.rect.bottom
        elif l:
            self.rect.right = element.rect.left
            self.speed[0] = 0

            WALKER_SPEED_X = - WALKER_SPEED_X
            MUSHROOM_SPEED_X = - MUSHROOM_SPEED_X
        elif r:
            self.rect.left = element.rect.right
            self.speed[0] = 0

            WALKER_SPEED_X = - WALKER_SPEED_X
            MUSHROOM_SPEED_X = - MUSHROOM_SPEED_X
        #print (self.speed[0])

    def update(self, *args):

        self.update_speed(DT)
        self.rect.move_ip(self.speed)
        # get ground items
        collided = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.ground.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)
        self.old_rect = self.rect.copy()


class Player(Moveable):

    def __init__(self, game):
        sprite = pygame.sprite.Group(GameSprite(2, 8, sprite='env/img/trump.png'))
        super(Player, self).__init__(game, sprite)
        self.reached_goal = False
        self.last = pygame.time.get_ticks()
        self.cooldown = 75

        self.r1 = True
        self.l1 = True
        self.l2 = False
        self.r2 = False

    def jump(self):
        if self.speed[1] == 0:
            self.speed[1] = -PLAYER_SPEED_Y

    def move_left(self):
        self.speed[0] = -PLAYER_SPEED_X

    def move_right(self):
        self.speed[0] = PLAYER_SPEED_X

    def stop(self):
        self.speed[0] = 0

    def handle_goal_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if l or r or t or b:
            self.reached_goal = True

    def handle_coin_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if l or r or b or t:
            element.alive = False
        #if t:
         #   element.alive = False

    def handle_enemy_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if l or r or b:
            self.alive = False
        if t:
            element.alive = False

    def update(self, *args):
        self.update_speed(DT)
        self.rect.move_ip(self.speed)
        # get ground items
        collided = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.ground.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)
        # loop over collided enemies, kill them or die accordingly
        for e in self.game.enemies:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
                self.handle_enemy_collision(self.old_rect, curr_rect, e)
        for m in self.game.mushrooms:
            if pygame.sprite.collide_rect(self, m):
                self.handle_obstacle_collision(self.old_rect, curr_rect, m)
                self.handle_enemy_collision(self.old_rect, curr_rect, m)
        for c in self.game.coins:
            if pygame.sprite.collide_rect(self, c):
                self.handle_obstacle_collision(self.old_rect, curr_rect, c)
                self.handle_coin_collision(self.old_rect, curr_rect, c)
        # check goal collision
        goal = self.game.goal.group.sprites()[0]
        if pygame.sprite.collide_rect(self, goal):
            self.handle_goal_collision(self.old_rect, curr_rect, goal)

        self.old_rect = self.rect.copy()

        if self.speed[0] > 0:
            now = pygame.time.get_ticks()
            if now - self.last >= self.cooldown:
                self.last = now

                if self.r1 == True:
                    self.group.sprites()[0].image = pygame.image.load('env/img/mario2.png')
                    self.r2 = True
                    self.r1 = False
                      #print(1)

                elif self.r2 == True:
                    self.group.sprites()[0].image = pygame.image.load('env/img/mario.png')
                    self.r1 = True
                    self.r2 = False
                      #print(2)


        elif self.speed[0] < 0:
            if now - self.last >= self.cooldown:
                self.last = now

                if self.l1 == True:
                    self.group.sprites()[0].image = pygame.image.load('env/img/marioR2.png')
                    self.l2 = True
                    self.l1 = False
                    #print(3)
                elif self.l2 == True:

                    self.group.sprites()[0].image = pygame.image.load('env/img/marioR1.png')
                    self.l1 = True
                    self.l2 = False
                    #print(4)

        #self.group.sprites()[0].image = pygame.transform.scale(self.group.sprites()[0].image, (WIDTH, HEIGHT))


class Enemy(Moveable):

    def handle_player_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if b:
            self.alive = False
        if l or r or t:
            element.alive = True


    def update(self, *args):
        self.update_speed(DT)
        self.rect.move_ip(self.speed)
        # get ground items
        collided = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.ground.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)

        # loop over collided enemies, simply avoid collisions
        for e in self.game.enemies:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
        #for m in self.game.mushrooms:
          #  if pygame.sprite.collide_rect(self, m):
           #     self.handle_obstacle_collision(self.old_rect, curr_rect, m)
        # kll player if necessary, or die accordingly
        if pygame.sprite.collide_rect(self, self.game.player):
            self.handle_player_collision(self.old_rect, curr_rect, self.game.player)

        self.old_rect = self.rect.copy()


class Walker(Enemy):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/burito.png'))
        super(Walker, self).__init__(game, sprite)

    def update(self, *args):
        if self.is_visible():
            self.speed[0] = -WALKER_SPEED_X

        super(Walker, self).update()

class Coin(Enemy):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/coin.png'))
        super(Coin, self).__init__(game, sprite)

    def update(self, *args):
        if self.is_visible():
            self.speed[0] = 0

        super(Coin, self).update()


class Mushroom(Enemy):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/mushroom.png'))
        super(Mushroom, self).__init__(game, sprite)

    def update(self, *args):
        if self.is_visible():
            self.speed[0] = MUSHROOM_SPEED_X

        super(Mushroom, self).update()


class Ground(GameObject):

    def __init__(self, game, positions):
        group = pygame.sprite.Group()
        for position in positions:
            group.add(GameSprite(*position, sprite='env/img/ground.jpg'))
        super(Ground, self).__init__(game, group)


class Goal(GameObject):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/flag.png'))
        super(Goal, self).__init__(game, sprite)


class GameSprite(pygame.sprite.Sprite):

    def __init__(self, x, y, sprite=None):
        super(GameSprite, self).__init__()

        if sprite is None:
            self.image = pygame.Surface([WIDTH, HEIGHT])
            self.image.fill((0, 0, 0))
        else:
            self.image = pygame.image.load(sprite)
            self.image = pygame.transform.scale(self.image, (WIDTH, HEIGHT))

        self.rect = self.image.get_rect()
        self.rect.x = x * WIDTH
        self.rect.y = y * HEIGHT

class Game(object):
    global scorevariable
    scorevariable = 0
    global maxstring
    maxstring = ' '
    global playing, done
    playing = False
    global max_score
    max_score = 0

    def __init__(self, levelfile):

        pygame.init()
        self.levelfile = levelfile
        height, width = self.load_level(levelfile)

        self.camera_x = 0
        self.height = height
        self.width = width
        self.visible_width = 10
        self.screen = pygame.display.set_mode((WIDTH * self.visible_width, HEIGHT * height))
        self.clock = pygame.time.Clock()
        pygame.mixer.music.stop()
        # self.effect = pygame.mixer.Sound('env/img/sound.ogg')
        # self.toilet = pygame.mixer.Sound('env/img/toilet.ogg')

        pygame.init()
        #pygame.mixer.music.load('env/img/04-castle.mp3')
        #pygame.mixer.music.play(-1)


    def menu(self):
        global playing

        myfont = pygame.font.SysFont('Comic Sans MS', 30)
        global scorevariable
        global max_score
        global maxstring
        print (max_score)
        print (maxstring)
        menu = pygame.image.load('env/img/menu.png')

        # pygame.mixer.music.load('foo.mp3')
        # pygame.mixer.music.play(0)
        self.reset()
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return
        while playing == False:
            self.screen.fill((70, 255, 10))
            self.screen.blit(menu, (0, 0))

            if scorevariable > max_score:
                max_score = scorevariable

            highscore = 'HIGHSCORE:'
            maxstring = highscore + str(max_score)
            text = myfont.render(maxstring, False, (0, 0, 0))
            self.screen.blit(text, (0, 0))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    playing = True
                    # pygame.mixer.music.stop()


                    game.play()
                if event.type == pygame.QUIT:
                    return

    def load_level(self, filename):
        ground_positions = []
        enemies = []
        mushrooms = []
        coins = []
        lvl = pd.read_csv(filename, header=None)
        for x in range(lvl.shape[1]):
            for y in range(lvl.shape[0]):
                if lvl[x][y] == 1:
                    ground_positions.append((x, y))
                if lvl[x][y] == 2:
                    self.goal = Goal(self, (x, y))
                if lvl[x][y] == 3:
                    enemies.append(Walker(self, (x, y)))
                if lvl[x][y] == 4:
                    mushrooms.append(Mushroom(self, (x, y)))  # Mushroom
                if lvl[x][y] == 5:
                    coins.append(Coin(self, (x, y))) # Coins

        self.ground = Ground(self, ground_positions)
        self.player = Player(self)
        self.enemies = enemies
        self.mushrooms = mushrooms
        self.coins = coins

        return lvl.shape

    def draw(self):
        # Clear canvas
        self.screen.fill((112, 145, 189))
        self.ground.draw(self.screen)
        self.player.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        self.goal.draw(self.screen)
        for m in self.mushrooms:
            m.draw(self.screen)
        for c in self.coins:
            c.draw(self.screen)
        self.goal.draw(self.screen)

        myfont = pygame.font.SysFont('Comic Sans MS', 30)
        global scorevariable
        scorestring = str(scorevariable)
        text = myfont.render(scorestring, False, (0, 0, 0))

        self.screen.blit(text, (0, 0))

        pygame.display.update()

    def get_camera_shift(self):
        relative_x = self.player.rect.x - PLAYER_X
        w, _ = pygame.display.get_surface().get_size()
        if (self.camera_x + relative_x) < 0 or (self.camera_x + relative_x) > (self.width * WIDTH - w):
            relative_x = 0
        return relative_x

    def update(self):
        # first move the player
        self.player.update()
        # get relative position wrt camera
        relative_x = self.get_camera_shift()
        # update enemies
        to_remove = []
        for e in self.enemies:
            e.update()
            if e.is_dead():
                to_remove.append(e)
        for e in to_remove:
            self.enemies.remove(e)

        to_remove = []

        for m in self.mushrooms:
            m.update()
            if m.is_dead():
                to_remove.append(m)
        for m in to_remove:
            self.mushrooms.remove(m)

            to_remove = []

        for c in self.coins:
            c.update()
            if c.is_dead():
                to_remove.append(c)
                global scorevariable
                scorevariable += 1
        for c in to_remove:
            self.coins.remove(c)

        # update relative positions _after_ update handling, or will have corrupt collisions
        self.player.update_rect(relative_x)
        for e in self.enemies:
            e.update_rect(relative_x, bounds=False)
        for m in self.mushrooms:
            m.update_rect(relative_x, bounds=False)
        for c in self.coins:
            c.update_rect(relative_x, bounds=False)
        # update ground position wrt camera
        for s in self.ground.group.sprites():
            s.rect.x -= relative_x
        # update goal position wrt camera
        self.goal.group.sprites()[0].rect.x -= relative_x
        # update camera position
        self.camera_x += relative_x

    def state(self):
        def scale_sprite(s):
            x, y = s.rect.center
            x = x // WIDTH
            y = y // HEIGHT
            return x, y

        tiles = np.zeros((self.visible_width, self.height))
        objects = {1: self.ground.group.sprites(),
                   2: self.goal.group.sprites(),
                   3: self.enemies,
                   4: self.mushrooms,
                   5:self.coins,
                   9: [self.player]}
        for id, elements in objects.items():
            for e in elements:
                x, y = scale_sprite(e)
                if x >= 0 and x < self.visible_width and y >= 0 and y < self.height:
                    tiles[x, y] = id
        coord = np.array(self.player.rect.center) / np.array([WIDTH, HEIGHT])
        state = {'tiles': np.expand_dims(tiles, axis=0), 'dead': self.player.is_dead(),
                 'goal': self.player.reached_goal, 'coord': coord}
        return state

    def reset(self):
        self.load_level(self.levelfile)
        self.camera_x = 0
        global scorevariable
        global playing
        global max_score
        if scorevariable > max_score:
            max_score = scorevariable
        scorevariable = 0
        playing = False
        # pygame.mixer.music.stop()

       # pygame.mixer.music.load('env/img/04-castle.mp3')
       # pygame.mixer.music.play(-1)


    def step(self, action):
        # NOOP(0) LEFT(1) RIGHT(2) JUMP(3) LEFT_JUMP(4) RIGHT_JUMP(5)
        if action == -1:
            self.pause()
        if action == 0 or action == 3:
            self.player.stop()
        if action == 1 or action == 4:
            self.player.move_left()
        if action == 2 or action == 5:
            self.player.move_right()
        if action == 3 or action == 4 or action == 5:
            self.player.jump()
            # self.effect.play()

        self.update()
        is_dead = self.player.is_dead()
        won = self.player.reached_goal
        done = is_dead or won

        return done

    def process_keys(self):
        keys = pygame.key.get_pressed()
        action = 0
        if keys[KEY_LEFT] and keys[KEY_SPACE]:
            action = 4
        elif keys[KEY_LEFT]:
            action = 1
        elif keys[KEY_RIGHT] and keys[KEY_SPACE]:
            action = 5
        elif keys[KEY_RIGHT]:
            action = 2
        elif keys[KEY_SPACE]:
            action = 3
        elif keys[KEY_PAUSE]:
            action = -1

        pygame.event.pump()
        return action

    def render(self, mode='human'):
         self.clock.tick(60)
         self.draw()
         return pygame.surfarray.array3d(self.screen)

    def play(self):
        global playing, done
        done = False
        pygame.mixer.music.load('env/img/04-castle.mp3')
        pygame.mixer.music.play(-1)
        while not done:
            action = self.process_keys()
            done = self.step(action)
            self.render()
            for event in pygame.event.get():

# determin if X was clicked, or Ctrl+W or Alt+F4 was used

              if event.type == pygame.QUIT:
                      return

        pygame.mixer.music.stop()
        # self.toilet.play()
        playing = False
        done = False
        game.menu()



#def pause(self):
 #   self.clock.tick(0)
#print(self.state())


if __name__ == '__main__':
    game = Game('env/level.csv')
    game.menu()
