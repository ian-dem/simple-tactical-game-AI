# should probably refactor this into smaller pieces at some point because it keeps getting bigger >>>
import copy
import random
from game.unit import Unit, ADVANTAGE, UnitClass
from game.actions import Action
from collections import deque

class GameState:
    def __init__(self, width=8, height=8):
        self.obstacles = set()   # set of (x, y) tiles that cannot be entered or passed through
        self.width = width
        self.height = height
        self.units = []  # list of units
        self.current_team = "PLAYER"  # or "ENEMY"

    def add_unit(self, unit, x, y):
        unit.x = x
        unit.y = y
        self.units.append(unit)

    def get_unit_at(self, x, y):
        for u in self.units:
            if u.x == x and u.y == y and u.is_alive():
                return u
        return None

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
    
    def add_obstacle(self, x, y):
        self.obstacles.add((x, y))

    def is_obstacle(self, x, y):
        return (x, y) in self.obstacles


    def get_legal_moves(self, unit):
        start = (unit.x, unit.y)
        max_range = unit.move_range

        visited = set([start])
        queue = deque([(start, 0)])
        legal = []

        while queue:
            (x, y), dist = queue.popleft()

            if dist > 0:
                legal.append((x, y))

            if dist == max_range:
                continue

            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy

                if not self.in_bounds(nx, ny):
                    continue

                if self.is_obstacle(nx, ny):
                    continue

                occupant = self.get_unit_at(nx, ny)
                if occupant is not None and occupant != unit:
                    continue

                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append(((nx, ny), dist + 1))

        return legal

    def get_attackable_units(self, unit):
        """Return list of enemy units in attack range."""
        targets = []
        for other in self.units:
            if other.team != unit.team and other.is_alive():
                dist = abs(unit.x - other.x) + abs(unit.y - other.y)
                if dist <= unit.attack_range:
                    targets.append(other)
        return targets

    def apply_move(self, unit, x, y):
        unit.x = x
        unit.y = y

    def apply_attack(self, attacker, defender):
        modifier = 1.0
        if ADVANTAGE[attacker.class_type] == defender.class_type:
            modifier = 1.5
        elif ADVANTAGE[defender.class_type] == attacker.class_type:
            modifier = 0.75

        damage = int(attacker.strength * modifier)
        counter_damage = int(0.8 * defender.strength / modifier)
        defender.hp = max(0, defender.hp - damage)
        attacker.hp = max(0, attacker.hp - counter_damage)
        

    def clone(self):
        new = GameState(width=self.width, height=self.height)

        # copy obstacles
        new.obstacles = set(self.obstacles)

        # copy units
        new.units = [u.copy_shallow() for u in self.units]

        # copy turn info
        new.current_team = self.current_team

        return new



    def is_terminal(self):
        player_alive = any(u.team == "PLAYER" and u.is_alive() for u in self.units)
        enemy_alive = any(u.team == "ENEMY" and u.is_alive() for u in self.units)
        return not (player_alive and enemy_alive)


    def end_turn(self):
      self.current_team = "ENEMY" if self.current_team == "PLAYER" else "PLAYER"
      self.reset_unit_turns()

    def get_units_for_team(self, team):
        return [u for u in self.units if u.team == team and u.is_alive()]
    
    def reset_unit_turns(self):
        for u in self.units:
            u.has_moved = False
            u.has_attacked = False




    def generate_actions(self, team):
        actions = []
        units = self.get_units_for_team(team)

        for u in units:
            if not u.is_alive():
                continue

            moves = self.get_legal_moves(u)
            # include "no move" option (stay in place)
            if not moves:
                moves = [(u.x, u.y)]

            for (mx, my) in moves:
                # simulate move in a cloned state to compute attacks
                tmp = self.clone()
                cu = tmp.get_unit_at(u.x, u.y)
                tmp.apply_move(cu, mx, my)
                targets = tmp.get_attackable_units(cu)

                if targets:
                    for t in targets:
                        actions.append(Action(unit=u,
                                            move_to=(mx, my),
                                            attack_target_id=t.id))
                else:
                    actions.append(Action(unit=u,
                                        move_to=(mx, my),
                                        attack_target_id=None))
        return actions

        
    def get_unit_by_id(self, uid):
        for u in self.units:
            if u.id == uid and u.is_alive():
                return u
        return None

    def apply_action(self, action):
        new_state = self.clone()

        cu = new_state.get_unit_by_id(action.unit_id)
        if cu is None:
            return new_state

        if action.move_to:
            new_state.apply_move(cu, action.move_to[0], action.move_to[1])

        if action.attack_target_id is not None:
            target = new_state.get_unit_by_id(action.attack_target_id)
            if target is not None:
                new_state.apply_attack(cu, target)

        new_state.end_turn()
        return new_state
    

    # game over functions 
    def is_terminal(self):
        player_alive = any(u.team == "PLAYER" and u.is_alive() for u in self.units)
        enemy_alive = any(u.team == "ENEMY" and u.is_alive() for u in self.units)
        return not player_alive or not enemy_alive

    def winner(self):
        player_alive = any(u.team == "PLAYER" and u.is_alive() for u in self.units)
        enemy_alive = any(u.team == "ENEMY" and u.is_alive() for u in self.units)

        if player_alive and not enemy_alive:
            return "PLAYER"
        if enemy_alive and not player_alive:
            return "ENEMY"
        return None


# game start function 
def generate_initial_gamestate(gs, width=8, height=8, 
                               num_player_units=3, num_enemy_units=3,
                               obstacle_density=0.15,
                               HP_RANGE = (8, 16), STR_RANGE = (3, 7),
                               seed=None 
                               ):
    if seed is not None:
        random.seed(seed)

    # function to check if map has no blocked regions
    def is_map_fully_connected(gs, width, height):
        # Find a starting walkable tile
        start = None
        for x in range(width):
            for y in range(height):
                if not gs.is_obstacle(x, y):
                    start = (x, y)
                    break
            if start:
                break

        if not start:
            return False  # map is all obstacles

        # BFS floodfill
        visited = set([start])
        queue = deque([start])

        while queue:
            x, y = queue.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if not gs.is_obstacle(nx, ny) and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        # Count walkable tiles
        total_walkable = sum(
            1 for x in range(width) for y in range(height)
            if not gs.is_obstacle(x, y)
        )

        return len(visited) == total_walkable



    # spawn regions
    player_cols = {0, 1}
    enemy_cols  = {width-1, width-2}


    # generate obstacles check if valid, reroll if not
    attempts = 0
    while attempts < 100: 
        attempts += 1
        gs.obstacles.clear()
        for x in range(width):
            for y in range(height):
                if x in player_cols or x in enemy_cols:
                    continue  # don't block spawn zones
                if random.random() < obstacle_density:
                    gs.add_obstacle(x, y)
            
        if is_map_fully_connected(gs, width, height):
            break
    
    if attempts == 100:
        raise RuntimeError("Failed to generate a connected map")
    
    # find empty tile
    def random_empty_tile(valid_cols):
        while True:
            x = random.choice(list(valid_cols))
            y = random.randrange(height)
            if gs.get_unit_at(x, y) is None and not gs.is_obstacle(x, y):
                return x, y

    # stat generator for units 
    def random_stats():
        hp = random.randint(*HP_RANGE)
        strength = random.randint(*STR_RANGE)
        return hp, strength

    # spawn player units
    player_units = []
    for _ in range(num_player_units):
        class_type = random.choice(list(UnitClass))
        hp, strength = random_stats()
        unit = Unit("PLAYER", class_type, hp=hp, strength=strength)
        x, y = random_empty_tile(player_cols)
        gs.add_unit(unit, x, y)
        player_units.append(unit)

    # spawn enemy units
    enemy_units = []
    for _ in range(num_enemy_units):
        class_type = random.choice(list(UnitClass))
        hp, strength = random_stats()
        unit = Unit("ENEMY", class_type, hp=hp, strength=strength)
        x, y = random_empty_tile(enemy_cols)
        gs.add_unit(unit, x, y)
        enemy_units.append(unit)


    # balancing lazyish way
    total_player_hp = sum(u.hp for u in player_units)
    total_player_str = sum(u.strength for u in player_units)

    total_enemy_hp = sum(u.hp for u in enemy_units)
    total_enemy_str = sum(u.strength for u in enemy_units)

    # Scale enemy stats proportionally
    hp_scale = total_player_hp / max(1, total_enemy_hp)
    str_scale = total_player_str / max(1, total_enemy_str)

    for u in enemy_units:
        u.hp = max(1, int(u.hp * hp_scale))
        u.strength = max(1, int(u.strength * str_scale))


    return gs

    