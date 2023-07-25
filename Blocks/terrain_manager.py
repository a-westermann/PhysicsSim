from Blocks.block import Block, Trail
import Blocks.block_type as block_type
from quadtree import Quadtree_Node, Quadtree
import pygame as pg
import math
import sys
import random
from collections import defaultdict
import multiprocessing.dummy as mp
# from multiprocessing import Pool
from threading import Thread
import asyncio
from numba import jit


display_res = []
frames_til_grounded = 1  # how many frames a block must be stationary before being grounded
slide_factor = 1  # how fast blocks slide horizontally - currently unused
# EMPTY = 0
# OCCUPIED = 1

class Matrix(defaultdict):  # defaultdict will create items if try to get a value from a key that does not exist
    def __init__(self, width: int, height: int):
        super().__init__(self.default)  # will return -1 for out of bounds (fall)
        # self.matrix = {}
        for x in range(width):  # initalize all spaces as empty
            for y in range(height):
                self[x,y] = -1

    def default(self):
        return -1



class Terrain_Manager:
    def __init__(self, screen_width: int, screen_height: int, game):
        self.blocks = set()
        # self.inactive_blocks = set()
        self.destroyable_blocks = set()
        self.unground_pos_checks = set()
        self.all_blocks = []  # do not remove from list so indices stay the same
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.game = game
        self.render_image = None
        self.first_trigger_radius = 10
        self.gravity = 1
        self.terminal_velocity = 20
        self.ground = 1200  # redefined by level
        self.matrix = Matrix(width=0, height=0)
        self.quadtree = Quadtree(0, 0)
        self.random_bits = []
        # self.pool = mp.Pool()


    def setup(self, render_image, world_size: (int, int), ground_level: int):
        self.render_image = render_image
        self.matrix = Matrix(width=world_size[0], height=world_size[1])
        self.quadtree = Quadtree(world_size[0], world_size[1])
        self.ground = ground_level
        self.blocks.clear()
        self.all_blocks.clear()
        # self.inactive_blocks.clear()
        self.destroyable_blocks.clear()
        # Fill ground w/ -2
        for x in range(world_size[0]):
            for y in range(self.ground, world_size[1]):
                self.matrix[x, y] = -2

    def fill_matrix(self):  # will need new method for adding blocks after init
        for i, b in enumerate(self.all_blocks):
            b.id = i
            self.matrix[b.position[0], b.position[1]] = b.id
        self.random_bits = [random.randrange(0, 2) for _ in range(len(self.blocks))]
        self.blocks = {block.id for block in self.blocks}
        print(f'length = {len(self.blocks)}')

    def add_blocks_to_matrix(self, particles: list[Block]):
        for p in particles:
            p.id = len(self.all_blocks)
            self.matrix[p.position[0], p.position[1]] = p.id
            if self.game.block_type_list[p.type].destroyable:
                self.destroyable_blocks.add(p)
            self.blocks.add(p.id)  # have to add ALL blocks to this first so they draw on frame 1
            self.all_blocks.append(p)
        self.random_bits.extend([random.randrange(0, 2) for _ in range(len(particles))])


    async def update(self) -> None:
        # self.pool.map(self.update_blocks, self.blocks)
        for block_id in list(self.blocks):  # use a copy of the set for safe multi threading
            await self.update_blocks(block_id=block_id)
        # self.end_frame_unground()

        # print(f'\t\t\t\t\t\t\t\t\tactive block count: {len(self.blocks)}')
        # print(f'\t\t\t\t\t\t\t\t\t\tinactive block count: {len(self.inactive_blocks)}')





# Particle physics
    def check_pos_collide(self, x: int, y: int) -> bool:
        return self.matrix[x,y] != -1


    def check_under_player(self, position: (int, int)) -> bool:
        if position[1] == self.ground:
            return True
        return self.matrix[(position[0], position[1] + 1)] != -1

    # def chain_fall_check(self, x: int, y: int) -> int:  # , y_vel: int
    #     for i in range(1, 11):
    #         block_id = self.matrix[x, y + i]
    #         if block_id == -1:
    #             continue


#TODO: Convert the all_blocks list to a custom python object (list)
# and on error return None to eliminate the extra step

    def check_slope(self, block_id: int, b_type: int, position: (int, int)) -> int:
        # returns int -1 for slide left, 1 slide right, 0 no slide
        direction = 1 if self.random_bits[block_id] == 1 else -1  # Improvement?
        slide_grade = self.game.block_type_list[b_type].slide_grade
        x, y = position[0] + direction * slide_grade[0], position[1] + slide_grade[1]
        if self.matrix[x,y] == -1:  # Do i need to check the spaces beteen block and the slide grade check spot?
            return direction
        else:  # check other direction
            x = position[0] - direction * slide_grade[0]
            if self.matrix[x, y] == -1:
                return -direction
            else:
                return 0

    def check_liquid_flow(self, block_id: int, position: (int, int)):
        # returns int -1 for flow left, 1 flow right, 0 no flow
        # Liquid: 0 y difference, ensure block below is liquid
        under_block_id = self.matrix[position[0], position[1] + 1]
        if under_block_id != -2 and self.all_blocks[under_block_id].type == block_type.WATER:
            # Now check if the direction is good
            direction = 1 if self.random_bits[block_id] == 1 else -1  # Improvement?
            if self.matrix[position[0] + direction, position[1]] == -1:
                return direction
            elif self.matrix[position[0] - direction, position[1]] == -1:
                return -direction
        return 0

    def check_walk_slope(self, player_pos: (int, int), direction: int):
        if self.matrix[(player_pos[0] + direction[0], player_pos[1])] != -1 \
                and self.matrix[(player_pos[0] + direction[0], player_pos[1] - 1)] == -1:  # EMPTY:
            return True
        return False



    # Particle functions
    # @jit(nopython=True)
    async def update_blocks(self, block_id: int):
        block = self.all_blocks[block_id]
        if block.collision_detection:
    #TODO: somehow a small # of blocks are remaining in the active list and not going into inactive list
    # try level 1.
            # update velocities
            if block.vert_velocity < self.terminal_velocity:
                block.vert_velocity += self.gravity
            if block.horiz_velocity != 0:
                horiz_step = 1 if block.horiz_velocity > 0 else -1
                block.horiz_velocity -= horiz_step

            # move through all spaces based on velocity
    #TODO: When blocks are moving very fast this causes them to go way too far w/ explosions
            total_x = block.horiz_velocity * self.game.physics_lag_frames
            total_y = block.vert_velocity * self.game.physics_lag_frames
            # slip_counter = self.game.block_type_list[block.type].slipperiness
            for _ in range(0, max(abs(block.vert_velocity), abs(block.horiz_velocity))):
                # Get the next position to check. If game is lagging, skip some checks. Otherwise use -1/1
                next_x, next_y = self.get_step_velocity(total_x, total_y)
                collided = self.move(block.id, next_x, next_y)
                if collided:
                    break
                # TODO: Is this correct with dynamic velocity? I think i'm supposed to be subtracting the step amount.
                if total_x != 0:
                    total_x -= 1 if total_x > 0 else -1  # decrement by 1 in correct direction
                if total_y != 0:
                    total_y -= 1 if total_y > 0 else -1

            # Spawn ghost trail
            # if not block.trail_created and abs(block.vert_velocity) > 0:
            #     block.trail_created = True
            #     self.create_trail(block_id)

        elif block.id in self.blocks:
            self.blocks.remove(block.id)
            # self.inactive_blocks.add(block)

        b_type = self.game.block_type_list[block.type]
        if b_type.destructive:
            self.destructive(block.position[0], block.position[1])
            # block.collision_detection = True  # need a better way

        self.game.render_dict.add((block.position, b_type.get_color()))


    def move(self, block_id: int, x_step: int, y_step: int) -> bool:  # returns collided, to end the movement loop
        block = self.all_blocks[block_id]
        new_x, new_y = block.position[0] + x_step, block.position[1] + y_step
        collision = self.check_pos_collide(new_x, new_y)

        if collision:  # collided. Check if it should slide/flow to either side + down 1
            block.horiz_velocity = 0  # Ideally both axes would not necessarily go to zero
            block.vert_velocity = 0
            slide = 0
            b_type = self.game.block_type_list[block.type]
            if b_type.liquid:
                slide = self.check_liquid_flow(block_id=block_id, position=block.position)
            else:
                slide = self.check_slope(block_id=block_id, b_type=block.type, position=block.position)
            if slide != 0:
                block.horiz_velocity += slide  # Doesn't matter right now, adding more than 1 would
                old_pos = block.position[0], block.position[1]
                self.matrix[old_pos] = -1  # EMPTY
                self.game.spaces_to_clear.add_pos(block.position)
                new_y = 0 if block.type == block_type.WATER else 1
                block.position = (block.position[0] + slide, block.position[1] + new_y)
                self.matrix[block.position[0], block.position[1]] = block.id
                self.trigger_ungrounding(old_pos)  # trigger ungrounding in previous position
            else:  # collided and is not sliding. Turn collision od
                block.collision_detection = False
                # self.inactive_blocks.add(block)   # gets added in update_block
                # self.blocks.remove(block)  # gets removed in update_block
            return True

        # Did not collide. Mark prev position empty & mark to fill with black
        old_pos = block.position[0], block.position[1]
        self.matrix[old_pos] = -1
        if self.game.spaces_to_clear.add_pos(block.position):
            block.collision_detection = False   # went out of bounds. Could just draw a square around map to avoid this

        block.position = (new_x, new_y)
        self.matrix[block.position[0], block.position[1]] = block.id  # OCCUPIED
        self.trigger_ungrounding(old_pos)  # trigger ungrounding in previous position
        return False


    def get_step_velocity(self, total_x: int, total_y: int) -> (int, int):
        # returns a position based on velocity, trimmed down to -1 to +1 in any direction
        x = total_x
        y = total_y
        if self.game.physics_lag_frames > 1:  # physics rendering lagging. Skip some checks
            if total_x > 1:
                x = min(self.game.physics_lag_frames * x, total_x)
            elif total_x < -1:
                x = max(self.game.physics_lag_frames * x, total_x)
            if total_y > 1:
                y = min(self.game.physics_lag_frames * y, total_y)
            elif total_y < -1:
                y = max(self.game.physics_lag_frames * y, total_y)
        else:
            if x < 0:
                x = -1
            elif x > 0:
                x = 1
            if y < 0:
                y = -1
            elif y > 0:
                y = 1
        return int(x), int(y)


    #
    # def slide(self, block: Block, slide: int) -> None:
    #                                                 # * self.game.physics_lag_frames
    #     block.horiz_velocity = slide * slide_factor  # don't add velocity. Don't need it and it causes issues
    #     self.matrix[block.position[0], block.position[1]] = -1  # EMPTY
    #     self.game.spaces_to_clear.add_pos(block.position)
    #     block.position = (block.position[0] + slide, block.position[1] + 1)
    #     self.matrix[block.position[0], block.position[1]] = block.id
    #     return
    #

    # def flow(self, block: Block, flow: (int, int))-> None:


    def create_trail(self, block_id: int):
        block = self.all_blocks[block_id]
        color = (min(self.game.block_type_list[block.type].color[0] + 65, 255),
                 min(self.game.block_type_list[block.type].color[0] + 65, 255),
                 min(self.game.block_type_list[block.type].color[0] + 65, 255))
        trail = Trail(parent_id=block_id, color=color)
        self.game.trails.add(trail)



    def destructive(self, x: int, y: int):
        for x in range(x-1, x+2):
            for y in range(y-1, y+2):
                neighbor_id = self.matrix[x, y]
                if neighbor_id >= 0:  # don't destroy ground
                    neighbor = self.all_blocks[neighbor_id]
                    if neighbor.type.destroyable:
                        self.destroy_block(neighbor)


    def destroy_block(self, block_id: int) -> None:
        block = self.all_blocks[block_id]
        self.matrix[block.position[0], block.position[1]] = -1  # EMPTY
        self.game.spaces_to_clear.add_pos(block.position)
        # Now check all spaces around this block for ungroundable blocks. Note this will be called for all
        # blocks in the destruction zone
        self.trigger_ungrounding(block.position)



#TODO: There may be more finetuning to reduce checks on same positions
# Can I move this to the main thread? Modifying the blocks in multiple places won't work, maybe there's a solution.
    def trigger_ungrounding(self, position: (int, int)) -> None:
        # Ungrounding should start from the lowest block so don't bother checking y > 0
        for x in range(-1, 2):
            for y in range(-2, 1):  # Updated from 2. Theoretically shouldn't need to check down
                check_pos = (position[0] + x, position[1] + y)
                # add the position to the set to check if there's an ungroundable block at end of sequence
                if check_pos != position:
                    block_id = self.matrix[check_pos]
                    if block_id < 0:  # -1 or -2 for ground
                        continue
                    block = self.all_blocks[block_id]
                    # Keep the ungrounding split up over multiple frames for performance.
                    # When this now active block moves it will activate its neighbors the following frame
                    if not self.game.block_type_list[block.type].rigid and not block.collision_detection:
                        block.collision_detection = True
                        self.blocks.add(block_id)
                    # self.unground_pos_checks.add(check_pos)


    # def end_frame_unground(self) -> None:
    #     if len(self.unground_pos_checks) == 0:
    #         return
    #     for pos in self.unground_pos_checks:
    #         block_id = self.matrix[(pos)]
    #         if block_id == -1:
    #             continue
    #         block = self.all_blocks[block_id]
    #         if not block.type.rigid and not block.collision_detection:
    #             block.collision_detection = True
    #             self.blocks.add(block)
    #     # self.unground_pos_checks.clear()



# Quadtree structure used for destroyable particles only, to find particles within destroy radius
    def initialize_quadtree(self) -> (set[Quadtree_Node], bool):
        if self.quadtree.initialized:
            return self.quadtree.all_quads, False
        else:
            insert_blocks = set()
            for b in self.blocks:
                if self.game.block_type_list[self.all_blocks[b].type].destroyable:
                    insert_blocks.add(self.all_blocks[b])
            # insert_blocks = {self.all_blocks[b] for b in self.blocks if self.all_blocks[b].type.destroyable}
            # only insert destroyable blocks
            print(f'quadtree particle insert count: {len(insert_blocks)}')
            # as blocks are always active upon load, then switch to inactive.
            return self.quadtree.create_tree(insert_blocks), True

    def insert_object_quadtree(self, obj, x: int, y: int) -> Quadtree_Node:  # use to put specific position in tree
        return self.quadtree.insert_object(obj=obj, x=x, y=y, start_node=self.quadtree.root_node)
        # now can access node.children to get neighboring objects
