import copy
from game.unit import Unit, ADVANTAGE

class GameState:
    def __init__(self, width=8, height=8):
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

    def get_legal_moves(self, unit):
        """Return list of (x, y) tiles the unit can move to."""
        moves = []
        for dx in range(-unit.move_range, unit.move_range + 1):
            for dy in range(-unit.move_range, unit.move_range + 1):
                nx, ny = unit.x + dx, unit.y + dy
                if self.in_bounds(nx, ny) and self.get_unit_at(nx, ny) is None:
                    if abs(dx) + abs(dy) <= unit.move_range:
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

    def get_units_for_team(self, team):
        return [u for u in self.units if u.team == team and u.is_alive()]

