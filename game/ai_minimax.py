# minimax ai
import math
from copy import deepcopy

import pygame


NODE_COUNT = 0



def evaluate_state(gs):
    '''evaluate player hp+str*0.5 sum - enemy sum, winning state big bonus'''
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
        val = u.hp + 0.5 * u.strength
        if u.team == "PLAYER":
            score += val
        else:
            score -= val
    return score


def minimax(gs, depth, alpha, beta, maximizing):
    '''
    standard alpha beta prun minimax.
    returns (value, best_action) best_action can be None
    '''
    global NODE_COUNT
    NODE_COUNT += 1

    if depth == 0 or gs.is_terminal():
        return evaluate_state(gs), None

    team = "PLAYER" if maximizing else "ENEMY"
    actions = gs.generate_actions(team)

    # no actions -> leaf -> eval
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
    '''
    evalute root actions for debug/heatmap (kind of just for fun)
    '''

    actions = gs.generate_actions("PLAYER")
    results = []

    for action in actions:
        child = gs.apply_action(action)
        NODE_COUNT = 0
        score, _ = minimax(child, depth-1, -99999, 99999, False)
        results.append((action, score))

    return results

def choose_best_action(gs, depth):
    '''because am lazy'''
    _, best = minimax(gs, depth, -99999, 99999, True)
    return best

def player_phase(gs, renderer=None, clock=None, depth=2, animate=True):
    '''
    executes PLAYER phase using minimax 
    will perform a minimax move until there are no units left to move
    returns true if phase happened, false if not
    '''
    global NODE_COUNT 

    if gs.current_team != "PLAYER":
        return False
    
    # will loop until there are no available units
    while True: 
        actions = gs.generate_actions("PLAYER")
        if not actions:
            break

        # eval root actions for heatmap 
        NODE_COUNT = 0
        root_evals = evaluate_root_actions(gs, depth)
        if not root_evals: break 

        # pick best action 
        action, score = max(root_evals, key=lambda x: x[1])

        # renderer heatmap 
        if renderer and animate:
            renderer.draw()
            try: renderer.draw_minimax_heatmap(root_evals)
            except Exception: pass

            try: renderer.draw_minimax_debug(action, score, NODE_COUNT)
            except Exception: pass 

            if renderer.screen:
                pygame.display.flip()
            if clock: 
                clock.tick(60)

            # pause for humans
            if animate:
                pygame.time.delay(1500)
            

        # action taking   
    
        # movement animation / movement 
        if action.move_to:
            unit = gs.get_unit_by_id(action.unit_id)
            if unit is None: 
                # this is not supposed to happen 
                continue 
                
            old_pos = (unit.x, unit.y)
            new_pos = action.move_to 

            # check move legality - obviously skip but this should happen in generate actions as well so it ShOULD be redundant.
            legal = gs.get_legal_moves(unit)
            if (new_pos[0], new_pos[1]) not in legal and (new_pos[0], new_pos[1]) != (unit.x, unit.y):
                continue

            gs.apply_move(unit, new_pos[0], new_pos[1])

            if renderer and animate:
                renderer.animate_slide(unit, old_pos, new_pos)
                while renderer.update_animations():
                    renderer.draw()
                    if renderer.screen:
                        pygame.display.flip()
                    if clock:
                        clock.tick(60)

        # attack anim + application
        if action.attack_target_id is not None:
            attacker = gs.get_unit_by_id(action.unit_id)
            target = gs.get_unit_by_id(action.attack_target_id)
            if attacker is None or target is None:
                # invalid for some reason -> skip 
                continue 

            # renderer 
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
                    pygame.time.delay(250)

            gs.apply_attack(attacker, target)
        
    # end turn
    gs.end_turn()
    return True


# EXPERIMENTING WITH HIERARCHICAL + JOIN ACTION ???
# NO IM TIRED