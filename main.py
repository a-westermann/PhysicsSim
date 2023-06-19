import pygame as pg
from pygame import time
from player import Player
import Blocks
from Blocks.block import Block
from Blocks.block_type import *
from Blocks import terrain_gen, terrain_manager
import physics
from quadtree import Quadtree


pg.init()
display_resolution = [2560, 1440]
screen = pg.display.set_mode(display_resolution)
physics.display_res = display_resolution
game_running = True

player = Player()
terrain_manager = terrain_manager.Terrain_Manager()
blocks = terrain_gen.gen_terrain(block_list=(500, Sand()), bounds=(100, 2000, 0, 1000),
                                      terrain_manager=terrain_manager)
rocks = terrain_gen.gen_terrain(block_list=(500, Rock()), bounds=(100, 2000, 1100, 1200),
                                      terrain_manager=terrain_manager)
blocks.extend(rocks)

terrain_manager.blocks.extend(blocks)
block_rects = [block.rect for block in blocks]
terrain_manager.block_rects.extend(block_rects)

# Initial load time goes up with more cells, but FPS better
y_count = 14 # 50
x_count = 24 # 80
# The quadtrees are slowing it down. More quadtrees = slower
width = display_resolution[1] / y_count
height = display_resolution[0] / x_count
quadtrees = []
for y in range(y_count):
    for x in range(x_count):
        quadtrees.append(Quadtree(x * width, y * height, width, height))
for quadtree in quadtrees:
    quadtree.north = next(iter([q for q in quadtrees if q.y == quadtree.y + q.height and q.x == quadtree.x]), None)
    quadtree.south = next(iter([q for q in quadtrees if q.y == quadtree.y - q.height and q.x == quadtree.x]), None)
    quadtree.east = next(iter([q for q in quadtrees if q.x == quadtree.x + q.width and q.y == quadtree.y]), None)
    quadtree.west = next(iter([q for q in quadtrees if q.x == quadtree.x - q.width and q.y == quadtree.y]), None)
[terrain_manager.add_rect_to_quadtree(block, quadtrees) for block in blocks]
# [print(f'{rock.quadtree}') for rock in rocks]

clock = time.Clock()
timer = 0


print('\n\nGame Loaded')
while game_running:
    clock.tick(60)
    timer += 1
    print(f'fps: {str(round(clock.get_fps()))}')

# trying to print out how many rock blocks are contained in q.objects
    print(f'{str(len([q for q in quadtrees if q.objects]))}')  ffff


    events = pg.event.get()
    for event in events:
        if event.type == pg.QUIT:
            game_running = False

    # fill screen with black
    screen.fill((0, 0, 0))

    # visualization
    pg.draw.line(screen, (0, 0, 255), (0, physics.ground), (2400, physics.ground))  # Ground
    for q in quadtrees:
        pg.draw.line(screen, (255, 255, 255), (q.x, q.y), (q.x + q.width, q.y))
        pg.draw.line(screen, (255, 255, 255), (q.x, q.y), (q.x, q.y - q.height))

    # timed functions
    if timer > 60 and timer < 120:
        new_blocks = terrain_gen.gen_terrain(block_list=(10, Sand()), bounds=(100, 2200, 0, 200),
                                terrain_manager=terrain_manager)
        # terrain_manager.blocks.extend(blocks)
        blocks.extend(new_blocks)
        terrain_manager.blocks.extend(new_blocks)
        [terrain_manager.block_rects.extend(block.rect) for block in new_blocks]
        [terrain_manager.add_rect_to_quadtree(block, quadtrees) for block in new_blocks]



    # [q.objects.clear() for q in quadtrees if len(q.objects) > 0]

# TODO: Big slowdown occurs from this line:
   # [terrain_manager.add_rect_to_quadtree(block, quadtrees) for block in blocks]

    # Updated to this, fixes FPS. No longer have object list being cleared and recreated every frame
    # Only blocks that leave their quadtree look for new ones.
    [physics.update_block_quadtree(block) for block in blocks if block.collision_detection and block.quadtree]

    terrain_manager.update(screen)

    player.update(events, screen)

    pg.event.pump()
    pg.display.flip()  # updates the display. Could use display.update() and pass in PARTS of the screen to update

    # col_blocks = [block for block in blocks if block.collision_detection]
    # print(f'{str(len(blocks))} sand blocks  /  {str(len(col_blocks))} col blocks')
pg.quit()


