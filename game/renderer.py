import pygame

TILE_SIZE = 64

COLORS = {
    "GRID": (200, 200, 200),
    "PLAYER": (50, 150, 255),
    "ENEMY": (255, 100, 100),
    "HIGHLIGHT_MOVE": (100, 200, 100),
    "HIGHLIGHT_ATTACK": (200, 100, 100),
}




class Renderer:
    def __init__(self, game_state):
        pygame.init()
        self.state = game_state
        self.screen = pygame.display.set_mode(
            (game_state.width * TILE_SIZE, game_state.height * TILE_SIZE)
        )
        pygame.display.set_caption("Tactical AI Demo")
        





    
    def draw_highlights(self, move_tiles, attack_tiles):
        for (x, y) in move_tiles:
            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLORS["HIGHLIGHT_MOVE"], rect, 3)

        for (x, y) in attack_tiles:
            rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, COLORS["HIGHLIGHT_ATTACK"], rect, 3)

    def draw(self, move_tiles=None, attack_tiles=None):
        self.screen.fill((30, 30, 30))

        # Draw grid
        for x in range(self.state.width):
            for y in range(self.state.height):
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, COLORS["GRID"], rect, 1)

        # Draw highlights
        if move_tiles:
            self.draw_highlights(move_tiles, [])
        if attack_tiles:
            self.draw_highlights([], attack_tiles)

        # Draw units
        font = pygame.font.SysFont(None, 24)
            
        for u in self.state.units:
            if not u.is_alive():
                continue
            color = COLORS["PLAYER"] if u.team == "PLAYER" else COLORS["ENEMY"]
            rect = pygame.Rect(u.x*TILE_SIZE+8, u.y*TILE_SIZE+8, TILE_SIZE-16, TILE_SIZE-16)
            pygame.draw.rect(self.screen, color, rect)

            hp_text = font.render(str(u.hp), True, (255,255,255))
            self.screen.blit(hp_text, (u.x*TILE_SIZE+20, u.y*TILE_SIZE+20))

        turn_text = font.render(f"Turn: {self.state.current_team}", True, (255,255,0))
        self.screen.blit(turn_text, (10, 10))


        pygame.display.flip()
