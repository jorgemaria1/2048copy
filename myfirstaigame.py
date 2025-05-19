import pygame
import random
import sys
import math

# Initialize pygame
pygame.init()
# 2048 game 
# Based on the original 2048 game by Gabriele Cirulli
# Original product: https://github.com/gabrielecirulli/2048
# Licensed under the MIT license 
#
# This version may contain modifications or enhancements.
# May or may not have been coded with generative AI.

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BACKGROUND_COLOR = (250, 248, 239)
GRID_COLOR = (187, 173, 160)
TEXT_COLOR = (119, 110, 101)
BRIGHT_TEXT = (249, 246, 242)
TWINKLE_COLOR = (255, 255, 255, 200)  # White with alpha for twinkle effect

# Tile colors (BGR values of the original game)
TILE_COLORS = {
    0: (205, 193, 180),
    2: (238, 228, 218),
    4: (237, 224, 200),
    8: (242, 177, 121),
    16: (245, 149, 99),
    32: (246, 124, 95),
    64: (246, 94, 59),
    128: (237, 207, 114),
    256: (237, 204, 97),
    512: (237, 200, 80),
    1024: (237, 197, 63),
    2048: (237, 194, 46)
}

# Tile text colors
TEXT_COLORS = {
    2: TEXT_COLOR,
    4: TEXT_COLOR,
    8: BRIGHT_TEXT,
    16: BRIGHT_TEXT,
    32: BRIGHT_TEXT,
    64: BRIGHT_TEXT,
    128: BRIGHT_TEXT,
    256: BRIGHT_TEXT,
    512: BRIGHT_TEXT,
    1024: BRIGHT_TEXT,
    2048: BRIGHT_TEXT
}

# Get display info for fullscreen
info = pygame.display.Info()
SCREEN_WIDTH = info.current_w
SCREEN_HEIGHT = info.current_h

# Calculate scaling factor based on screen size
scale_factor = min(SCREEN_WIDTH / 500, SCREEN_HEIGHT / 600)

# Game parameters - now adaptive to screen size
BASE_WIDTH = 500
BASE_HEIGHT = 600
WINDOW_WIDTH = int(BASE_WIDTH * scale_factor)
WINDOW_HEIGHT = int(BASE_HEIGHT * scale_factor)
GRID_SIZE = 4
GRID_PADDING = int(15 * scale_factor)
GRID_WIDTH = WINDOW_WIDTH - 2 * GRID_PADDING
CELL_SIZE = GRID_WIDTH // GRID_SIZE
CELL_PADDING = int(15 * scale_factor)
TILE_SIZE = CELL_SIZE - 2 * CELL_PADDING
HEADER_HEIGHT = int(100 * scale_factor)

# Set up the game window in fullscreen
window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.display.set_caption("2048 Game")

# Load fonts - scaled according to display size
try:
    title_font = pygame.font.Font(None, int(80 * scale_factor))
    score_font = pygame.font.Font(None, int(40 * scale_factor))  # Increased size
    tile_fonts = {
        2: pygame.font.Font(None, int(60 * scale_factor)),
        4: pygame.font.Font(None, int(60 * scale_factor)),
        8: pygame.font.Font(None, int(60 * scale_factor)),
        16: pygame.font.Font(None, int(60 * scale_factor)),
        32: pygame.font.Font(None, int(60 * scale_factor)),
        64: pygame.font.Font(None, int(60 * scale_factor)),
        128: pygame.font.Font(None, int(50 * scale_factor)),
        256: pygame.font.Font(None, int(50 * scale_factor)),
        512: pygame.font.Font(None, int(50 * scale_factor)),
        1024: pygame.font.Font(None, int(40 * scale_factor)),
        2048: pygame.font.Font(None, int(40 * scale_factor))
    }
except:
    print("Could not load font.")
    sys.exit()

# Class for twinkle particles
class TwinkleParticle:
    def __init__(self, x, y, size, lifetime=20):
        self.x = x
        self.y = y
        self.size = size
        self.max_lifetime = lifetime
        self.lifetime = lifetime
        self.alpha = 255
        
    def update(self):
        self.lifetime -= 1
        self.alpha = int((self.lifetime / self.max_lifetime) * 255)
        return self.lifetime > 0
        
    def draw(self, surface):
        if self.lifetime > 0:
            alpha_surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            color = (*TWINKLE_COLOR[:3], self.alpha)
            pygame.draw.circle(alpha_surface, color, (self.size//2, self.size//2), self.size//2)
            surface.blit(alpha_surface, (self.x - self.size//2, self.y - self.size//2))

class Game2048:
    def __init__(self):
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.keep_playing = False
        self.add_random_tile()
        self.add_random_tile()
        self.twinkle_particles = []
        self.merged_tiles = []  # Track tiles that merged for twinkle effect

    def add_random_tile(self):
        """Add a random tile (either 2 or 4) to an empty cell"""
        empty_cells = []
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == 0:
                    empty_cells.append((i, j))
        
        if empty_cells:
            row, col = random.choice(empty_cells)
            self.grid[row][col] = 2 if random.random() < 0.9 else 4

    def has_empty_cells(self):
        """Check if there are any empty cells"""
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == 0:
                    return True
        return False

    def has_adjacent_matches(self):
        """Check if there are any adjacent cells with the same value"""
        # Check horizontally
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE - 1):
                if self.grid[i][j] == self.grid[i][j + 1] and self.grid[i][j] != 0:
                    return True
        
        # Check vertically
        for i in range(GRID_SIZE - 1):
            for j in range(GRID_SIZE):
                if self.grid[i][j] == self.grid[i + 1][j] and self.grid[i][j] != 0:
                    return True
        
        return False

    def has_available_moves(self):
        """Check if any moves are possible"""
        return self.has_empty_cells() or self.has_adjacent_matches()

    def update_twinkle_particles(self):
        """Update all twinkle particles and remove expired ones"""
        self.twinkle_particles = [particle for particle in self.twinkle_particles if particle.update()]
        self.merged_tiles = []  # Reset merged tiles for next move

    def move_left(self):
        """Move tiles left and merge if possible"""
        moved = False
        self.merged_tiles = []  # Reset merged tiles
        
        for i in range(GRID_SIZE):
            # Compress (slide all tiles to the left)
            new_row = [val for val in self.grid[i] if val != 0] + [0] * self.grid[i].count(0)
            
            # Merge adjacent tiles with the same value
            for j in range(GRID_SIZE - 1):
                if new_row[j] == new_row[j + 1] and new_row[j] != 0:
                    merged_value = new_row[j] * 2
                    new_row[j] = merged_value
                    new_row[j + 1:] = new_row[j + 2:] + [0]
                    self.score += merged_value
                    
                    # Record merge for twinkle effect if value is 64 or higher
                    if merged_value >= 64:
                        # Convert grid position to screen coordinates
                        cell_x = GRID_PADDING + j * CELL_SIZE + CELL_SIZE // 2
                        cell_y = HEADER_HEIGHT + i * CELL_SIZE + CELL_SIZE // 2
                        self.merged_tiles.append((cell_x, cell_y, merged_value))
                    
                    # Check for win
                    if merged_value == 2048 and not self.won:
                        self.won = True
            
            # Check if the row has changed
            if new_row != self.grid[i]:
                self.grid[i] = new_row
                moved = True
        
        return moved

    def move_right(self):
        """Move tiles right and merge if possible"""
        # Flip the grid horizontally, move left, then flip back
        self.grid = [row[::-1] for row in self.grid]
        moved = self.move_left()
        self.grid = [row[::-1] for row in self.grid]
        return moved

    def move_up(self):
        """Move tiles up and merge if possible"""
        # Transpose the grid, move left, then transpose back
        self.grid = [list(col) for col in zip(*self.grid)]
        moved = self.move_left()
        self.grid = [list(col) for col in zip(*self.grid)]
        return moved

    def move_down(self):
        """Move tiles down and merge if possible"""
        # Transpose the grid, move right, then transpose back
        self.grid = [list(col) for col in zip(*self.grid)]
        moved = self.move_right()
        self.grid = [list(col) for col in zip(*self.grid)]
        return moved

    def restart(self):
        """Reset the game"""
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.score = 0
        self.game_over = False
        self.won = False
        self.keep_playing = False
        self.twinkle_particles = []
        self.merged_tiles = []
        self.add_random_tile()
        self.add_random_tile()

    def generate_twinkle_effect(self):
        """Generate twinkle particles for merged tiles"""
        for x, y, value in self.merged_tiles:
            # Number of particles scales with tile value
            num_particles = min(20, int(math.log2(value)) * 2)
            
            for _ in range(num_particles):
                # Random offset within the tile
                offset_x = random.randint(-TILE_SIZE//3, TILE_SIZE//3)
                offset_y = random.randint(-TILE_SIZE//3, TILE_SIZE//3)
                particle_size = random.randint(3, 8) * scale_factor
                lifetime = random.randint(15, 30)
                
                self.twinkle_particles.append(
                    TwinkleParticle(x + offset_x, y + offset_y, particle_size, lifetime)
                )

def draw_grid(game):
    """Draw the game grid with tiles"""
    # Draw background
    window.fill(BACKGROUND_COLOR)
    
    # Center the game on the screen
    x_offset = (SCREEN_WIDTH - WINDOW_WIDTH) // 2
    y_offset = (SCREEN_HEIGHT - WINDOW_HEIGHT) // 2
    
    # Draw title
    title_surface = title_font.render("2048", True, TEXT_COLOR)
    window.blit(title_surface, (x_offset + int(20 * scale_factor), y_offset + int(20 * scale_factor)))
    
    # Draw score with larger size and more padding
    score_box_width = int(180 * scale_factor)
    score_box_height = int(80 * scale_factor)
    score_box_x = x_offset + WINDOW_WIDTH - score_box_width - int(20 * scale_factor)
    score_box_y = y_offset + int(20 * scale_factor)
    
    pygame.draw.rect(window, GRID_COLOR, 
                    (score_box_x, score_box_y, score_box_width, score_box_height), 
                    border_radius=int(5 * scale_factor))
    
    score_label = score_font.render("SCORE", True, BRIGHT_TEXT)
    score_value = score_font.render(str(game.score), True, BRIGHT_TEXT)
    
    label_rect = score_label.get_rect(center=(score_box_x + score_box_width//2, 
                                             score_box_y + score_box_height//4))
    value_rect = score_value.get_rect(center=(score_box_x + score_box_width//2, 
                                             score_box_y + 3*score_box_height//4))
    
    window.blit(score_label, label_rect)
    window.blit(score_value, value_rect)
    
    # Draw grid background
    grid_bg_x = x_offset + GRID_PADDING
    grid_bg_y = y_offset + HEADER_HEIGHT
    pygame.draw.rect(window, GRID_COLOR, 
                    (grid_bg_x, grid_bg_y, GRID_WIDTH, GRID_WIDTH), 
                    border_radius=int(6 * scale_factor))
    
    # Draw cells and tiles
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            cell_x = grid_bg_x + j * CELL_SIZE + CELL_PADDING
            cell_y = grid_bg_y + i * CELL_SIZE + CELL_PADDING
            
            # Draw empty cell
            if game.grid[i][j] == 0:
                pygame.draw.rect(window, TILE_COLORS[0], 
                                (cell_x, cell_y, TILE_SIZE, TILE_SIZE), 
                                border_radius=int(3 * scale_factor))
            else:
                # Draw tile
                value = game.grid[i][j]
                tile_color = TILE_COLORS.get(value, TILE_COLORS[2048])  # Default to 2048 color for higher values
                
                pygame.draw.rect(window, tile_color, 
                                (cell_x, cell_y, TILE_SIZE, TILE_SIZE), 
                                border_radius=int(3 * scale_factor))
                
                # Draw tile value
                text_color = TEXT_COLORS.get(value, BRIGHT_TEXT)
                font = tile_fonts.get(value, tile_fonts[2048])  # Default to 2048 font for higher values
                text = font.render(str(value), True, text_color)
                text_rect = text.get_rect(center=(cell_x + TILE_SIZE // 2, cell_y + TILE_SIZE // 2))
                window.blit(text, text_rect)
    
    # Draw twinkle particles
    for particle in game.twinkle_particles:
        particle.draw(window)

    # Draw game over or win message if needed
    if game.game_over:
        # Semi-transparent overlay
        overlay = pygame.Surface((GRID_WIDTH, GRID_WIDTH), pygame.SRCALPHA)
        overlay.fill((238, 228, 218, 179))  # RGBA with semi-transparency
        window.blit(overlay, (grid_bg_x, grid_bg_y))
        
        # Game over message
        game_over_text = title_font.render("Game Over!", True, TEXT_COLOR)
        text_rect = game_over_text.get_rect(center=(x_offset + WINDOW_WIDTH // 2, 
                                                   grid_bg_y + GRID_WIDTH // 2 - int(30 * scale_factor)))
        window.blit(game_over_text, text_rect)
        
        # Try again button
        retry_button = pygame.Rect(x_offset + WINDOW_WIDTH // 2 - int(75 * scale_factor), 
                                  grid_bg_y + GRID_WIDTH // 2 + int(20 * scale_factor), 
                                  int(150 * scale_factor), int(50 * scale_factor))
        pygame.draw.rect(window, (143, 122, 102), retry_button, border_radius=int(3 * scale_factor))
        retry_text = score_font.render("Try again", True, BRIGHT_TEXT)
        text_rect = retry_text.get_rect(center=retry_button.center)
        window.blit(retry_text, text_rect)
        return retry_button
    elif game.won and not game.keep_playing:
        # Semi-transparent overlay
        overlay = pygame.Surface((GRID_WIDTH, GRID_WIDTH), pygame.SRCALPHA)
        overlay.fill((237, 194, 46, 179))  # RGBA with semi-transparency
        window.blit(overlay, (grid_bg_x, grid_bg_y))
        
        # Win message
        win_text = title_font.render("You Win!", True, BRIGHT_TEXT)
        text_rect = win_text.get_rect(center=(x_offset + WINDOW_WIDTH // 2, 
                                             grid_bg_y + GRID_WIDTH // 2 - int(50 * scale_factor)))
        window.blit(win_text, text_rect)
        
        # Buttons
        keep_playing_button = pygame.Rect(x_offset + WINDOW_WIDTH // 2 - int(100 * scale_factor), 
                                         grid_bg_y + GRID_WIDTH // 2 + int(10 * scale_factor), 
                                         int(200 * scale_factor), int(40 * scale_factor))
        pygame.draw.rect(window, (143, 122, 102), keep_playing_button, border_radius=int(3 * scale_factor))
        keep_playing_text = score_font.render("Keep playing", True, BRIGHT_TEXT)
        text_rect = keep_playing_text.get_rect(center=keep_playing_button.center)
        window.blit(keep_playing_text, text_rect)
        
        try_again_button = pygame.Rect(x_offset + WINDOW_WIDTH // 2 - int(100 * scale_factor), 
                                      grid_bg_y + GRID_WIDTH // 2 + int(60 * scale_factor), 
                                      int(200 * scale_factor), int(40 * scale_factor))
        pygame.draw.rect(window, (143, 122, 102), try_again_button, border_radius=int(3 * scale_factor))
        try_again_text = score_font.render("Try again", True, BRIGHT_TEXT)
        text_rect = try_again_text.get_rect(center=try_again_button.center)
        window.blit(try_again_text, text_rect)
        
        return keep_playing_button, try_again_button
    
    return None

def main():
    """Main game loop"""
    game = Game2048()
    clock = pygame.time.Clock()
    fps = 60
    
    while True:
        buttons = draw_grid(game)
        
        # Generate twinkle effects for merged tiles
        if game.merged_tiles:
            game.generate_twinkle_effect()
        
        # Update twinkle particles
        game.update_twinkle_particles()
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # Handle ESC key to exit the game
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            
            # Handle keypresses
            if event.type == pygame.KEYDOWN and not (game.game_over or (game.won and not game.keep_playing)):
                moved = False
                
                if event.key == pygame.K_LEFT:
                    moved = game.move_left()
                elif event.key == pygame.K_RIGHT:
                    moved = game.move_right()
                elif event.key == pygame.K_UP:
                    moved = game.move_up()
                elif event.key == pygame.K_DOWN:
                    moved = game.move_down()
                
                # Add new random tile if tiles moved
                if moved:
                    game.add_random_tile()
                    
                    # Check if the game is over
                    if not game.has_available_moves():
                        game.game_over = True
            
            # Handle button clicks
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                if game.game_over and buttons is not None:
                    retry_button = buttons
                    if retry_button.collidepoint(mouse_pos):
                        game.restart()
                
                elif game.won and not game.keep_playing and buttons is not None:
                    keep_playing_button, try_again_button = buttons
                    if keep_playing_button.collidepoint(mouse_pos):
                        game.keep_playing = True
                    elif try_again_button.collidepoint(mouse_pos):
                        game.restart()
        
        clock.tick(fps)

if __name__ == "__main__":
    main()
