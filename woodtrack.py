from itertools import chain
from math import sin, cos, pi, hypot

TRACK_WIDTH = 40.0
GROOVE_WIDTH = 6.0
CENTER_WIDTH = 20.0
GROOVE_OVERHANG = 1.0

MALE_DIAM = 11.0
MALE_SHAFT_WIDTH = 5.5
MALE_LENGTH = 18.0
MALE_OVERHANG = 1.0

FEMALE_DIAM = 12.0
FEMALE_SHAFT_WIDTH = 6.5
FEMALE_LENGTH = 18.5
FEMALE_OVERHANG = 1.0

def rectangle(color, x1, y1, x2, y2):
    return ('polygon', color, (x1, y1), (x2, y1), (x2, y2), (x1, y2))

MALE_BASE = [
    rectangle('black', MALE_OVERHANG, 0.5*MALE_SHAFT_WIDTH, -MALE_LENGTH+0.5*MALE_DIAM, -0.5*MALE_SHAFT_WIDTH),
    ('circle', 'black', (-MALE_LENGTH + 0.5*MALE_DIAM, 0.0), 0.5*MALE_DIAM)
]

FEMALE_BASE = [
    rectangle('white', -FEMALE_OVERHANG, 0.5*FEMALE_SHAFT_WIDTH, FEMALE_LENGTH-0.5*FEMALE_DIAM, -0.5*FEMALE_SHAFT_WIDTH),
    ('circle', 'white', (FEMALE_LENGTH - 0.5*FEMALE_DIAM, 0.0), 0.5*FEMALE_DIAM)
]


def item_to_svg(item):
    if item[0] == 'circle':
        _, color, (cx,cy), r = item
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
    elif item[0] == 'polygon':
        points = ' '.join(f'{pt[0]},{pt[1]}' for pt in item[2:])
        return f'<polygon points="{points}" fill="{item[1]}"/>'

def items_to_svg(items, width=300.0, height=300.0):
    preamble = f'''<?xml version="1.0" standalone="yes"?>
<svg
    width="{width}mm"
    height="{height}mm"
    viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg">\n'''
    return preamble + '\n'.join(item_to_svg(it) for it in items) + '\n</svg>\n'

class Transformation(tuple):
    def __new__(cls, content):
        self = tuple.__new__(cls, content)
        if len(self) != 6:
            raise ValueError('Transformation: Expected six components')
        return self

    def transform(self, item):
        if item[0] == 'polygon':
            return item[:2] + tuple(self.transform(pt) for pt in item[2:])
        if item[0] == 'circle':
            return item[:2] + (self.transform(item[2]), item[3])

        x,y = item
        return self[0]*x + self[1]*y + self[2], self[3]*x + self[4]*y + self[5]

    @classmethod
    def translate(cls, x, y):
        return cls((1.0, 0.0, x, 0.0, 1.0, y))

    def __add__(self, offset):
        return Transformation(self[:4]+(self[4]+offset[0], self[5]+offset[1]))

def straight(start, end, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    dd = hypot(dx, dy)
    dxn = dx / dd
    dyn = dy / dd

    trs = Transformation((dxn, -dyn, start[0], dyn, dxn, start[1]))
    tre = Transformation((-dxn, dyn, end[0], -dyn, -dxn, end[1]))

    base = rectangle('black', 0.0, 0.5*TRACK_WIDTH, dd, -0.5*TRACK_WIDTH)

    yield trs.transform(base)
    for item in start_decoration:
        yield trs.transform(item)
    for item in end_decoration:
        yield tre.transform(item)

    for sign in (1.0, -1.0):
        groove = rectangle('grey', -GROOVE_OVERHANG, sign*CENTER_WIDTH*0.5, dd + GROOVE_OVERHANG, sign*(CENTER_WIDTH*0.5+GROOVE_WIDTH))
        yield trs.transform(groove)

def arc(start, direction, radius, angle, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE):

    angle = angle * pi / 180

    steps = int(radius*angle)

    dp = angle / steps

    dx, dy = direction
    dd = hypot(dx, dy)
    dxn = dx / dd
    dyn = dy / dd


    dxe = dxn * cos(angle) + dyn * sin(angle)
    dye = -dxn * sin(angle) + dyn * cos(angle)

    end = (radius * sin(angle), radius * (1-cos(angle)))

    ro = radius + 0.5*TRACK_WIDTH
    ri = radius - 0.5*TRACK_WIDTH
    points = [(ro * sin(i*dp), radius - ro * cos(i*dp)) for i in range(steps+1)]
    points += [(ri * sin(i*dp), radius - ri * cos(i*dp)) for i in range(steps, -1, -1)]

    base = ('polygon', 'black',) + tuple(points)

    trs = Transformation((dxn, -dyn, start[0], dyn, dxn, start[1]))
    end = trs.transform(end)
    tre = Transformation((dxe, dye, end[0], -dye, dxe, end[1]))

    yield trs.transform(base)
    for item in start_decoration:
        yield trs.transform(item)
    for item in end_decoration:
        yield tre.transform(item)

    amin = -GROOVE_OVERHANG / radius
    amax = angle + GROOVE_OVERHANG / radius
    steps = int(radius*(amax-amin))
    dp = (amax-amin) / steps
    for ro, ri in ((radius+0.5*CENTER_WIDTH+GROOVE_WIDTH, radius+0.5*CENTER_WIDTH),
                   (radius-0.5*CENTER_WIDTH, radius-0.5*CENTER_WIDTH-GROOVE_WIDTH)):
        points = [(ro * sin(amin+i*dp), radius - ro * cos(amin+i*dp)) for i in range(steps+1)]
        points += [(ri * sin(amin+i*dp), radius - ri * cos(amin+i*dp)) for i in range(steps, -1, -1)]

        groove = ('polygon', 'grey',) + tuple(points)
        yield trs.transform(groove)


with open('woodtrack.svg', 'w') as f:
    f.write(items_to_svg(chain(
        straight((30.0, 10.0), (30.0, 150.0)),
        arc((130.0, 10.0), (0.0, 1.0), 192.0, 45.0),
        )))
