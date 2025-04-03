import pygame
import random
import os
import neat
pygame.font.init()

WIN_WIDTH = 600
WIN_HEIGHT = 800
FLOOR = 730
STAT_FONT = pygame.font.SysFont("arial", 30)
END_FONT = pygame.font.SysFont("arial", 50)
DRAW_LINES = True

WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
pygame.display.set_caption("Jetpack Game")

pipe_img = pygame.transform.scale(
    pygame.image.load(os.path.join("imgs", "pipe.png")).convert_alpha(),
    (250, 400)
)

bg_img = pygame.transform.scale(
    pygame.image.load(os.path.join("imgs", "bg.png")).convert_alpha(),
    (600, 900)
)
bg_width = bg_img.get_width()
bg_x1 = 0
bg_x2 = bg_width
bg_scroll_speed = 1

jetpack_images = [pygame.transform.scale(pygame.image.load(os.path.join("imgs", f"jet{x}.png")).convert_alpha(), (80, 80)) for x in range(1, 4)]

gen = 0

class Jetpack:
    MAX_ROTATION = 25
    IMGS = jetpack_images
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1
        displacement = self.vel * self.tick_count + 0.5 * 3 * self.tick_count ** 2
        if displacement >= 16:
            displacement = (displacement / abs(displacement)) * 16
        if displacement < 0:
            displacement -= 2
        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1
        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME * 2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2
        blitRotateCenter(win, self.img, (self.x, self.y), self.tilt)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)

class Pipe:
    GAP = 200
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, jetpack, win):
        jetpack_mask = jetpack.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)
        top_offset = (self.x - jetpack.x, self.top - round(jetpack.y))
        bottom_offset = (self.x - jetpack.x, self.bottom - round(jetpack.y))
        return jetpack_mask.overlap(bottom_mask, bottom_offset) or jetpack_mask.overlap(top_mask, top_offset)

def blitRotateCenter(surf, image, topleft, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(topleft=topleft).center)
    surf.blit(rotated_image, new_rect.topleft)

def draw_window(win, jetpacks, pipes, score, gen, pipe_ind):
    global bg_x1, bg_x2
    bg_x1 -= bg_scroll_speed
    bg_x2 -= bg_scroll_speed
    if bg_x1 + bg_width < 0:
        bg_x1 = bg_x2 + bg_width
    if bg_x2 + bg_width < 0:
        bg_x2 = bg_x1 + bg_width
    win.blit(bg_img, (bg_x1, 0))
    win.blit(bg_img, (bg_x2, 0))
    for pipe in pipes:
        pipe.draw(win)
    for jetpack in jetpacks:
        if DRAW_LINES:
            try:
                pygame.draw.line(win, ((255, 189, 89)), (jetpack.x + jetpack.img.get_width() / 2, jetpack.y + jetpack.img.get_height() / 2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width() / 2, pipes[pipe_ind].height), 1)
                pygame.draw.line(win, ((255, 189, 89)), (jetpack.x + jetpack.img.get_width() / 2, jetpack.y + jetpack.img.get_height() / 2), (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width() / 2, pipes[pipe_ind].bottom), 1)
            except:
                pass
        jetpack.draw(win)
    win.blit(STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255)), (WIN_WIDTH - 110, 10))
    win.blit(STAT_FONT.render("Gens: " + str(gen - 1), 1, (255, 255, 255)), (10, 10))
    win.blit(STAT_FONT.render("Alive: " + str(len(jetpacks)), 1, (255, 255, 255)), (10, 50))
    pygame.display.update()

def eval_genomes(genomes, config):
    global WIN, gen
    win = WIN
    gen += 1
    nets = []
    jetpacks = []
    ge = []
    for genome_id, genome in genomes:
        genome.fitness = 0
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
        jetpacks.append(Jetpack(230, 350))
        ge.append(genome)
    pipes = [Pipe(700)]
    score = 0
    clock = pygame.time.Clock()
    run = True
    while run and len(jetpacks) > 0:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
                break
        pipe_ind = 0
        if len(jetpacks) > 0:
            if len(pipes) > 1 and jetpacks[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        for x, jetpack in enumerate(jetpacks):
            ge[x].fitness += 0.1
            jetpack.move()
            output = nets[x].activate((jetpack.y, abs(jetpack.y - pipes[pipe_ind].height), abs(jetpack.y - pipes[pipe_ind].bottom)))
            if output[0] > 0.5:
                jetpack.jump()
        rem = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            for jetpack in jetpacks:
                if pipe.collide(jetpack, win):
                    idx = jetpacks.index(jetpack)
                    ge[idx].fitness -= 1
                    nets.pop(idx)
                    ge.pop(idx)
                    jetpacks.pop(idx)
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            if not pipe.passed and len(jetpacks) > 0 and pipe.x < jetpacks[0].x:

                pipe.passed = True
                add_pipe = True
        if add_pipe:
            score += 1
            for genome in ge:
                genome.fitness += 5
            pipes.append(Pipe(WIN_WIDTH))
        for r in rem:
            pipes.remove(r)
        for jetpack in jetpacks:
            if jetpack.y + jetpack.img.get_height() - 10 >= FLOOR or jetpack.y < -50:
                idx = jetpacks.index(jetpack)
                nets.pop(idx)
                ge.pop(idx)
                jetpacks.pop(idx)
        draw_window(WIN, jetpacks, pipes, score, gen, pipe_ind)

def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(eval_genomes, 50)
    print('\nBest genome:\n{!s}'.format(winner))

if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward.txt')
    run(config_path)