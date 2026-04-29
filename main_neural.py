import pygame
import torch

from game.game_state import GameState, generate_initial_gamestate
from game.unit import Unit
from game.renderer import Renderer
from game.ai_simple import simple_enemy_turn
from game.actions import Action
from game.ai_nn import TacticsNet, encode_state, neural_policy


def main():
    pygame.init()

    # -------------------------
    # Load trained neural model
    # -------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model = TacticsNet(
        height=8,
        width=8,
        channels=14,
        max_units=8
    ).to(device)

    model.load_state_dict(torch.load("tactics_model_epoch20.pt", map_location=device))
    model.eval()

    # -------------------------
    # Create game + renderer
    # -------------------------
    gs = GameState()
    seed = 12345  # or random, or user input
    generate_initial_gamestate(gs, width=8, height=8, seed=seed)

    renderer = Renderer(gs)
    clock = pygame.time.Clock()

    running = True
    while running:
        clock.tick(60)

        # Quit handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # -------------------------
        # PLAYER = Neural Agent
        # -------------------------
        if gs.current_team == "PLAYER":
            action = neural_policy(gs, model, device)

            # Animate movement
            if action.move_to:
                unit = gs.get_unit_by_id(action.unit_id)
                old_pos = (unit.x, unit.y)
                new_pos = action.move_to

                gs.apply_move(unit, new_pos[0], new_pos[1])
                renderer.animate_slide(unit, old_pos, new_pos)

                while renderer.update_animations():
                    renderer.draw()
                    pygame.display.flip()
                    clock.tick(60)

            # Animate attack
            if action.attack_target_id is not None:
                attacker = gs.get_unit_by_id(action.unit_id)
                target = gs.get_unit_by_id(action.attack_target_id)

                # Flash target tile
                for _ in range(4):
                    renderer.draw()
                    pygame.draw.rect(
                        renderer.screen,
                        (255, 0, 0),
                        pygame.Rect(target.x * 64, target.y * 64, 64, 64),
                        4
                    )
                    pygame.display.flip()
                    pygame.time.delay(120)

                gs.apply_attack(attacker, target)

            gs.end_turn()

        # -------------------------
        # ENEMY = Simple AI
        # -------------------------
        elif gs.current_team == "ENEMY":
            enemy, move_to, target = simple_enemy_turn(gs)

            if enemy and move_to:
                old_pos = (enemy.x, enemy.y)
                gs.apply_move(enemy, move_to[0], move_to[1])
                renderer.animate_slide(enemy, old_pos, move_to)

                while renderer.update_animations():
                    renderer.draw()
                    pygame.display.flip()
                    clock.tick(60)

            if enemy and target:
                for _ in range(4):
                    renderer.draw()
                    pygame.draw.rect(
                        renderer.screen,
                        (255, 0, 0),
                        pygame.Rect(target.x * 64, target.y * 64, 64, 64),
                        4
                    )
                    pygame.display.flip()
                    pygame.time.delay(120)

                gs.apply_attack(enemy, target)

            gs.end_turn()

        # -------------------------
        # GAME OVER
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
        renderer.draw()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
