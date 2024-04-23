import sys, random, pygame
from enum import Enum
from pygame import *

class GameState(Enum):
	PLAYING   = 0
	GAME_OVER = 1

def draw_text_at(screen, font, text, color, x_pos, y_pos):
	font_surface = font.render(text, True, color)
	text_size = font.size(text)
	x = x_pos - text_size[0]/2
	y = y_pos - text_size[1]/2
	screen.blit(font_surface, (x, y)) 


class Snake:
	body_segments = []

	# pos is a tuple (row, col) that represents a square in the grid.
	# From row and col we derive the top and left of each square
	def __init__(self, pos, dim, color, base_speed):
		left = pos[0]*SQUARE_DIM + (SQUARE_DIM - dim[0])/2
		top  = pos[1]*SQUARE_DIM + (SQUARE_DIM - dim[1])/2

		self.body_segments.clear()
		self.body_segments.append(Rect(left, top, dim[0], dim[1]))
		self.color      = color
		self.speed      = [base_speed, 0]
		self.base_speed = base_speed
		self.dim        = dim

	def head(self):
		return self.body_segments[0]

	def last(self):
		return self.body_segments[-1] #List can't ever be empty

	def grow(self):
		curr_rect  = self.last()
		new_rect   = curr_rect

		if self.speed[0] > 0:
			new_rect.left = curr_rect.left - SQUARE_DIM
		elif self.speed[0] < 0:
			new_rect.left = curr_rect.left + SQUARE_DIM
		elif self.speed[1] > 0:
			new_rect.top = curr_rect.top - SQUARE_DIM
		elif self.speed[1] < 0:
			new_rect.top = curr_rect.top + SQUARE_DIM

		self.body_segments.append(new_rect)


	def collides(self, entity):
		return self.head().colliderect(entity.rect)

	def collides_with_itself(self):
		if len(self.body_segments) < 2:
			return False

		for i, r in enumerate(self.body_segments[1:]):
			if i == 0:
				continue
			if self.head().colliderect(r):
				return True
		
		return False

	def handle_input(self, next_move):
		speed_multi = 1.0

		#if pressed_keys[pygame.K_LSHIFT] == True:
		#	speed_multi *= 2.0

		if self.speed[1] == 0 and next_move[0] == True:
			self.speed[1] = -self.base_speed*speed_multi
			self.speed[0] = 0
		if self.speed[1] == 0 and next_move[2] == True:
			self.speed[1] = self.base_speed*speed_multi
			self.speed[0] = 0
		if self.speed[0] == 0 and next_move[1] == True:
			self.speed[0] = -self.base_speed*speed_multi
			self.speed[1] = 0
		if self.speed[0] == 0 and next_move[3] == True:
			self.speed[0] = self.base_speed*speed_multi
			self.speed[1] = 0

	def draw(self, surface):
		head_r = self.head()
		debug_dot = Rect(head_r.left, head_r.top, 4, 4)

		for r in self.body_segments:
			pygame.draw.rect(surface, self.color, r)

		if DEBUG_GRID == True:
			pygame.draw.rect(surface, (255, 0, 0), debug_dot)
			for r in self.body_segments:
				debug_dot = Rect(r.left, r.top, 4, 4)
				pygame.draw.rect(surface, (255, 0, 0), debug_dot)



	def move_segment(self, segment, size):
		prev_pos = segment
		segment = segment.move(self.speed[0]*SQUARE_DIM, self.speed[1]*SQUARE_DIM)

		if segment.left < 0:
			segment.left = (COL_COUNT-1)*SQUARE_DIM + (SQUARE_DIM - self.dim[0])/2
		if segment.right > size[0]:
			segment.left = (SQUARE_DIM - self.dim[0])/2

		if segment.top < 0:
			segment.top = (ROW_COUNT-1)*SQUARE_DIM + (SQUARE_DIM - self.dim[1])/2
		if segment.bottom > size[1]:
			segment.top = (SQUARE_DIM - self.dim[1])/2

		return segment

	def move(self, size):
		prev_seg = self.head()
		self.body_segments[0] = self.move_segment(prev_seg, size)
		
		if len(self.body_segments) > 1:
			for i, segment in enumerate(self.body_segments[1:]):
					self.body_segments[i+1] = prev_seg
					prev_seg = segment

class Fruit:
	def __init__(self, pos, dim, color):
		left = pos[0]*SQUARE_DIM + (SQUARE_DIM - dim[0])/2
		top  = pos[1]*SQUARE_DIM + (SQUARE_DIM - dim[0])/2

		self.rect = pygame.Rect(left, top, dim[0], dim[1])
		self.color = color
	
	def draw(self, surface):
		pygame.draw.rect(surface, self.color, self.rect)


def debug_draw_grid(surface, grid, size):
	for (i, row) in enumerate(grid):
		start_row = Vector2(0, i*SQUARE_DIM)
		end_row   = Vector2(size[0], i*SQUARE_DIM)
		pygame.draw.line(surface, (255, 255, 255), start_row, end_row)
		
		start_col = Vector2(i*SQUARE_DIM, 0)
		end_col   = Vector2(i*SQUARE_DIM, size[1])
		pygame.draw.line(surface, (255, 255, 255), start_col, end_col)


class Board:

	entities  = []
	next_move = [False] * 4
	score     = 0

	def __init__(self, screen, bkg_color, size):
		self.screen = screen
		self.bkg_color = bkg_color
		self.size = size
		self.grid = [[0 for i in range (COL_COUNT)] for j in range(ROW_COUNT)]
	
		self.do_reset()

	def do_reset(self):
		self.entities.clear()
		
		snake_dim  = SNAKE_DIM, SNAKE_DIM
		snake_pos  = ROW_COUNT/2, COL_COUNT/2
		self.snake = Snake(snake_pos, snake_dim, (255, 255, 255), 1)

		# The board must always have at least 1 fruit available.
		self.spawn_fruit()

		self.game_state = GameState.PLAYING


	def handle_input(self):
		pressed_keys = pygame.key.get_pressed()
		
		if pressed_keys[pygame.K_w] == True:
			self.next_move = [True, False, False, False]
		if pressed_keys[pygame.K_a] == True:
			self.next_move = [False, True, False, False]
		if pressed_keys[pygame.K_s] == True:
			self.next_move = [False, False, True, False]
		if pressed_keys[pygame.K_d] == True:
			self.next_move = [False, False, False, True]


	# Main workhorse of the game. The game advances the logic one `tick` at a time
	# Every tick, the snake moves, eats a fruit if it collides with it,
	#   new fruit is spawned, etc.
	def tick(self):
		self.snake.handle_input(self.next_move)
		self.snake.move(self.size)

		if self.snake.collides_with_itself() == True:
			self.game_state = GameState.GAME_OVER
			return

		if self.snake.collides(self.entities[0]) == True:
			self.entities.remove(self.entities[0])
			self.snake.grow()
			self.spawn_fruit()
			self.score += 1

	def draw(self):
		self.screen.fill(self.bkg_color)
		
		if DEBUG_GRID == True:
			debug_draw_grid(self.screen, self.grid, self.size)

		#Draw the snake
		self.snake.draw(self.screen)

		#Draw the fruit (and maybe other entity kinds in the future?)
		self.entities[0].draw(self.screen)

		#Draw the score
		score_x = self.size[0]*0.05
		score_y = self.size[1]*0.02
		draw_text_at(self.screen, SCORE_FONT, "Score: {}".format(self.score), (255, 255, 255), score_x, score_y)

	def draw_game_over(self):
		x_pos = self.size[0]*0.50
		y_pos = self.size[1]*0.50
		draw_text_at(self.screen, GAME_OVER_FONT, "GAME OVER", (255, 0, 0), x_pos, y_pos)
		draw_text_at(self.screen, SCORE_FONT, "Press Enter to Restart", 
			   (255, 255, 255), x_pos, self.size[1]*0.55)

	def check_reset(self):
		pressed_keys = pygame.key.get_pressed()

		if pressed_keys[pygame.K_RETURN]:
			self.do_reset()

	def spawn_fruit(self):
		row = random.randint(0, ROW_COUNT-1)
		col = random.randint(0, COL_COUNT-1)
		fruit_dim = FRUIT_DIM, FRUIT_DIM

		random_r = random.randint(90, 255)
		random_g = random.randint(0, 50)
		random_b = random.randint(0, 50)
		fruit_color = (random_r, random_g, random_b)
		self.entities.append(Fruit((col, row), fruit_dim, fruit_color)) 



def main():
	pygame.init()

	global GAME_OVER_FONT
	GAME_OVER_FONT = pygame.font.Font(None, 48)

	global SCORE_FONT
	SCORE_FONT = pygame.font.Font(None, 24)

	global DEBUG_GRID
	DEBUG_GRID = False

	global GAME_TICK_INTERVAL
	GAME_TICK_INTERVAL = 150
	
	global ROW_COUNT
	global COL_COUNT
	global SQUARE_DIM
	global SNAKE_DIM
	global FRUIT_DIM

	ROW_COUNT        = 32
	COL_COUNT        = 32
	SQUARE_DIM       = 24
	SQUARE_HALF_DIM  = SQUARE_DIM / 2
	SNAKE_DIM        = 20
	FRUIT_DIM        = 16
	
	size = width, height = SQUARE_DIM*COL_COUNT, SQUARE_DIM*ROW_COUNT

	screen = pygame.display.set_mode(size)
	pygame.display.set_caption("Cobra")

	board = Board(screen, (0, 0, 0), size)
	
	game_tick_start = pygame.time.get_ticks()
	while True:
		input_tick_start = pygame.time.get_ticks()

		speedMax = 4
		
		for event in pygame.event.get():
			if event.type == pygame.QUIT: sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_F1:
					DEBUG_GRID = not DEBUG_GRID
					

		board.handle_input()

		if board.game_state == GameState.PLAYING:		
			game_tick_end = pygame.time.get_ticks()
			if game_tick_end - game_tick_start > GAME_TICK_INTERVAL:
				board.tick()
				game_tick_start = pygame.time.get_ticks()
			board.draw()
		elif board.game_state == GameState.GAME_OVER:
			board.draw_game_over()
			board.check_reset()

		input_tick_end = pygame.time.get_ticks()
		if input_tick_end - input_tick_start < 16:
			pygame.time.wait(16 - (input_tick_end - input_tick_start))

		pygame.display.flip()

	print("Hello World!")

if __name__ == "__main__":
	main()
