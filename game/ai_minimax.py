#
NODE_COUNT = 0



def evaluate_state(gs):
    if gs.is_terminal():
        player_alive = any(u.team == "PLAYER" and u.is_alive() for u in gs.units)
        enemy_alive = any(u.team == "ENEMY" and u.is_alive() for u in gs.units)
        if player_alive and not enemy_alive:
            return 10_000
        if enemy_alive and not player_alive:
            return -10_000
        return 0

    score = 0
    for u in gs.units:
        if not u.is_alive():
            continue
        val = u.hp
        if u.team == "PLAYER":
            score += val
        else:
            score -= val
    return score


def minimax(gs, depth, alpha, beta, maximizing):
    global NODE_COUNT
    NODE_COUNT += 1

    if depth == 0 or gs.is_terminal():
        return evaluate_state(gs), None

    team = "PLAYER" if maximizing else "ENEMY"
    actions = gs.generate_actions(team)
    if not actions:
        return evaluate_state(gs), None

    best_action = None

    if maximizing:
        value = -float("inf")
        for a in actions:
            child = gs.apply_action(a)
            eval_val, _ = minimax(child, depth-1, alpha, beta, False)
            if eval_val > value:
                value = eval_val
                best_action = a
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best_action
    else:
        value = float("inf")
        for a in actions:
            child = gs.apply_action(a)
            eval_val, _ = minimax(child, depth-1, alpha, beta, True)
            if eval_val < value:
                value = eval_val
                best_action = a
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_action


def evaluate_root_actions(gs, depth):
    from .ai_minimax import minimax, NODE_COUNT

    actions = gs.generate_actions("PLAYER")
    results = []

    for action in actions:
        child = gs.apply_action(action)
        NODE_COUNT = 0
        score, _ = minimax(child, depth-1, -99999, 99999, False)
        results.append((action, score))

    return results
