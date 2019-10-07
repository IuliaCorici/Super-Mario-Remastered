import pygame
import numpy as np
import pandas as pd

WIDTH = 80
HEIGHT = 80
# WIDTH = 20
# HEIGHT = 20

KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
KEY_SPACE = pygame.K_SPACE

GRAVITY = 9.81*HEIGHT/20

PLAYER_X = 2*WIDTH
PLAYER_SPEED_X = WIDTH/10
PLAYER_SPEED_Y = HEIGHT/2

WALKER_SPEED_X = WIDTH/10
DT = 0.1


class GameObject(object):

    def __init__(self, game, sprite):
        self.group = sprite
        self.game = game

    def draw(self, surface):
        self.group.draw(surface)


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
            if self.rect.x > (w-WIDTH):
                self.rect.x = w - WIDTH
        self.rect.x -= x
        self.old_rect.x -= x

    def update_speed(self, t):
        self.speed[1] += GRAVITY*t

    def is_visible(self):
        return self.rect.x < self.game.visible_width*WIDTH

    def is_dead(self):
        return (not self.alive) or (self.rect.y > self.game.height*HEIGHT)

    def collided_with(self, old_rect, rect, element):
        with_left = old_rect.right <= element.rect.left and rect.right > element.rect.left
        with_right = old_rect.left >= element.rect.right and rect.left < element.rect.right
        with_top = old_rect.bottom <= element.rect.top and rect.bottom > element.rect.top
        with_bottom = old_rect.top >= element.rect.bottom and rect.top < element.rect.bottom
        return with_left, with_right, with_top, with_bottom

    def handle_obstacle_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if t:
            self.rect.bottom = element.rect.top
            self.speed[1] = 0
        elif b:
            self.rect.top = element.rect.bottom
        elif l:
            self.rect.right = element.rect.left
            self.speed[0] = 0
        elif r:
            self.rect.left = element.rect.right
            self.speed[0] = 0

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
        sprite = pygame.sprite.Group(GameSprite(2, 8, sprite='env/img/mario.png'))
        super(Player, self).__init__(game, sprite)
        self.reached_goal = False

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
        collided1 = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.ground.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided1:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)

        collided2 = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.cloud.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided2:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)

        # loop over collided enemies, kill them or die accordingly
        for e in self.game.enemies:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
                self.handle_enemy_collision(self.old_rect, curr_rect, e)
        for e in self.game.goombas:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
                self.handle_enemy_collision(self.old_rect, curr_rect, e)
        for e in self.game.meatballs:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
                self.handle_enemy_collision(self.old_rect, curr_rect, e)
        # check goal collision
        goal = self.game.goal.group.sprites()[0]
        if pygame.sprite.collide_rect(self, goal):
            self.handle_goal_collision(self.old_rect, curr_rect, goal)

        self.old_rect = self.rect.copy()


class Enemy(Moveable):

    def handle_player_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if b:
            self.alive = False
        if l or r or t:
            element.alive = False

    def update(self, *args):
        self.update_speed(DT)
        self.rect.move_ip(self.speed)
        # get ground items
        collided1= pygame.sprite.spritecollide(self.group.sprites()[0], self.game.ground.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided1:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)

        collided2 = pygame.sprite.spritecollide(self.group.sprites()[0], self.game.cloud.group, False)
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        for c in collided2:
            self.handle_obstacle_collision(self.old_rect, curr_rect, c)

        # loop over collided enemies, simply avoid collisions
        for e in self.game.enemies:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
        # kll player if necessary, or die accordingly
        if pygame.sprite.collide_rect(self, self.game.player):
            self.handle_player_collision(self.old_rect, curr_rect, self.game.player)

        self.old_rect = self.rect.copy()

class Goomba(Enemy):
   def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/Walker.png'))
        self.direct = -1
        super(Goomba, self).__init__(game, sprite)

   def update(self, *args):
        if self.is_visible():
            self.speed[0] = self.direct*0.5*WALKER_SPEED_X

        last_speed = self.speed[0]

        super(Goomba, self).update()

        if self.speed[0] != last_speed:
            self.direct = -1*self.direct



class Walker(Enemy):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/DryBones.png'))
        self.direct = -1
        super(Walker, self).__init__(game, sprite)

    def update(self, *args):
        if self.is_visible():
            self.speed[0] = self.direct*WALKER_SPEED_X

        last_speed = self.speed[0]

        super(Walker, self).update()

        if self.speed[0]!=last_speed:
            self.direct=-self.direct


class Enemy2(Moveable):

    def handle_player_collision(self, old_rect, rect, element):
        l, r, t, b = self.collided_with(old_rect, rect, element)
        if b:
            self.alive = False
        if l or r or t:
            element.alive = False

    def update(self, *args):
        self.update_speed(DT)
        self.rect.move_ip(self.speed)
        # get ground items
        curr_rect = self.rect.copy()
        # loop over collided ground items, shift position to not collide anymore
        # loop over collided enemies, simply avoid collisions
        for e in self.game.enemies:
            if pygame.sprite.collide_rect(self, e):
                self.handle_obstacle_collision(self.old_rect, curr_rect, e)
        # kll player if necessary, or die accordingly
        if pygame.sprite.collide_rect(self, self.game.player):
            self.handle_player_collision(self.old_rect, curr_rect, self.game.player)

        self.old_rect = self.rect.copy()




class Meatball(Enemy2):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/meatball.png'))
        super(Meatball, self).__init__(game, sprite)

    def update(self, *args):
        self.speed[1] = 0.1 * PLAYER_SPEED_Y
        super(Meatball, self).update()


class Ground(GameObject):

    def __init__(self, game, positions):
        group = pygame.sprite.Group()
        for position in positions:
            group.add(GameSprite(*position, sprite='env/img/floor.png'))
        super(Ground, self).__init__(game, group)


class Cloud(GameObject):

    def __init__(self, game, positions):
        group = pygame.sprite.Group()
        for position in positions:
            group.add(GameSprite(*position, sprite='env/img/cloud.png'))
        super(Cloud,self).__init__(game, group)

class Lava(GameObject):

    def __init__(self, game, positions):
        group = pygame.sprite.Group()
        for position in positions:
            group.add(GameSprite(*position, sprite='env/img/lava.png'))
        super(Lava,self).__init__(game, group)

class Goal(GameObject):

    def __init__(self, game, position):
        sprite = pygame.sprite.Group(GameSprite(*position, sprite='env/img/bowsette.png'))
        super(Goal, self).__init__(game, sprite)


class GameSprite(pygame.sprite.Sprite):

    def __init__(self, x, y, sprite=None):
        super(GameSprite, self).__init__()

        if sprite is None:
            self.image = pygame.Surface([WIDTH, HEIGHT])
            self.image.fill((0,0,0))
        else:
            self.image = pygame.image.load(sprite)
            self.image = pygame.transform.scale(self.image, (WIDTH, HEIGHT))

        self.rect = self.image.get_rect()
        self.rect.x = x*WIDTH
        self.rect.y = y*HEIGHT


class Game(object):

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

    def load_level(self, filename):
        ground_positions = []
        enemies = []
        meatballs = []
        goombas = []
        cloud_positions = []
        lava_positions = []
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
                    cloud_positions.append((x, y))
                if lvl[x][y] == 5:
                    lava_positions.append((x, y))
                if lvl[x][y] == 6:
                    meatballs.append(Meatball(self, (x, y)))
                if lvl[x][y] == 7:
                    goombas.append(Goomba(self, (x, y)))

        self.ground = Ground(self, ground_positions)
        self.player = Player(self)
        self.enemies = enemies
        self.meatballs = meatballs
        self.goombas = goombas
        self.cloud = Cloud(self, cloud_positions)
        self.lava = Lava(self, lava_positions)
        return lvl.shape

    def draw(self):
        # Clear canvas
        self.screen.fill((50,0,0))
        self.ground.draw(self.screen)
        self.cloud.draw(self.screen)
        self.player.draw(self.screen)
        self.lava.draw(self.screen)
        for e in self.enemies:
            e.draw(self.screen)
        for e in self.meatballs:
            e.draw(self.screen)
        for e in self.goombas:
            e.draw(self.screen)
        self.goal.draw(self.screen)

        pygame.display.update()

    def get_camera_shift(self):
        relative_x = self.player.rect.x - PLAYER_X
        w, _ = pygame.display.get_surface().get_size()
        if (self.camera_x + relative_x) < 0 or (self.camera_x + relative_x) > (self.width*WIDTH - w):
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
        for e in self.meatballs:
            e.update()
            if e.is_dead():
                to_remove.append(e)
        for e in to_remove:
            self.meatballs.remove(e)
        to_remove = []
        for e in self.goombas:
            e.update()
            if e.is_dead():
                to_remove.append(e)
        for e in to_remove:
            self.goombas.remove(e)
        # update relative positions _after_ update handling, or will have corrupt collisions
        self.player.update_rect(relative_x)
        for e in self.enemies:
            e.update_rect(relative_x, bounds=False)
        for e in self.meatballs:
            e.update_rect(relative_x, bounds=False)
        for e in self.goombas:
            e.update_rect(relative_x, bounds=False)
        # update ground position wrt camera
        for s in self.ground.group.sprites():
            s.rect.x -= relative_x
        # update goal position wrt camera
        self.goal.group.sprites()[0].rect.x -= relative_x
        # update cloud position wrt camera
        for s in self.cloud.group.sprites():
            s.rect.x -= relative_x
        # update lava position wrt camera
        for s in self.lava.group.sprites():
            s.rect.x -= relative_x
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
                   4: self.cloud.group.sprites(),
                   5: self.lava.group.sprites(),
                   6: self.meatballs,
                   7: self.goombas,
                   9: [self.player]}
        for id, elements in objects.items():
            for e in elements:
                x, y = scale_sprite(e)
                if x >= 0 and x < self.visible_width and y >= 0 and y < self.height:
                    tiles[x, y] = id
        coord = np.array(self.player.rect.center) / np.array([WIDTH, HEIGHT])
        state = {'tiles': np.expand_dims(tiles, axis=0), 'dead': self.player.is_dead(), 'goal': self.player.reached_goal, 'coord': coord}
        return state

    def reset(self):
        self.load_level(self.levelfile)
        self.camera_x = 0

    def step(self, action):
        # NOOP(0) LEFT(1) RIGHT(2) JUMP(3) LEFT_JUMP(4) RIGHT_JUMP(5)
        if action == 0 or action == 3:
            self.player.stop()
        if action == 1 or action == 4:
            self.player.move_left()
        if action == 2 or action == 5:
            self.player.move_right()
        if action == 3 or action == 4 or action == 5:
            self.player.jump()

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
        pygame.event.pump()
        return action

    def render(self, mode='human'):
        self.clock.tick(60)
        self.draw()
        return pygame.surfarray.array3d(self.screen)

    def play(self):

        done = False
        while not done:
            action = self.process_keys()
            done = self.step(action)
            self.render()
        print(self.state())


if __name__ == '__main__':

    game = Game('env/level.csv')
    game.play()