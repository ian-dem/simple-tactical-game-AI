import pygame
from game.game_state import GameState, generate_initial_gamestate
from game.unit import Unit, UnitClass
from game.renderer import Renderer
from game.ai_simple import enemy_phase
from game.actions import Action

TILE_SIZE = 64

def main():
    pygame.init()
    gs = GameState()
    generate_initial_gamestate(gs, width=8, height=8)
    renderer = Renderer(gs)

    '''
    # add units for now 
    gs.add_unit(Unit("PLAYER", UnitClass.SWORD), 1, 1)
    gs.add_unit(Unit("ENEMY", UnitClass.AXE), 5, 5)
    gs.add_unit(Unit("PLAYER", UnitClass.SPEAR), 1, 3)
    gs.add_unit(Unit("ENEMY", UnitClass.SWORD), 3, 5)

    # add obstacles 
    for x in range(0, 6):
        gs.add_obstacle(x, 4)
    '''
    clock = pygame.time.Clock()

    turn_state = "SELECT"  # SELECT then MOVE then ATTACK
    selected_unit = None
    move_tiles = []
    attack_targets = []
    acted_units = set()


    running = True
    while running:
        clock.tick(60)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # only process mouse input on PLAYER turn
            if gs.current_team != "PLAYER":
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                gx, gy = mx // TILE_SIZE, my // TILE_SIZE

                # -------------------------
                # SELECT PHASE
                # -------------------------
                if turn_state == "SELECT":
                    u = gs.get_unit_at(gx, gy)
                    if u and u.team == "PLAYER" and u not in acted_units:
                        selected_unit = u
                        move_tiles = gs.get_legal_moves(u)
                        attack_targets = []
                        turn_state = "MOVE"
                    continue

                # -------------------------
                # MOVE PHASE
                # -------------------------
                if turn_state == "MOVE":
                    # click unit again -> cancel and mark as acted
                    if gx == selected_unit.x and gy == selected_unit.y:
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                    # clicked a legal move tile
                    if (gx, gy) in move_tiles:
                        old_pos = (selected_unit.x, selected_unit.y)
                        gs.apply_move(selected_unit, gx, gy)
                        renderer.animate_slide(selected_unit, old_pos, (gx, gy))

                        while renderer.update_animations():
                            renderer.draw(move_tiles, [(t.x, t.y) for t in attack_targets])
                            pygame.display.flip()
                            clock.tick(60)

                        attack_targets = gs.get_attackable_units(selected_unit)
                        move_tiles = []
                        turn_state = "ATTACK"
                        continue

                    # otherwise cancel selection
                    selected_unit = None
                    move_tiles = []
                    attack_targets = []
                    turn_state = "SELECT"
                    continue

                # -------------------------
                # ATTACK PHASE
                # -------------------------
                if turn_state == "ATTACK":
                    # click unit -> skip attack, end unit turn
                    if gx == selected_unit.x and gy == selected_unit.y:
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                    target = gs.get_unit_at(gx, gy)
                    if target in attack_targets:
                        # simple flash like minimax
                        for _ in range(4):
                            renderer.draw(move_tiles, [(t.x, t.y) for t in attack_targets])
                            pygame.draw.rect(
                                renderer.screen,
                                (255, 0, 0),
                                pygame.Rect(target.x*TILE_SIZE, target.y*TILE_SIZE, TILE_SIZE, TILE_SIZE),
                                4
                            )
                            pygame.display.flip()
                            pygame.time.delay(120)

                        gs.apply_attack(selected_unit, target)
                        acted_units.add(selected_unit)
                        selected_unit = None
                        move_tiles = []
                        attack_targets = []
                        turn_state = "SELECT"
                        continue

                    # clicked elsewhere -> skip attack
                    acted_units.add(selected_unit)
                    selected_unit = None
                    move_tiles = []
                    attack_targets = []
                    turn_state = "SELECT"
                    continue

        # -------------------------
        # TURN HANDLING
        # -------------------------
        if gs.current_team == "PLAYER":
            if len(acted_units) == len(gs.get_units_for_team("PLAYER")):
                gs.end_turn()
                acted_units.clear()
                selected_unit = None
                move_tiles = []
                attack_targets = []

        # -------------------------
        # ENEMY PHASE
        # -------------------------
        elif gs.current_team == "ENEMY":
            enemy_phase(gs, renderer=renderer, clock=clock, animate=True)


        # -------------------------
        # GAME OVER CHECK
        # -------------------------
        if gs.is_terminal():
            renderer.draw()
            renderer.draw_game_over(gs.winner())
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False
            continue

        # -------------------------
        # DRAW
        # -------------------------
        if gs.current_team == "PLAYER":
            renderer.draw(move_tiles, [(t.x, t.y) for t in attack_targets])
        else:
            renderer.draw()

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()