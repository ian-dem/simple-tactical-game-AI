import torch
from game.game_state import GameState, generate_initial_gamestate
from game.ai_minimax import evaluate_root_actions
from game.ai_simple import simple_enemy_turn
from game.ai_nn import encode_state, encode_expert_action

import sys
sys.setrecursionlimit(5000)


def generate_dataset(num_games=200, depth=2, max_units=8):
    '''
    sample structure
    {
    "state": Tensor(C, H, W),
    "unit_idx": int,
    "move_idx": int,
    "attack_idx": int,
    }
    '''
    samples = []

    for game_idx in range(num_games):
        gs = GameState()
        seed = game_idx  # deterministic but varied
        generate_initial_gamestate(gs, seed=seed)

        print(f"Starting game {game_idx+1} with seed {seed}")

        while not gs.is_terminal():

            if gs.current_team == "PLAYER":
                # 1. encode state
                state_tensor = encode_state(gs)

                # 2. get expert action from minimax
                root_evals = evaluate_root_actions(gs, depth)
                action, score = max(root_evals, key=lambda x: x[1])

                # 3. encode expert action
                unit_idx, move_idx, attack_idx = encode_expert_action(gs, action, max_units)

                # 4. store sample
                samples.append({
                    "state": state_tensor,
                    "unit_idx": unit_idx,
                    "move_idx": move_idx,
                    "attack_idx": attack_idx,
                })

                # 5. apply expert action
                unit = gs.get_unit_by_id(action.unit_id)
                if action.move_to:
                    gs.apply_move(unit, *action.move_to)
                if action.attack_target_id is not None:
                    target = gs.get_unit_by_id(action.attack_target_id)
                    gs.apply_attack(unit, target)

                gs.end_turn()

            else:
                # enemy turn
                enemy, move_to, target = simple_enemy_turn(gs)
                if enemy and move_to:
                    gs.apply_move(enemy, *move_to)
                if enemy and target:
                    gs.apply_attack(enemy, target)
                gs.end_turn()

        print(f"Finished game {game_idx+1}/{num_games}")

    # save dataset
    torch.save(samples, "tactics_dataset.pt")
    print("Dataset saved to tactics_dataset.pt")

    return samples
