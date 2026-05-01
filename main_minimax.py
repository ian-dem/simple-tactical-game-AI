import pygame
from game.game_state import GameState, generate_initial_gamestate
from game.renderer import Renderer
from game.ai_minimax import player_phase
from game.ai_simple import enemy_phase
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
            player_phase(gs, renderer=renderer, clock=clock, depth=2, animate=True)

        # -------------------------
        # ENEMY PHASE
        # -------------------------
        elif gs.current_team == "ENEMY":
            enemy_phase(gs, renderer=renderer, clock=clock, animate=True)



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
