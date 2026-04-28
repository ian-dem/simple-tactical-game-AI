

class Action:
    def __init__(self, unit, move_to=None, attack_target_id=None):
        self.unit = unit
        self.unit_id = self.unit.id          
        self.move_to = move_to          # (x, y) or None
        self.attack_target_id = attack_target_id  # id or None
