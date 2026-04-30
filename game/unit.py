from enum import Enum

class UnitClass(Enum):
    SWORD = 0
    AXE = 1
    SPEAR = 2

# Rock-paper-scissors advantage table
ADVANTAGE = {
    UnitClass.SWORD: UnitClass.AXE,
    UnitClass.AXE: UnitClass.SPEAR,
    UnitClass.SPEAR: UnitClass.SWORD,
}

class Unit:
    _next_id = 0 

    def __init__(self, team, class_type, hp=10, strength=5, move_range=3, attack_range=1, x=None, y=None, id=None, has_moved=False, has_attacked=False):
        if id:
            self.id = id
        else:
            self.id = Unit._next_id 
            Unit._next_id += 1

        self.team = team
        self.class_type = class_type
        self.hp = hp
        self.strength = strength
        self.move_range = move_range
        self.attack_range = attack_range
        self.x = x
        self.y = y
        self.has_moved = has_moved
        self.has_attacked = has_attacked

    def is_alive(self):
        return self.hp > 0
    
    def copy(self):
        return Unit(
            team=self.team,
            class_type=self.class_type,
            hp=self.hp,
            strength=self.strength,
            x=self.x,
            y=self.y,
            id=self.id,
            has_moved=self.has_moved,
            has_attacked=self.has_attacked
        )
