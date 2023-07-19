import pygame
import neat
import time
import os
import random
pygame.font.init()

WIN_WIDTH = 400
WIN_HEIGHT = 600

BIRD_IMGS = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird_0.png")))
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 30)

class Bird:
  IMGS = BIRD_IMGS
  MAX_ROTATION = 25
  ROTATION_VELOCITY = 20

  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.tilt = 0
    self.tick_count = 0
    self.velocity = 0
    self.height = self.y
    self.img = self.IMGS

  def jump(self):
    self.velocity = -6.5
    self.tick_count = 0
    self.height = self.y

  def move(self):
    self.tick_count += 1

    d = self.velocity * self.tick_count + 0.5 * (3) * self.tick_count ** 2

    if d >= 16:
      d = 16

    if d < 0:
      d -= 2

    self.y = self.y + d

    if d < 0 or self.y < self.height + 50:
      if self.tilt < self.MAX_ROTATION:
        self.tilt = self.MAX_ROTATION
    else :
      if self.tilt > -90:
        self.tilt -= self.ROTATION_VELOCITY

  def draw(self, win):
    rotated_image = pygame.transform.rotate(self.img, self.tilt)
    new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
    win.blit(rotated_image, new_rect.topleft)

  def get_mask(self):
    return pygame.mask.from_surface(self.img)

class Pipe:
  GAP = 200
  VELOCITY = 5

  def __init__(self, x):
    self.x = x
    self.height = 0
    self.gap = 100

    self.top = 0
    self.bottom = 0
    self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
    self.PIPE_BOTTOM = PIPE_IMG

    self.passed = False
    self.set_height()

  def set_height(self):
    self.height = random.randrange(0, 280)
    self.top = self.height - (self.PIPE_TOP.get_height() - 75)
    self.bottom = self.height + self.GAP

  def move(self):
    self.x -= self.VELOCITY

  def draw(self, win):
    win.blit(self.PIPE_TOP, (self.x, self.top))
    win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

  def collide(self, bird):
    bird_mask = bird.get_mask()
    top_mask = pygame.mask.from_surface(self.PIPE_TOP)
    bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

    top_offset = (self.x - bird.x, self.top - round(bird.y))
    bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

    b_point = bird_mask.overlap(bottom_mask, bottom_offset)
    t_point = bird_mask.overlap(top_mask, top_offset)

    if t_point or b_point:
      return True

def draw_window(win, birds, pipes, score):
  win.blit(BG_IMG, (0, 0))
  for pipe in pipes:
    pipe.draw(win)

  text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
  win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

  for bird in birds:
    bird.draw(win)

  pygame.display.update()

def eval_gnomes(gnomes, config):
  nets = []
  ge = []

  birds = []

  for _, gnome in gnomes:
    net = neat.nn.FeedForwardNetwork.create(gnome, config)
    nets.append(net)
    birds.append(Bird(50, 150))
    gnome.fitness = 0
    ge.append(gnome)

  pipes = [Pipe(350), Pipe(600), Pipe(850)]
  win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
  clock = pygame.time.Clock()

  score = 0

  run = True
  while run and len(birds) > 0:
    clock.tick(30)

    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        run = False
        pygame.quit()
        quit()

    pipe_ind = 0
    if len(birds) > 0:
      if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
        pipe_ind = 1

    for x, bird in enumerate(birds):
      ge[x].fitness += 0.1
      bird.move()

      output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

      if output[0] > 0.5:
        bird.jump()

    to_remove = []
    add_pipe = False

    for pipe in pipes:
      pipe.move()
      for x, bird in enumerate(birds):
        if pipe.collide(bird=bird):
          ge[x].fitness -= 1
          birds.pop(x)
          nets.pop(x)
          ge.pop(x)

        if not pipe.passed and pipe.x < bird.x:
          pipe.passed = True
          add_pipe = True

      if pipe.x + pipe.PIPE_TOP.get_width() < 0:
        to_remove.append(pipe)

    if add_pipe:
      score += 1
      add_pipe = False

      for gnome in ge:
        gnome.fitness += 5

      pipes.append(Pipe(750))

    for pipe_to_remove in to_remove:
      pipes.remove(pipe_to_remove)

    for x, bird in enumerate(birds):
      if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
        birds.pop(x)
        nets.pop(x)
        ge.pop(x)

    draw_window(win=win, birds=birds, pipes=pipes, score=score)

  # pygame.quit()
  # quit()

def run(config_file):
  config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

  population = neat.Population(config)
  population.add_reporter(neat.StdOutReporter(True))
  stats = neat.StatisticsReporter()
  population.add_reporter(stats)

  winner = population.run(eval_gnomes, 50)

if __name__ == "__main__":
  local_directory = os.path.dirname(__file__)
  config_path = os.path.join(local_directory, "config-feedforward.txt")
  run(config_path)

