# game renderer using pygame 
# holds functions for rendering for each main file

import pygame

TILE_SIZE = 64

COLORS = {
    "GRID": (200, 200, 200),
    "PLAYER": (50, 150, 255),
    "ENEMY": (255, 100, 100),
    "HIGHLIGHT_MOVE": (100, 200, 100),
    "HIGHLIGHT_ATTACK": (200, 100, 100),
    "SWORD": (150, 180, 255),
    "AXE":   (150, 180, 255),
    "SPEAR": (150, 180, 255),
}



class Renderer:
    def __init__(self, game_state):
        pygame.init()
        self.state = game_state
        self.animations = []
        self.animation_speed = 8  # pixels / frame
        self.font = pygame.font.SysFont(None, 24) # for units
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


    # main drawing functions

    def draw(self, move_tiles=None, attack_tiles=None):


        self.screen.fill((30, 30, 30))
        self.update_animations()

        # Draw grid
        for x in range(self.state.width):
            for y in range(self.state.height):
                rect = pygame.Rect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(self.screen, COLORS["GRID"], rect, 1)

        # draw obstacles 
        self.draw_obstacles()

        # Draw highlights
        if move_tiles:
            self.draw_highlights(move_tiles, [])
        if attack_tiles:
            self.draw_highlights([], attack_tiles)

            
        # draw units    
        animated_units = {anim["unit"] for anim in self.animations if not anim["done"]}

        for u in self.state.units:
            if u.is_alive() and u not in animated_units:
                self.draw_unit(u, u.x * TILE_SIZE, u.y * TILE_SIZE)

        # draw anim unit
        for anim in self.animations:
            if not anim["done"]:
                self.draw_unit(anim["unit"], anim["px"], anim["py"])


        
        


        turn_text = self.font.render(f"Turn: {self.state.current_team}", True, (255,255,0))
        self.screen.blit(turn_text, (10, 10))


        pygame.display.flip()


    def draw_minimax_debug(self, action, score, nodes):
        if action is None:
            return

        # move arrow
        if action.move_to:
            unit = self.state.get_unit_by_id(action.unit_id)
            sx = unit.x * TILE_SIZE + TILE_SIZE // 2
            sy = unit.y * TILE_SIZE + TILE_SIZE // 2
            ex = action.move_to[0] * TILE_SIZE + TILE_SIZE // 2
            ey = action.move_to[1] * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.line(self.screen, (255, 255, 0), (sx, sy), (ex, ey), 8)

        # attack highlight
        if action.attack_target_id is not None:
            target = self.state.get_unit_by_id(action.attack_target_id)
            rect = pygame.Rect(target.x*TILE_SIZE, target.y*TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(self.screen, (255, 0, 0), rect, 4)

        # Draw text
        text1 = self.font.render(f"Minimax Score: {score}", True, (255,255,0))
        text2 = self.font.render(f"Nodes: {nodes}", True, (255,255,0))
        self.screen.blit(text1, (10, 40))
        self.screen.blit(text2, (10, 70))

    def draw_minimax_heatmap(self, action_scores):
        if not action_scores:
            return

        scores = [score for (_, score) in action_scores]
        min_s = min(scores)
        max_s = max(scores)
        span = max_s - min_s if max_s != min_s else 1

        for action, score in action_scores:
            if action.move_to is None:
                continue

            x, y = action.move_to
            # normalize 
            t = (score - min_s) / span  

            r = int(255 * (1 - t))
            g = int(255 * t)
            b = 0

            rect = pygame.Rect(x*64, y*64, 64, 64)
            s = pygame.Surface((64, 64), pygame.SRCALPHA)
            s.fill((r, g, 0, 120)) 
            self.screen.blit(s, rect)



    def draw_unit_icon(self, unit, rect):
        cx = rect.centerx
        cy = rect.centery
        color = COLORS[unit.class_type.name]

        # SWORD: two crossing lines
        if unit.class_type.name == "SWORD":
            pygame.draw.line(self.screen, color, (cx-10, cy-10), (cx+10, cy+10), 3)
            pygame.draw.line(self.screen, color, (cx+10, cy-10), (cx-10, cy+10), 3)

        # AXE: handle + blade
        elif unit.class_type.name == "AXE":
            # handle
            pygame.draw.line(self.screen, color, (cx-8, cy+10), (cx+8, cy-10), 4)
            # blade
            pygame.draw.rect(self.screen, color, (cx+2, cy-14, 10, 12))

        # SPEAR: vertical shaft + triangle tip
        elif unit.class_type.name == "SPEAR":
            pygame.draw.line(self.screen, color, (cx, cy+12), (cx, cy-12), 4)
            pygame.draw.polygon(self.screen, color, [
                (cx, cy-18),
                (cx-6, cy-8),
                (cx+6, cy-8)
            ])

    def draw_unit(self, unit, px, py):
        rect = pygame.Rect(px+8, py+8, TILE_SIZE-16, TILE_SIZE-16)
        color = COLORS["PLAYER"] if unit.team == "PLAYER" else COLORS["ENEMY"]
        pygame.draw.rect(self.screen, color, rect)
        self.draw_unit_icon(unit, rect)

        hp_text = self.font.render(str(unit.hp), True, (255,255,255))
        self.screen.blit(hp_text, (px+20, py+20))

    def draw_game_over(self, winner):
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = f"{winner} WINS!"
        surf = self.font.render(text, True, (255, 255, 0))
        rect = surf.get_rect(center=(self.screen.get_width()//2,
                                    self.screen.get_height()//2))
        self.screen.blit(surf, rect)


    def draw_obstacles(self):
        for (x, y) in self.state.obstacles:
            rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            # base color
            pygame.draw.rect(self.screen, (60, 60, 60), rect)

            # border
            pygame.draw.rect(self.screen, (20, 20, 20), rect, 3)

            # texture lines
            pygame.draw.line(self.screen, (90, 90, 90),
                            (rect.x + 8, rect.y + 8),
                            (rect.x + TILE_SIZE - 8, rect.y + TILE_SIZE - 8), 2)
            pygame.draw.line(self.screen, (90, 90, 90),
                            (rect.x + TILE_SIZE - 8, rect.y + 8),
                            (rect.x + 8, rect.y + TILE_SIZE - 8), 2)


    # ANIMATIONS
    def animate_slide(self, unit, start_pos, end_pos):
        # Convert grid coords to pixel coords
        sx = start_pos[0] * TILE_SIZE
        sy = start_pos[1] * TILE_SIZE
        ex = end_pos[0] * TILE_SIZE
        ey = end_pos[1] * TILE_SIZE

        animation = {
            "unit": unit,
            "sx": sx, "sy": sy,
            "ex": ex, "ey": ey,
            "px": sx, "py": sy,  
            "done": False
        }

        self.animations.append(animation)

    def update_animations(self):
        still_animating = False 
        new_list = []

        for anim in self.animations:
            if not anim["done"]:
                dx = anim["ex"] - anim["px"]
                dy = anim["ey"] - anim["py"]
                dist = (dx*dx + dy*dy) ** 0.5

                if dist < self.animation_speed:
                    anim["px"] = anim["ex"]
                    anim["py"] = anim["ey"]
                    anim["done"] = True
                else:
                    anim["px"] += self.animation_speed * dx / dist
                    anim["py"] += self.animation_speed * dy / dist

            # keep only unfinished animations
            if not anim["done"]:
                still_animating = True
                new_list.append(anim)

        self.animations = new_list
        return still_animating