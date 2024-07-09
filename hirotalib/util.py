import random

def make_initial(size):
    # sは端に配置
    while True:
        sx = random.randrange(size)
        sy = random.randrange(size)
        if sx == 0 or sx == size-1 or sy == 0 or sy == size-1:
            break
    # 他の艦から2マス以内に入らないようにする
    while True:
        cx = random.randrange(size)
        cy = random.randrange(size)
        if abs(cx-sx) > 2 or abs(cy-sy) > 2:
            break
    while True:
        wx = random.randrange(size)
        wy = random.randrange(size)
        if (abs(wx-sx) > 2 or abs(wy-sy) > 2) and (abs(wx-cx) > 2 or abs(wy-cy) > 2):
            break
    return [[wx, wy], [cx, cy], [sx, sy]]

def near(pos1, pos2):
    return abs(pos1[0]-pos2[0]) <= 1 and abs(pos1[1]-pos2[1]) <= 1