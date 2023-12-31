from Blocks.block import Block
import Blocks.block_type as block_type
from environment import *
import json
from types import SimpleNamespace


class Level_Getter:
    def __init__(self):
        self.levels = []
        self.read_levels_json()


    def read_levels_json(self):
        json_file = open('levels.json')
        levels = json.load(json_file)
        for level in levels:
            self.levels.append(Level(id=level['id'], block_counts=level['block_counts'],
                                     block_types=level['block_types'], bounds=level['bounds'],
                                     world_size=level['world_size'], start_pos=level['start_pos'],
                                     ground_level=level['ground'], wind=level['wind'],
                                     energy_fields=level['energy_fields'],
                                     timed_spawns=level['timed_spawns']))
        # [print(l.bounds) for l in self.levels]


    def get_level(self, level: int):
        print(f'creating level {level}')
        level = [l for l in self.levels if l.id == level][0]
        return level


# noinspection PyTypeChecker
class Level:
    def __init__(self, id: int, block_counts: list[int], block_types: list[int],
                 bounds: list[(int,int,int,int)], world_size: (int, int) = (1280, 720), start_pos: (int, int) = (200,200),
                 ground_level: int = 1200, wind: int = 0, energy_fields: dict = None,
                 timed_spawns: dict = None, writing: bool = False):
        self.id = id
        self.world_size = world_size
        self.block_counts = block_counts
        self.bounds = bounds
        self.block_types = block_types  # Now built at terrain generation step.
        self.timed_spawns = []  # create the list even if none so no if check needed in game.update
        self.start_pos = (start_pos[0], start_pos[1])
        self.ground = ground_level
        self.wind = wind
        self.energy_fields = []

        if writing:  # Creating json. Don't convert to objects
            self.block_types = block_types
        # Timed Spawn example format:  [{"block_types":[SAND, SAND], "times":[10, 23], "bounds":[(0,1,2,3), (4,4,4,4)}]
            self.timed_spawns = timed_spawns  # particles that spawn over time. Time in seconds
            self.energy_fields = energy_fields

        else:  # Reading level. Create block types from the enums
            if timed_spawns:
                # get the length of 1 of the fields, which will equate to length for all fields
                for i in range(len(timed_spawns['block_types'])):
                    timed_spawn = Timed_Spawn(b_type=timed_spawns['block_types'][i],
                                  spawn_rate=timed_spawns['spawn_rate'][i], time=timed_spawns['times'][i],
                                  bounds=timed_spawns['bounds'][i])
                    self.timed_spawns.append(timed_spawn)

            if energy_fields:
                for i in range(len(energy_fields['energy_field'])):
                    energy_field = get_field(energy_fields['energy_field'][i], energy_fields['position'][i])
                    self.energy_fields.append(energy_field)




class Timed_Spawn:
    def __init__(self, b_type: int, spawn_rate: int, time: int, bounds: (int, int, int, int)):
        self.block_type = b_type
        self.spawn_rate = spawn_rate
        self.time = time
        self.bounds = bounds
