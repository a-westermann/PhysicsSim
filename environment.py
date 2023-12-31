from Blocks.block import Block
import pygame as pg
from scipy import spatial

BLACK_HOLE = 1
SMALL_BLACK_HOLE = 2
LARGE_BLACK_HOLE = 3
REPULSOR = 4

def get_field(field_num: int, position: (int, int)):
    if field_num == BLACK_HOLE:
        return Black_Hole(position)
    elif field_num == LARGE_BLACK_HOLE:
        return Large_Black_Hole(position)
    
class Energy_Field:
    def __init__(self):
        self.energy = 0
        self.position = (0,0)
        self.event_horizon = 1  # total radius of effect, objects at (0,0) position destroyed
        self.quad_node = None
        self.color = (0, 0, 0)
        self.kill_zone = 15

    
class Black_Hole(Energy_Field):
    def __init__(self, position: (int, int)):
        super().__init__()
        self.energy = -6
        self.position = position
        self.event_horizon = 200


class Large_Black_Hole(Energy_Field):
    def __init__(self, position: (int, int)):
        super().__init__()
        self.energy = -50
        self.position = position
        self.event_horizon = 100



class Environment:
    def __init__(self, wind: int, energy_fields: [Energy_Field]):
        self.wind = wind
        self.energy_fields: [Energy_Field] = None
        if energy_fields:
            self.energy_fields = {e for e in energy_fields}

    def get_wind(self):
        return self.wind


    def render_energy_fields(self, screen: pg.Surface):
        if not self.energy_fields:
            return
        for e in self.energy_fields:
            pg.draw.circle(screen, (0,0,0), e.position, e.event_horizon)
