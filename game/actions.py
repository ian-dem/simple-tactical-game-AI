

class Action:
    def __init__(self, unit_id, move_to=None, attack_target_id=None):
        self.unit_id = unit_id        
        self.move_to = move_to          # (x, y) or None
        self.attack_target_id = attack_target_id  # id or None
