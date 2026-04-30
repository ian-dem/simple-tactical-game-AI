from game.pathfinding import astar
import random
import pygame

def _choose_attack_move_for_enemy(gs, enemy):
    """Return (move_to, target) where target is a Unit or None."""
    moves = set(gs.get_legal_moves(enemy))
    

    # try to find moves that enable an attack (prefer weakest target)
    for (mx, my) in list(moves):
        tmp = gs.clone()
        tmp_enemy = tmp.get_unit_by_id(enemy.id)
        if tmp_enemy is None:
            continue
        tmp.apply_move(tmp_enemy, mx, my)
        targets = tmp.get_attackable_units(tmp_enemy)
        if targets:
            t = min(targets, key=lambda u: u.hp)
            return (mx, my), t.id

    # no target -> move toward nearest player
    players = gs.get_units_for_team("PLAYER")
    if players:
        # simply move closer if cant attack
        nearest = min(players, key=lambda p: abs(p.x - enemy.x) + abs(p.y - enemy.y))
        goal = (nearest.x, nearest.y)

        path = astar(gs, (enemy.x, enemy.y), goal)

        if path and len(path) > 0:
            # move up to enemy.move_range steps along the path
            steps = min(enemy.move_range, len(path))
            nx, ny = path[steps - 1]
            return (nx, ny), None



    # Fallback random legal move
    if moves:
        mx, my = random.choice(list(moves))
        return (mx, my), None

    return None, None


def enemy_phase(gs, renderer=None, clock=None, animate=True):
    """
    Execute the entire ENEMY phase on the provided GameState `gs`.
    If renderer and clock are provided and animate is True, perform the same animations. 
    (this really needs to be refactored) Otherwise, only mutate `gs`.
    Returns True if the phase ran (i.e., it was ENEMY's turn), False otherwise.
    """
    if gs.current_team != "ENEMY":
        return False

    # if no enemy units, just end turn
    enemies = gs.get_units_for_team("ENEMY")
    if not enemies:
        gs.end_turn()
        return True

    # Loop until no actions remain for ENEMY
    while True:
        actions = gs.generate_actions("ENEMY")
        if not actions:
            break

        # Find an enemy that can act (respect has_moved/has_attacked flags)
        acted_any = False
        for enemy in enemies:
            if not enemy.is_alive():
                continue
            if enemy.has_moved and enemy.has_attacked:
                continue

            move_to, target_id = _choose_attack_move_for_enemy(gs, enemy)
            if move_to is None:
                break 
            
            target = None
            if target_id: 
                target = gs.get_unit_by_id(target_id)
            
            

            # If move_to equals current position and no target treat as skip
            if (move_to[0], move_to[1]) == (enemy.x, enemy.y) and target is None:
                # fallback to an Action if generate_actions returned something else
                # pick first available action for this enemy
                fallback = next((a for a in actions if a.unit_id == enemy.id), None)
                if fallback:
                    gs = gs.apply_action(fallback)
                    acted_any = True
                    break
                else:
                    continue

            # apply move & anim
            old_pos = (enemy.x, enemy.y)
            gs.apply_move(enemy, move_to[0], move_to[1])
            if renderer and animate:
                renderer.animate_slide(enemy, old_pos, move_to)
                # run animation frames
                while renderer.update_animations():
                    renderer.draw()
                    if renderer.screen:
                        pygame.display.flip()
                    if clock:
                        clock.tick(60)

            # if target found attack & anim
            if target:
                
                if renderer and animate:
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

            # Mark that this enemy acted (the GameState should track a unit has_moved/has_attacked if needed)
            acted_any = True
            break  # recompute actions after each unit acts

        if not acted_any:
            # No enemy could act this iteration; break to avoid infinite loop
            break

    gs.end_turn()
    return True
