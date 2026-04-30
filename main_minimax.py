import pygame
from game.game_state import GameState, generate_initial_gamestate
from game.renderer import Renderer
from game.ai_minimax import minimax, NODE_COUNT, evaluate_root_actions
from game.ai_simple import simple_enemy_turn
from game.actions import Action
from game.unit import Unit, UnitClass

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

    running = True
    while running:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # PLAYER is controlled by minimax
        if gs.current_team == "PLAYER":
            # Run minimax
            NODE_COUNT = 0
            # score, action = minimax(gs, depth=2, alpha=-9999, beta=9999, maximizing=True)
            root_evals = evaluate_root_actions(gs, depth=2)
            action, score = max(root_evals, key=lambda x: x[1])

            # Draw debug info BEFORE executing the move
            renderer.draw()
            renderer.draw_minimax_heatmap(root_evals)
            renderer.draw_minimax_debug(action, score, NODE_COUNT)
            pygame.display.flip()
            pygame.time.delay(900)

            # Pause so humans can see the decision
            pygame.time.delay(900)

            # animate movement
            if action and action.move_to:
                unit = gs.get_unit_by_id(action.unit_id)
                old_pos = (unit.x, unit.y)
                new_pos = action.move_to
       
                gs.apply_move(unit, new_pos[0], new_pos[1])

                renderer.animate_slide(unit, old_pos, new_pos)

                while renderer.update_animations():
                    renderer.draw()
                    pygame.display.flip()
                    clock.tick(60)

            # animate attack (if any)
            if action and action.attack_target_id is not None:
                attacker = gs.get_unit_by_id(action.unit_id)
                target = gs.get_unit_by_id(action.attack_target_id)

                # Flash target tile
                for i in range(4):
                    renderer.draw()
                    pygame.draw.rect(
                        renderer.screen,
                        (255, 0, 0),
                        pygame.Rect(target.x*64, target.y*64, 64, 64),
                        4
                    )
                    pygame.display.flip()
                    pygame.time.delay(120)

                # apply attack
                gs.apply_attack(attacker, target)

            # end turn
            gs.end_turn()

        # -------------------------
        # ENEMY PHASE
        # -------------------------
        elif gs.current_team == "ENEMY":
            while True:
                actions = gs.generate_actions("ENEMY")
                if not actions:
                    break

            enemy, move_to, target = simple_enemy_turn(gs)

            if enemy and move_to:
                old_pos = (enemy.x, enemy.y)
                gs.apply_move(enemy, move_to[0], move_to[1])
                renderer.animate_slide(enemy, old_pos, move_to)

                while renderer.update_animations():
                    renderer.draw()
                    pygame.display.flip()
                    clock.tick(60)
            else: 
                fallback = actions[0]
                gs = gs.apply_action(fallback)
                continue

            if enemy and target:
                for _ in range(4):
                    renderer.draw()
                    pygame.draw.rect(
                        renderer.screen,
                        (255, 0, 0),
                        pygame.Rect(target.x*64, target.y*64, 64, 64),
                        4
                    )
                    pygame.display.flip()
                    pygame.time.delay(120)

                gs.apply_attack(enemy, target)

            gs.end_turn()



        # GAME OVER CHECK
        if gs.is_terminal():
            renderer.draw()
            renderer.draw_game_over(gs.winner())
            pygame.display.flip()
            pygame.time.delay(2000)
            running = False
            continue


        # Draw normally
        renderer.draw()

    pygame.quit()

if __name__ == "__main__":
    main()
