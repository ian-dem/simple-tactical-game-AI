
from game.pathfinding import astar
import random


def simple_enemy_turn(gs):
    enemies = gs.get_units_for_team("ENEMY")
    players = gs.get_units_for_team("PLAYER")

    # If no players remain, nothing to do
    if not players:
        return None, None, None

    for enemy in enemies:
        if not enemy.is_alive():
            continue
        if enemy.has_moved and enemy.has_attacked:
            continue

        moves = gs.get_legal_moves(enemy)


        # find a move -> attack
        for (mx, my) in moves:
            # simulate move
            tmp = gs.clone()
            tmp_enemy = tmp.get_unit_at(enemy.x, enemy.y)
            # clone map fail skip enemy for now
            if tmp_enemy is None: continue
            tmp.apply_move(tmp_enemy, mx, my)

            # check attacks after moving
            targets = tmp.get_attackable_units(tmp_enemy)

            if targets:
                # choose weakest target
                t = min(targets, key=lambda u: u.hp)
                return enemy, (mx, my), t
            
        # simply move closer if cant attack
        nearest = min(players, key=lambda p: abs(p.x - enemy.x) + abs(p.y - enemy.y))
        goal = (nearest.x, nearest.y)

        path = astar(gs, (enemy.x, enemy.y), goal)

        if path and len(path) > 0:
            # move up to enemy.move_range steps along the path
            steps = min(enemy.move_range, len(path))
            nx, ny = path[steps - 1]
            return enemy, (nx, ny), None

        # pathfinding fail 
        if moves:
            mx, my = random.choice(moves)
            return enemy, (mx, my), None    
        

    return None, None, None