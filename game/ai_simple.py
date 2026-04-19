def simple_enemy_turn(gs):
    enemies = gs.get_units_for_team("ENEMY")
    players = gs.get_units_for_team("PLAYER")

    for enemy in enemies:
        if not enemy.is_alive():
            continue

        # 1. Attack if possible
        targets = gs.get_attackable_units(enemy)
        if targets:
            weakest = min(targets, key=lambda u: u.hp)
            gs.apply_attack(enemy, weakest)
            continue

        # 2. Move toward nearest player
        if not players:
            return

        # Find nearest player
        px, py = min(
            [(p.x, p.y) for p in players],
            key=lambda pos: abs(pos[0] - enemy.x) + abs(pos[1] - enemy.y)
        )

        # Move one step toward player
        dx = 1 if px > enemy.x else -1 if px < enemy.x else 0
        dy = 1 if py > enemy.y else -1 if py < enemy.y else 0

        nx, ny = enemy.x + dx, enemy.y + dy
        if gs.in_bounds(nx, ny) and gs.get_unit_at(nx, ny) is None:
            gs.apply_move(enemy, nx, ny)
