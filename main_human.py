import pygame
from game.game_state import GameState
from game.unit import Unit, UnitClass
from game.renderer import Renderer
from game.ai_simple import simple_enemy_turn

def main():
    gs = GameState()

    # manual add units for now
    gs.add_unit(Unit("PLAYER", UnitClass.SWORD), 1, 1)
    gs.add_unit(Unit("ENEMY", UnitClass.AXE), 5, 5)
    gs.add_unit(Unit("PLAYER", UnitClass.SWORD), 1, 3)
    gs.add_unit(Unit("ENEMY", UnitClass.AXE), 3, 5)

    renderer = Renderer(gs)

    acted_units = set()

    turn_state = "SELECT"  # SELECT then MOVE then ATTACK
    selected_unit = None
    move_tiles = []
    attack_targets = []
    acted_units = set()


    running = True
    while running:
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                gx, gy = mx // 64, my // 64

                # -------------------------
                # SELECT PHASE
                # -------------------------
                if turn_state == "SELECT":
                    u = gs.get_unit_at(gx, gy)
                    if u and u.team == "PLAYER" and u not in acted_units:
                        selected_unit = u
                        move_tiles = gs.get_legal_moves(u)
                        turn_state = "MOVE"
                    continue

                # -------------------------
                # MOVE PHASE
                # -------------------------
                if turn_state == "MOVE":
                    # if player clicks the unit again, cancel and end turn for that unit
                    if gx == selected_unit.x and gy == selected_unit.y:
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                    # if clicked a legal move tile move
                    if (gx, gy) in move_tiles:
                        old_pos = (selected_unit.x, selected_unit.y)
                        gs.apply_move(selected_unit, gx, gy)
                        renderer.animate_slide(selected_unit, old_pos, (gx, gy))
                        attack_targets = gs.get_attackable_units(selected_unit)
                        move_tiles = []
                        turn_state = "ATTACK"
                        continue

                    # otherwise cancel selection
                    selected_unit = None
                    move_tiles = []
                    turn_state = "SELECT"
                    continue

                # -------------------------
                # ATTACK PHASE
                # -------------------------
                if turn_state == "ATTACK" and attack_targets:
                    # if player clicks the unit end turn
                    
                    if gx == selected_unit.x and gy == selected_unit.y:
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                    # Player clicks an attackable enemy, attack then end unit turn
                    target = gs.get_unit_at(gx, gy)
                    if target in attack_targets:
                        gs.apply_attack(selected_unit, target)
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                # Otherwise skip attack
                else:
                    acted_units.add(selected_unit)
                    selected_unit = None
                    move_tiles = []
                    attack_targets = []
                    turn_state = "SELECT"
                    continue

        # After processing events each frame:
        if gs.current_team == "PLAYER":
            if len(acted_units) == len(gs.get_units_for_team("PLAYER")):
                gs.end_turn()
                acted_units.clear()

                # Enemy AI turn
                simple_enemy_turn(gs)
                gs.end_turn()


        # GAME OVER CHECK
        if gs.is_terminal():
            renderer.draw()
            renderer.draw_game_over(gs.winner())
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False
            continue


        renderer.draw(move_tiles, [(t.x, t.y) for t in attack_targets])



    pygame.quit()

if __name__ == "__main__":
    main()
