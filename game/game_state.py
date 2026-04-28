import copy
from game.unit import Unit, ADVANTAGE
from game.actions import Action

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
        """Return list of (x, y) tiles the unit can move to."""
        moves = []
        for dx in range(-unit.move_range, unit.move_range + 1):
            for dy in range(-unit.move_range, unit.move_range + 1):
                nx, ny = unit.x + dx, unit.y + dy
                if not self.in_bounds(nx, ny):
                    continue
                if abs(dx) + abs(dy) > unit.move_range:
                    continue
                if self.get_unit_at(nx, ny) is not None:
                    continue  
                if self.is_obstacle(nx, ny):
                    continue
                moves.append((nx, ny))
        return moves

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
        defender.hp -= damage

    def clone(self):
        return copy.deepcopy(self)

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
