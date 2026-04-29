import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from game.unit import Unit, UnitClass
from game.actions import Action

MAX_HP = 16
MAX_STR = 7

def encode_state(gs):
    '''
    0 player unit prsent
    1 enemy unit present
    2 player hp normalized
    3 enemy hp normalized
    4 player strength normalized
    5 enemy strength normalized
    6 player class sword
    7 player class axe
    8 player class spear
    9 enemy class sword
    10  enemy class axe
    11  enemy class spear
    12  obstacles 
    13  current team (1 = player, 0 = enemy)    
    '''
    H, W = gs.height, gs.width
    C = 14
    state = torch.zeros((C, H, W), dtype=torch.float32)

    # Obstacles
    for (x, y) in gs.obstacles:
        state[12, y, x] = 1.0

    # Units
    for u in gs.units:
        if not u.is_alive():
            continue

        x, y = u.x, u.y

        if u.team == "PLAYER":
            state[0, y, x] = 1.0
            state[2, y, x] = u.hp / MAX_HP
            state[4, y, x] = u.strength / MAX_STR

            if u.class_type == UnitClass.SWORD:
                state[6, y, x] = 1.0
            elif u.class_type == UnitClass.AXE:
                state[7, y, x] = 1.0
            elif u.class_type == UnitClass.SPEAR:
                state[8, y, x] = 1.0

        else:  # ENEMY
            state[1, y, x] = 1.0
            state[3, y, x] = u.hp / MAX_HP
            state[5, y, x] = u.strength / MAX_STR

            if u.class_type == UnitClass.SWORD:
                state[9, y, x] = 1.0
            elif u.class_type == UnitClass.AXE:
                state[10, y, x] = 1.0
            elif u.class_type == UnitClass.SPEAR:
                state[11, y, x] = 1.0

    # team indicator
    if gs.current_team == "PLAYER":
        state[13, :, :] = 1.0
    else:
        state[13, :, :] = 0.0

    return state

def encode_expert_action(gs, action, max_units):
    player_units = [u for u in gs.units if u.team == "PLAYER" and u.is_alive()]
    enemy_units  = [u for u in gs.units if u.team == "ENEMY" and u.is_alive()]

    # 1. unit index
    unit_idx = next(i for i,u in enumerate(player_units) if u.id == action.unit_id)

    # 2. move index
    if action.move_to is None:
        raise ValueError("Minimax should always produce a move")
    mx, my = action.move_to
    move_idx = my * gs.width + mx

    # 3. attack index
    if action.attack_target_id is None:
        attack_idx = len(enemy_units)  # "no attack"
    else:
        attack_idx = next(i for i,u in enumerate(enemy_units)
                          if u.id == action.attack_target_id)

    return unit_idx, move_idx, attack_idx


def neural_policy(gs, model):
    state = encode_state(gs).unsqueeze(0)
    unit_logits, move_logits, attack_logits = model(state)

    # gather units
    player_units = [u for u in gs.units if u.team == "PLAYER" and u.is_alive()]
    enemy_units  = [u for u in gs.units if u.team == "ENEMY" and u.is_alive()]

    # 1) UNIT SELECTION
    unit_mask = build_unit_mask(player_units, model.max_units)
    unit_idx = masked_argmax(unit_logits[0], unit_mask)
    acting_unit = player_units[unit_idx]

    # 2) MOVE SELECTION
    legal_moves = gs.get_legal_moves(acting_unit)
    move_mask = build_move_mask_from_legal(legal_moves, gs.height, gs.width)
    move_idx = masked_argmax(move_logits[0], move_mask)
    move_x, move_y = move_idx % gs.width, move_idx // gs.width
    move_to = (move_x, move_y)

    # 3) ATTACK SELECTION
    legal_attacks = gs.get_attackable_units(acting_unit)
    attack_mask = build_attack_mask_from_legal(legal_attacks, enemy_units, model.max_units)
    attack_idx = masked_argmax(attack_logits[0], attack_mask)

    if attack_idx == len(enemy_units):
        attack_target = None
    else:
        attack_target = enemy_units[attack_idx]

    return Action(
        unit_id=acting_unit.id,
        move_to=move_to,
        attack_target_id=attack_target.id if attack_target else None
    )


def build_unit_mask(player_units, max_units):
    mask = torch.zeros(max_units, dtype=torch.float32)
    for i, u in enumerate(player_units):
        if u.is_alive():
            mask[i] = 1.0
    return mask

def build_move_mask_from_legal(legal_moves, height, width):
    mask = torch.zeros(height * width, dtype=torch.float32)
    for (x, y) in legal_moves:
        idx = y * width + x
        mask[idx] = 1.0
    return mask

def build_attack_mask_from_legal(legal_attacks, enemy_units, max_units):
    mask = torch.zeros(max_units + 1, dtype=torch.float32)

    # mark legal enemy targets
    for i, enemy in enumerate(enemy_units):
        if enemy in legal_attacks:
            mask[i] = 1.0

    # "no attack" is always legal
    mask[len(enemy_units)] = 1.0

    return mask

def masked_argmax(logits, mask):
    masked = logits.clone()
    masked[mask == 0] = -1e9
    return masked.argmax().item()

import torch
import torch.nn as nn

def train(model, loader, epochs=10, device="cuda"):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)

    unit_loss_fn = nn.CrossEntropyLoss()
    move_loss_fn = nn.CrossEntropyLoss()
    attack_loss_fn = nn.CrossEntropyLoss()

    for epoch in range(epochs):
        model.train()
        total_loss = 0
        total_unit_loss = 0
        total_move_loss = 0
        total_attack_loss = 0

        for batch in loader:
            states, unit_idx, move_idx, attack_idx = batch
            states = states.to(device)
            unit_idx = unit_idx.to(device)
            move_idx = move_idx.to(device)
            attack_idx = attack_idx.to(device)

            optimizer.zero_grad()

            unit_logits, move_logits, attack_logits = model(states)

            # compute losses
            loss_unit = unit_loss_fn(unit_logits, unit_idx)
            loss_move = move_loss_fn(move_logits, move_idx)
            loss_attack = attack_loss_fn(attack_logits, attack_idx)

            loss = loss_unit + loss_move + loss_attack

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            total_unit_loss += loss_unit.item()
            total_move_loss += loss_move.item()
            total_attack_loss += loss_attack.item()

        print(f"Epoch {epoch+1}/{epochs}")
        print(f"  Total Loss:   {total_loss:.4f}")
        print(f"  Unit Loss:    {total_unit_loss:.4f}")
        print(f"  Move Loss:    {total_move_loss:.4f}")
        print(f"  Attack Loss:  {total_attack_loss:.4f}")

        # save checkpoint
        torch.save(model.state_dict(), f"tactics_model_epoch{epoch+1}.pt")
        print("  Saved checkpoint")





class TacticsNet(nn.Module):
    def __init__(self, height, width, channels, max_units):
        super().__init__()
        self.height = height
        self.width = width
        self.max_units = max_units

        # backbone: CNN over (C, H, W)
        self.backbone = nn.Sequential(
            nn.Conv2d(channels, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
        )

        flat_size = 64 * height * width

        self.unit_head = nn.Linear(flat_size, max_units)          # logits over units
        self.move_head = nn.Linear(flat_size, height * width)     # logits over tiles
        self.attack_head = nn.Linear(flat_size, max_units + 1)    # enemy units + "no attack"

    def forward(self, x):
        # x: (B, C, H, W)
        feat = self.backbone(x)          # (B, 64, H, W)
        feat = feat.view(feat.size(0), -1)  # (B, 64*H*W)

        unit_logits = self.unit_head(feat)      # (B, max_units)
        move_logits = self.move_head(feat)      # (B, H*W)
        attack_logits = self.attack_head(feat)  # (B, max_units+1)

        return unit_logits, move_logits, attack_logits

class TacticsDataset(Dataset):
    def __init__(self, samples):
        self.samples = samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        return (
            s["state"], 
            torch.tensor(s["unit_idx"], dtype=torch.long),
            torch.tensor(s["move_idx"], dtype=torch.long),
            torch.tensor(s["attack_idx"], dtype=torch.long),
        )