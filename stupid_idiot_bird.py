import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from screeninfo import get_monitors
import pygame
import shelve
import time
import math
import random
import stupid_bird_sprite
import pipe_sprites
import cloud_sprites

# Constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
SKY = (0, 204, 255)

TITLE_WIDTH = 433
TITLE_HEIGHT = 251

BUTTON_WIDTH = 281
BUTTON_HEIGHT = 133

PIPE_HEIGHT = 860.0
PIPE_WIDTH = 75.0

BIRD_WIDTH = 47.0
BIRD_HEIGHT = 30.0
BIRD_HITBOX_HEIGHT = 30.0
BIRD_HITBOX_WIDTH = 25.0

NUMBER_OF_CLOUDS = 6
CLOUD_WIDTH = 101
CLOUD_HEIGHT = 50

ADDED_ROT_ANGLE = 3
HOPPING_ANGLE = 45

#Code for putting outlines around text
# shamelessly stolen from stack overflow
_circle_cache = {}
def _circlepoints(r):
    r = int(round(r))
    if r in _circle_cache:
        return _circle_cache[r]
    x, y, e = r, 0, 1 - r
    _circle_cache[r] = points = []
    while x >= y:
        points.append((x, y))
        y += 1
        if e < 0:
            e += 2 * y - 1
        else:
            x -= 1
            e += 2 * (y - x) - 1
    points += [(y, x) for x, y in points if x > y]
    points += [(-x, y) for x, y in points if x]
    points += [(x, -y) for x, y in points if y]
    points.sort()
    return points

def render(text, font, gfcolor=WHITE, ocolor=BLACK, opx=2):
    textsurface = font.render(text, True, gfcolor).convert_alpha()
    w = textsurface.get_width() + 2 * opx
    h = font.get_height()

    osurf = pygame.Surface((w, h + 2 * opx)).convert_alpha()
    osurf.fill((0, 0, 0, 0))

    surf = osurf.copy()

    osurf.blit(font.render(text, True, ocolor).convert_alpha(), (0, 0))

    for dx, dy in _circlepoints(opx):
        surf.blit(osurf, (dx + opx, dy + opx))

    surf.blit(textsurface, (opx, opx))
    return surf
# end of code shamelessly stolen from stack overflow

#Simple collision method to use hitboxes rather than the image rects
def collided(sprite, other):
	return sprite.hitbox.colliderect(other.hitbox)

class Game(object):
	""" Represents an instance of the game """
	
	def __init__(self, horiz_scale = 1.0, verti_scale = 1.0, s_width = 1280, s_height = 720, show_fps = False, sound_on = True):
		# Setting initial variables and loading images to be passed to infinitely generated sprites
		# (Loading the image once then passing it looks messier, but vastly improves performance)
		self.score = 0
		self.blockFrames = 15
		
		self.pipe_timer = 30
		self.pipe_gap = 225
		
		self.cloud_timer = 50
		
		self.start_time = time.time()
		
		self.game_over = False
		self.first_input_recieved = False
		self.paused = False
		self.new_high_score = False
		self.sound_on = sound_on
		
		self.show_fps = show_fps
		self.fps = 60
		
		self.screen_width = s_width
		self.screen_height = s_height
		self.h_scale = horiz_scale
		self.v_scale = verti_scale
		
		self.TOP_PIPE_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/top_pipe.png")).convert_alpha()
		self.TOP_PIPE_IMAGE = pygame.transform.scale(self.TOP_PIPE_IMAGE, (int(PIPE_WIDTH * horiz_scale), int(PIPE_HEIGHT * verti_scale)))
		self.BOTTOM_PIPE_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/bottom_pipe.png")).convert_alpha()
		self.BOTTOM_PIPE_IMAGE = pygame.transform.scale(self.BOTTOM_PIPE_IMAGE, (int(PIPE_WIDTH * horiz_scale), int(PIPE_HEIGHT * verti_scale)))
		
		self.CLOUD_1_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/cloud_1.png")).convert_alpha()
		self.CLOUD_1_IMAGE = pygame.transform.scale(self.CLOUD_1_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		self.CLOUD_2_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/cloud_2.png")).convert_alpha()
		self.CLOUD_2_IMAGE = pygame.transform.scale(self.CLOUD_2_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		self.CLOUD_3_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/cloud_3.png")).convert_alpha()
		self.CLOUD_3_IMAGE = pygame.transform.scale(self.CLOUD_3_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		self.CLOUD_4_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/cloud_4.png")).convert_alpha()
		self.CLOUD_4_IMAGE = pygame.transform.scale(self.CLOUD_4_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		self.CLOUD_5_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/cloud_5.png")).convert_alpha()
		self.CLOUD_5_IMAGE = pygame.transform.scale(self.CLOUD_5_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		self.BEST_CLOUD_IMAGE = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/thebestcloud.png")).convert_alpha()
		self.BEST_CLOUD_IMAGE = pygame.transform.scale(self.BEST_CLOUD_IMAGE, (int(CLOUD_WIDTH * self.h_scale), int(CLOUD_HEIGHT * self.v_scale)))
		
		self.gravity = 15
		self.player_x = int(self.screen_width / 5)
		self.player_y = 360
		self.player_velo_y = 0
		self.player_rot_angle = 0
		self.player_on_ground = False
		self.player_between_pipes = False
		
		self.hop_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "resources/hop.ogg"))
		self.hit_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "resources/hit.ogg"))
		
		self.clouds_list = pygame.sprite.Group()
		self.pipes_list = pygame.sprite.Group()
		self.scorezone_list = pygame.sprite.Group()
		self.all_sprites_list = pygame.sprite.Group()
		
		self.bird = stupid_bird_sprite.Bird(self.h_scale, self.v_scale)
		self.bird.moveTo(self.player_x, self.player_y)
		self.all_sprites_list.add(self.bird)
		
		# retrieving high score
		try:
			high_score_tracker = shelve.open('high_score.txt')
			try:
				self.high_score = high_score_tracker['high_score']
			except:
				self.high_score = 0
				high_score_tracker['high_score'] = 0
			high_score_tracker.close()
		except:
			if not os.path.exists(os.path.expanduser('~/Documents/stupid_idiot_bird/high_score.txt')):
				os.makedirs(os.path.expanduser('~/Documents/stupid_idiot_bird/high_score.txt'))
			high_score_tracker = shelve.open(os.path.expanduser('~/Documents/stupid_idiot_bird/high_score.txt'))
			try:
				self.high_score = high_score_tracker['high_score']
			except:
				self.high_score = 0
				high_score_tracker['high_score'] = 0
			high_score_tracker.close()

	
	# set player's upward velocity to 15, reset bird's rotation to 45 degrees, play a sound if applicable
	def hop(self):
		self.player_velo_y = -15.0
		self.bird.rot_center(HOPPING_ANGLE - self.player_rot_angle)
		self.player_rot_angle = HOPPING_ANGLE
		if self.sound_on:
			self.hop_sound.play()
	
	# self explanitory method name
	def process_events(self):
		# if game is over, subtract 1 from blockFrames (variable used to block input when game ends)
		if self.game_over:
			self.blockFrames-=1
			
		for event in pygame.event.get():
			# if the game is quit, save the high score if needed then return false (ending the game)
			if event.type == pygame.QUIT:
				try:
					high_score_tracker = shelve.open('high_score.txt')
					if self.high_score > high_score_tracker['high_score']:
						high_score_tracker['high_score'] = self.high_score
					high_score_tracker.close()
				except:
					high_score_tracker = shelve.open(os.path.expanduser('~/Documents/stupid_idiot_bird/high_score.txt'))
					if self.high_score > high_score_tracker['high_score']:
						high_score_tracker['high_score'] = self.high_score
					high_score_tracker.close()

				return False
			if event.type == pygame.KEYDOWN:
				# if player pressed space or up arrow, hop
				if (event.key == pygame.K_UP or event.key == pygame.K_SPACE) and not self.game_over:
					if not self.paused:
						self.hop()
					if not self.first_input_recieved:
						self.first_input_recieved = True
				# if the game is over and r or space is pressed (and not blocked) or if escape is pressed at any point
				elif ((event.key == pygame.K_r or ((event.key == pygame.K_SPACE or event.key == pygame.K_UP) and self.blockFrames <= 0)) and self.game_over) or event.key == pygame.K_ESCAPE:
					# update the high score
					try:
						high_score_tracker = shelve.open('high_score.txt')
						if self.high_score > high_score_tracker['high_score']:
							high_score_tracker['high_score'] = self.high_score
						high_score_tracker.close()
					except:
						high_score_tracker = shelve.open(os.path.expanduser('~/Documents/stupid_idiot_bird/high_score.txt'))
						if self.high_score > high_score_tracker['high_score']:
							high_score_tracker['high_score'] = self.high_score
						high_score_tracker.close()
					
					# if the key was r or space, play again. Else return false and end the game.
					if event.key == pygame.K_r or event.key == pygame.K_SPACE or event.key == pygame.K_UP:
						self.__init__(self.h_scale, self.v_scale, self.screen_width, self.screen_height, self.show_fps, self.sound_on)
					else:
						return False
				# if F3 is pressed, show debug info
				elif event.key == pygame.K_F3:
					self.show_fps = not self.show_fps
				# if p is pressed, toggle paused state
				elif event.key == pygame.K_p and self.first_input_recieved and not self.game_over:
					self.paused = not self.paused
		
		return True
	
	# self explanitory method name
	def run_logic(self):
		# only run if not paused
		if not self.paused:
		
			# increment timers, then add new pipes and clouds if needed.
			self.pipe_timer += 1
			self.cloud_timer += 1
			
			if self.pipe_timer >= 60 and self.first_input_recieved:
				self.pipe_timer = 0
				bottom_pipe = pipe_sprites.Bottom_pipe(self.BOTTOM_PIPE_IMAGE, self.pipe_gap, self.h_scale, self.v_scale, self.screen_width, self.screen_height)
				between_pipe = pipe_sprites.Between_pipe(bottom_pipe, self.pipe_gap, self.h_scale, self.v_scale)
				top_pipe = pipe_sprites.Top_pipe(bottom_pipe, self.TOP_PIPE_IMAGE, self.pipe_gap, self.h_scale, self.v_scale)
				
				self.all_sprites_list.add(bottom_pipe)
				self.all_sprites_list.add(top_pipe)
				self.pipes_list.add(bottom_pipe)
				self.pipes_list.add(top_pipe)
				self.scorezone_list.add(between_pipe)
			
			if self.cloud_timer >= 55:
				self.cloud_timer = 0
				num = random.randint(1, NUMBER_OF_CLOUDS)
				if num == 1:
					cloud_image = self.CLOUD_1_IMAGE
				elif num == 2:
					cloud_image = self.CLOUD_2_IMAGE
				elif num == 3:
					cloud_image = self.CLOUD_3_IMAGE
				elif num == 4:
					cloud_image = self.CLOUD_4_IMAGE
				elif num == 5:
					cloud_image = self.CLOUD_5_IMAGE
				elif num == 6:
					cloud_image = self.BEST_CLOUD_IMAGE
					
				cloud = cloud_sprites.Cloud(cloud_image, self.h_scale, self.screen_width, self.screen_height)
				
				self.clouds_list.add(cloud)
			
			# set the player's new y positon according to the players vertical velocity
			self.player_y += self.player_velo_y
			
			# apply gravity to the player if not at terminal velocity and not on the ground (increment their vertical velocity and adjust their angle)
			if self.player_velo_y < self.gravity and not self.player_on_ground:
				self.player_velo_y += 1
				self.bird.rot_center(-ADDED_ROT_ANGLE)
				self.player_rot_angle -= ADDED_ROT_ANGLE % 360
			
			# keep the player from going off the top of the screen, kill the player if they go off the bottom of the screen
			if self.player_y < 0:
				self.player_y = 0
			elif int(self.player_y * self.v_scale) > self.screen_height:
				self.game_over = True
			
			# update all sprites
			if not self.game_over:
				self.all_sprites_list.update()
				self.clouds_list.update()
				self.scorezone_list.update()
			
			# detect if player hit a scorezone, manipulate score and gap between pipes if needed
			score_hit_list = pygame.sprite.spritecollide(self.bird, self.scorezone_list, True, collided)
			for zone in score_hit_list:
				if not self.game_over:
					self.score += 1
					if self.score % 10 == 0 and self.pipe_gap > 145:
						self.pipe_gap -= 5
					elif self.score % 10 == 0 and self.pipe_gap > 60:
						self.pipe_gap -= 1
			
			# detect if player hit a pipe, end the game and manipulate the bird's position according to the type of collision
			self.player_on_ground = False
			pipe_hit_list = pygame.sprite.spritecollide(self.bird, self.pipes_list, False, collided)
			for pipe in pipe_hit_list:
				if not self.game_over:
					if self.sound_on:
						self.hit_sound.play()
					self.game_over = True
				
				# get pipe's position and calculate if the player is between a top pipe and a bottom pipe
				pipe_x_pos = pipe.hitbox.left/self.h_scale
				pipe_y_pos = 0
				
				if isinstance(pipe, pipe_sprites.Top_pipe):
					pipe_y_pos = (pipe.hitbox.bottom - 50)/self.v_scale
				else:
					pipe_y_pos = (pipe.hitbox.top + 50)/self.v_scale
				
				player_between_pipes = False
				
				if isinstance(pipe, pipe_sprites.Top_pipe) and self.player_y >= pipe_y_pos and self.player_y <= pipe_y_pos + self.pipe_gap - 100 and self.bird.hitbox.right >= pipe_x_pos:
					player_between_pipes = True
				if isinstance(pipe, pipe_sprites.Bottom_pipe) and self.player_y <= pipe_y_pos and self.player_y >= pipe_y_pos - self.pipe_gap + 100 and self.bird.hitbox.right >= pipe_x_pos:
					player_between_pipes = True
				
				# if the player landed on top of a bottom pipe, reset vertical velocity, push bird out of the pipe, and roll off the side of it
				if self.player_velo_y > 0 and isinstance(pipe, pipe_sprites.Bottom_pipe) and player_between_pipes:
					self.player_velo_y = 0
					self.player_y = int(pipe.hitbox.top / self.v_scale) - ((((BIRD_HITBOX_HEIGHT + BIRD_HITBOX_WIDTH)/2)/2) - 1)
					self.player_x += 2
					self.bird.rot_center(-ADDED_ROT_ANGLE)
					self.player_rot_angle -= ADDED_ROT_ANGLE % 360
					self.player_on_ground = True
				# if the bird hit the bottom of a top pipe, reset vertical velocity and push bird out of the pipe
				elif self.player_velo_y < 0 and isinstance(pipe, pipe_sprites.Top_pipe) and player_between_pipes:
					self.player_velo_y = 0
					self.player_y = int((pipe.hitbox.bottom + (.5 * BIRD_HITBOX_HEIGHT)) / self.v_scale) + 1
				# if bird hit the side of any pipe, push the bird out of the pipe and let gravity do its job
				# fun fact: I had to actually go to one of my professors to figure out how to make it look like the bird wasn't hitting a god damn forcefield
				elif not self.player_on_ground and not player_between_pipes:
					pos_horiz_offset = (math.cos(math.radians(self.player_rot_angle)) * (.5 * BIRD_HITBOX_WIDTH)) - (math.sin(math.radians(self.player_rot_angle)) * (.5 * BIRD_HITBOX_HEIGHT))
					neg_horiz_offset = (math.cos(math.radians(self.player_rot_angle)) * (.5 * BIRD_HITBOX_WIDTH)) - (math.sin(math.radians(self.player_rot_angle)) * (.5 * (-1 * BIRD_HITBOX_HEIGHT)))
					if pos_horiz_offset > neg_horiz_offset:
						self.player_x = pipe_x_pos - pos_horiz_offset
					else:
						self.player_x = pipe_x_pos - neg_horiz_offset 
					
			# move the bird to its new position	
			self.bird.moveTo(int(self.player_x * self.h_scale), int(self.player_y * self.v_scale))
			if self.player_y * self.v_scale > self.screen_height + 50:
				self.bird.kill()
			
			# outdated code
			'''if self.game_over:
				for pipe in self.pipes_list:
					pipe.setMoving(False)'''
			
			# if no input has been given, keep the bird hopping around the middle of the screen
			if not self.first_input_recieved and int(self.player_y * self.v_scale) > (self.screen_height / 2) + (.5 * BIRD_HEIGHT):
				self.hop()
				
			# if a new high score has been achieved, update the high score variable and make a note of it for later
			if self.score > self.high_score:
				self.high_score = self.score
				self.new_high_score = True
	
	# sets the time at the start of the frame for purposes of fps tracking
	def set_start_time(self, time):
		self.start_time = time
	
	# sets the fps value to be displayed, calculated outside this class in the main method
	def set_fps(self, frames):
		self.fps = frames
	
	# self explanitory method name
	def display_frame(self, screen):
		# draw the sky
		pygame.draw.rect(screen, SKY, pygame.Rect(0, 0, self.screen_width, self.screen_height))
		
		# draw the clouds then everything else
		self.clouds_list.draw(screen)
		self.all_sprites_list.draw(screen)
		
		# if the game isn't over, display the score and high score in the corner of the screen
		if not self.game_over:
			font = pygame.font.SysFont("Calibri", 25, True, False)
			screen.blit(render('Score: ' + str(self.score), font), [10, 10])
			if not self.high_score == 0:
				screen.blit(render('High Score: ' + str(self.high_score), font), [10, 40])
		
		# if the player hasn't pressed anything yet, display the tooltip telling them how to hop
		if not self.first_input_recieved:
			font = pygame.font.SysFont("Calibri", 30, True, False)
			text = font.render("press SPACE to hop", True, WHITE)
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			y = 500 * self.v_scale
			screen.blit(render("press SPACE to hop", font), [center_x, y])
		
		# if the game is over, display the end screen text
		if self.game_over:
			font = pygame.font.SysFont("Calibri", 40, True, False)
			
			text = font.render("or press ESC to return to the Main Menu", True, WHITE)
			center_y = (self.screen_height // 2) + (text.get_height() * 3.5)
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			screen.blit(render("or press ESC to return to the Main Menu", font), [center_x, center_y])
			
			text = font.render("press R or SPACE to restart", True, WHITE)
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			center_y -= (text.get_height() * 1.5)
			screen.blit(render("press R or SPACE to restart", font), [center_x, center_y])

			text = font.render("HIGH SCORE: " + str(self.high_score), True, WHITE)
			center_y -= text.get_height() * 3
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			screen.blit(render("HIGH SCORE: " + str(self.high_score), font), [center_x, center_y])
			
			text = font.render("SCORE: " + str(self.score), True, WHITE)
			center_y -= text.get_height() * 1.5
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			screen.blit(render("SCORE: " + str(self.score), font), [center_x, center_y])
			
			if self.new_high_score:
				text = font.render("NEW HIGH SCORE!", True, WHITE)
				center_y -= text.get_height() * 1.5
				center_x = (self.screen_width // 2) - (text.get_width() // 2)
				screen.blit(render("NEW HIGH SCORE!", font), [center_x, center_y])
			else:
				text = font.render("GAME OVER", True, WHITE)
				center_y -= text.get_height() * 1.5
				center_x = (self.screen_width // 2) - (text.get_width() // 2)
				screen.blit(render("GAME OVER", font), [center_x, center_y])
				
		# if the game is paused, display PAUSED in the middle of the screen
		if self.paused:
			font = pygame.font.SysFont("Calibri", 40, True, False)
			text = font.render("PAUSED", True, WHITE)
			center_x = (self.screen_width // 2) - (text.get_width() // 2)
			center_y = (self.screen_height // 2) - (text.get_height() // 2)
			screen.blit(render("PAUSED", font), [center_x, center_y])
		
		# if debug info should be shown, show it in the corner of the screen
		if self.show_fps:
				font = pygame.font.SysFont("Calibri", 25, True, False)
				screen.blit(render(('FPS: ' + str(self.fps)), font), [self.screen_width - 150, 10])
				screen.blit(render(('pyAngle: ' + str(self.player_rot_angle)), font), [self.screen_width - 150, 50])
		
		# flip the display (i.e. actually draw everything rather than just thinking about drawing it)
		pygame.display.flip()

# Main method, execution starts here		
def main():
	# set up some initial stuff to make the sound work, then initiate pygame
	pygame.mixer.pre_init(44100, -16, 2, 1024)
	pygame.mixer.init()
	pygame.init()
	
	# getting screen size and setting the game to fullscreen
	#ctypes.windll.user32.SetProcessDPIAware()
	#true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
	monitor = get_monitors()[0]
	true_res = (monitor.width, monitor.height)
	screen = pygame.display.set_mode(true_res,pygame.FULLSCREEN)
	screen_width, screen_height = pygame.display.get_surface().get_size()
	
	# getting the amount to scale everything by for proper display
	horizontal_scale = screen_width / 1280
	vertical_scale = screen_height / 720
	
	# doesn't do anything anymore unless you somehow get the game into windowed mode
	icon = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/icon.png"))
	icon.set_colorkey(WHITE)
	pygame.display.set_icon(icon)
	pygame.display.set_caption("Stupid Idiot Bird Can't Fly")
	
	# load and set the positition of the title image
	title_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/title.png")).convert()
	title_image = pygame.transform.scale(title_image, (int(TITLE_WIDTH * horizontal_scale), int(TITLE_HEIGHT * vertical_scale)))
	title_image.set_colorkey(WHITE)
	title_x = screen_width // 2 - int(TITLE_WIDTH * horizontal_scale / 2)
	title_y = screen_height // 5
	
	# setting up button images, positions, and hitboxes
	play_button_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/play_button.png")).convert()
	play_button_image = pygame.transform.scale(play_button_image, (int(BUTTON_WIDTH * horizontal_scale), int(BUTTON_HEIGHT * vertical_scale)))
	play_button_image.set_colorkey(WHITE)
	play_button_hover_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/play_button_hover.png")).convert()
	play_button_hover_image = pygame.transform.scale(play_button_hover_image, (int(BUTTON_WIDTH * horizontal_scale), int(BUTTON_HEIGHT * vertical_scale)))
	play_button_hover_image.set_colorkey(WHITE)
	
	play_button_x_1 = (screen_width) // 5
	play_button_x_2 = (screen_width) // 5 + int(BUTTON_WIDTH * horizontal_scale)
	play_button_y_1 = title_y + int(350 * vertical_scale)
	play_button_y_2 = play_button_y_1 + int(BUTTON_HEIGHT * vertical_scale)
	
	quit_button_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/quit_button.png")).convert()
	quit_button_image = pygame.transform.scale(quit_button_image, (int(BUTTON_WIDTH * horizontal_scale), int(BUTTON_HEIGHT * vertical_scale)))
	quit_button_image.set_colorkey(WHITE)
	quit_button_hover_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/quit_button_hover.png")).convert()
	quit_button_hover_image = pygame.transform.scale(quit_button_hover_image, (int(BUTTON_WIDTH * horizontal_scale), int(BUTTON_HEIGHT * vertical_scale)))
	quit_button_hover_image.set_colorkey(WHITE)
	
	quit_button_x_1 = (3 * ((screen_width) // 5))
	quit_button_x_2 = (3 * ((screen_width) // 5)) + int(BUTTON_WIDTH * horizontal_scale)
	quit_button_y_1 = title_y + int(350 * vertical_scale)
	quit_button_y_2 = quit_button_y_1 + int(BUTTON_HEIGHT * vertical_scale)
	
	sound_on_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/sound_on.png")).convert_alpha()
	sound_on_image = pygame.transform.scale(sound_on_image, (int(13 * horizontal_scale), int(11 * vertical_scale)))
	sound_off_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "resources/sound_off.png")).convert_alpha()
	sound_off_image = pygame.transform.scale(sound_off_image, (int(13 * horizontal_scale), int(11 * vertical_scale)))
	sound_button_x1 = 10
	sound_button_x2 = 10 + (int(13 * horizontal_scale))
	sound_button_y1 = screen_height - (20 + int(11 * vertical_scale))
	sound_button_y2 = screen_height - 20
	
	# setting up other inital variables
	click_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), "resources/click.ogg"))
	
	done = False
	clock = pygame.time.Clock()
	
	sound_on = True
	
	intro = True
	playing = True
	
	# while the program is running
	while not done:
		pygame.mouse.set_visible(True)
		# while we're on the title screen
		while intro:
			# detect mouse clicks and check if they're on any of our buttons
			for event in pygame.event.get():
				# if they closed the game, exit all loops (which basically exits the game)
				if event.type == pygame.QUIT:
					intro = False
					playing = False
					done = True
				elif event.type == pygame.MOUSEBUTTONDOWN:
					# if they left-clicked
					if event.button == 1:
						# if the mouse was over the play button, turn off the menu and turn on the game
						if event.pos[0] in range(play_button_x_1, play_button_x_2) and event.pos[1] in range(play_button_y_1, play_button_y_2):
							if sound_on:
								click_sound.play()
							intro = False
							playing = True
						# if the mouse was over the quit button, exit the game
						if event.pos[0] in range(quit_button_x_1, quit_button_x_2) and event.pos[1] in range(quit_button_y_1, quit_button_y_2):
							if sound_on:
								click_sound.play()
							intro = False
							playing = False
							done = True
						# if the mouse was over the sound toggle button, toggle the sound (WOW!)
						if event.pos[0] in range(sound_button_x1, sound_button_x2) and event.pos[1] in range(sound_button_y1, sound_button_y2):
							sound_on = not sound_on
							if sound_on:
								click_sound.play()
								
				# if there was no mouse click and it was in fact a keystroke on the key ESC, then exit the game
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						intro = False
						playing = False
						done = True
						
			# get the mouse position for reasons unrelated to clicking			
			mouse = pygame.mouse.get_pos()
			
			# draw everything
			pygame.draw.rect(screen, SKY, pygame.Rect(0, 0, screen_width, screen_height))
			screen.blit(title_image, [title_x, title_y])
			
			# when drawing the buttons, if the mouse is over the button then display the lighter colored variant of it
			if mouse[0] in range(play_button_x_1, play_button_x_2) and mouse[1] in range(play_button_y_1, play_button_y_2):
				screen.blit(play_button_hover_image, [play_button_x_1, play_button_y_1])
			else:
				screen.blit(play_button_image, [play_button_x_1, play_button_y_1])
				
			if mouse[0] in range(quit_button_x_1, quit_button_x_2) and mouse[1] in range(quit_button_y_1, quit_button_y_2):
				screen.blit(quit_button_hover_image, [quit_button_x_1, quit_button_y_1])
			else:
				screen.blit(quit_button_image, [quit_button_x_1, quit_button_y_1])
			
			# display the correct version of the sound toggle button, which doubles as an indicator of whether or not sound is on
			if sound_on:
				screen.blit(sound_on_image, [sound_button_x1, sound_button_y1])
			else:
				screen.blit(sound_off_image, [sound_button_x1, sound_button_y1])
						
			pygame.display.flip()
		
		# upon exiting the main menu loop, we immediately set the variable determining if we should be in the main menu loop to true again
		# so that in the future, when we leave the game we go back to the menu
		intro = True
		
		# hide the mouse, initiate the start_time variable, and start up a new game 
		pygame.mouse.set_visible(False)
		
		start_time = 0
		
		game = Game(horizontal_scale, vertical_scale, screen_width, screen_height, False, sound_on)
		
		# while playing, update the framerate if neede, process events, run logic, display a frame, then tick the clock
		while playing:
			update_fps = False
			if game.show_fps and time.time() - game.start_time >= .25:
				game.set_start_time(time.time())
				update_fps = True
				
			playing = game.process_events()
			
			game.run_logic()
			
			game.display_frame(screen)
			
			clock.tick(60) # this keeps us locked to a max of 60 fps
			
			if game.show_fps and update_fps:
				game.set_fps(math.floor(1.0 / (time.time() - game.start_time)))
	
	# when all that is done, quit the game
	pygame.quit()
	
if __name__ == "__main__":
	main()
