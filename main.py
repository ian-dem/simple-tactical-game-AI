import pygame
from game.game_state import GameState
from game.unit import Unit, UnitClass
from game.renderer import Renderer
from game.ai_simple import simple_enemy_turn

def main():
    gs = GameState()

    # Add sample units
    gs.add_unit(Unit("PLAYER", UnitClass.SWORD), 1, 1)
    gs.add_unit(Unit("ENEMY", UnitClass.AXE), 5, 5)

    renderer = Renderer(gs)

    acted_units = set()

    selected_unit = None
    move_tiles = []
    attack_targets = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                gx, gy = mx // 64, my // 64

                # No unit selected yet → try selecting one
                if selected_unit is None:
                    u = gs.get_unit_at(gx, gy)
                    if u and u.team == "PLAYER":
                        selected_unit = u
                        move_tiles = gs.get_legal_moves(u)
                        attack_targets = gs.get_attackable_units(u)

                else:
                    # If clicked an attackable enemy → attack
                    target = gs.get_unit_at(gx, gy)
                    if target in attack_targets:
                        gs.apply_attack(selected_unit, target)
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        continue

                    # If clicked a legal move tile → move
                    if (gx, gy) in move_tiles:
                        gs.apply_move(selected_unit, gx, gy)
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        continue

                    # Otherwise deselect
                    selected_unit = None
                    move_tiles = []
                    attack_targets = []
                
                if len(acted_units) == len(gs.get_units_for_team("PLAYER")):
                    gs.end_turn()
                    acted_units.clear()

                if gs.current_team == "ENEMY":
                    simple_enemy_turn(gs)
                    gs.end_turn()


        renderer.draw(move_tiles, [(t.x, t.y) for t in attack_targets])


    pygame.quit()

if __name__ == "__main__":
    main()
