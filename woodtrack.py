from itertools import chain
from math import sin, cos, tan, pi
import cmath

from shapes import Polygon, Circle, ShapeCollection, return_collection

TRACK_WIDTH = 40.0
GROOVE_WIDTH = 6.0
CENTER_WIDTH = 20.0
GROOVE_OVERHANG = 1.0

MALE_DIAM = 11.5
MALE_SHAFT_WIDTH = 5.5
MALE_LENGTH = 17.7
MALE_OVERHANG = 1.0

FEMALE_DIAM = 12.0
FEMALE_SHAFT_WIDTH = 6.5
FEMALE_LENGTH = 18.5
FEMALE_OVERHANG = 1.0

def rectangle(color, x1, y1, x2, y2):
    return Polygon([complex(x1, y1), complex(x2, y1), complex(x2, y2), complex(x1, y2)], color)

MALE_BASE = ShapeCollection([
    rectangle('black', MALE_OVERHANG, 0.5*MALE_SHAFT_WIDTH, -MALE_LENGTH+0.5*MALE_DIAM, -0.5*MALE_SHAFT_WIDTH),
    Circle(complex(-MALE_LENGTH + 0.5*MALE_DIAM, 0.0), 0.5*MALE_DIAM, 'black')
])

FEMALE_BASE = ShapeCollection([
    rectangle('white', -FEMALE_OVERHANG, 0.5*FEMALE_SHAFT_WIDTH, FEMALE_LENGTH-0.5*FEMALE_DIAM, -0.5*FEMALE_SHAFT_WIDTH),
    Circle(complex(FEMALE_LENGTH - 0.5*FEMALE_DIAM, 0.0), 0.5*FEMALE_DIAM, 'white')
])

NO_DECORATION = ShapeCollection([])


def items_to_svg(items, width=300.0, height=300.0):
    preamble = f'''<?xml version="1.0" standalone="yes"?>
<svg
    width="{width}mm"
    height="{height}mm"
    viewBox="0 0 {width} {height}"
    xmlns="http://www.w3.org/2000/svg">
<defs>
<pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
   <rect x="0" y="0" width="10" height="10" fill="none" stroke="blue" stroke-width="0.2" />
 </pattern>
 </defs>
 <rect id="background" width="{width}" height="{height}" fill="url(#grid)" />
'''
    return preamble + '\n'.join(item.to_svg() for item in items) + '\n</svg>\n'

@return_collection
def place(items, x, y, angle_in_degrees):
    return items * cmath.rect(1.0, angle_in_degrees * pi / 180) + complex(x, y)


@return_collection
def straight(length, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    base = rectangle('black', 0.0, 0.5*TRACK_WIDTH, length, -0.5*TRACK_WIDTH)

    if draw_base:
        yield base
        yield from start_decoration
        for item in end_decoration:
            yield item * (-1) + length

    if draw_groove:
        for sign in (1.0, -1.0):
            groove = rectangle('grey', -GROOVE_OVERHANG, sign*CENTER_WIDTH*0.5, length + GROOVE_OVERHANG, sign*(CENTER_WIDTH*0.5+GROOVE_WIDTH))
            yield groove


@return_collection
def arc(radius, angle_in_degrees, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    angle = angle_in_degrees * pi / 180
    steps = int(radius*angle)
    dp = angle / steps

    end = radius * complex(sin(angle), 1-cos(angle))

    ro = radius + 0.5*TRACK_WIDTH
    ri = radius - 0.5*TRACK_WIDTH
    points = [complex(ro * sin(i*dp), radius - ro * cos(i*dp)) for i in range(steps+1)]
    points += [complex(ri * sin(i*dp), radius - ri * cos(i*dp)) for i in range(steps, -1, -1)]

    base = Polygon(points, 'black')

    if draw_base:
        yield base
        yield from start_decoration
        yield from end_decoration * cmath.rect(-1.0, angle) + end

    if draw_groove:
        amin = -GROOVE_OVERHANG / radius
        amax = angle + GROOVE_OVERHANG / radius
        steps = int(radius*(amax-amin))
        dp = (amax-amin) / steps
        for ro, ri in ((radius+0.5*CENTER_WIDTH+GROOVE_WIDTH, radius+0.5*CENTER_WIDTH),
                       (radius-0.5*CENTER_WIDTH, radius-0.5*CENTER_WIDTH-GROOVE_WIDTH)):
            points = [complex(ro * sin(amin+i*dp), radius - ro * cos(amin+i*dp)) for i in range(steps+1)]
            points += [complex(ri * sin(amin+i*dp), radius - ri * cos(amin+i*dp)) for i in range(steps, -1, -1)]

            groove = Polygon(points, 'grey')
            yield groove


@return_collection
def double_switch(radius, angle_in_degrees, draw_base=True, draw_groove=True):
    angle = angle_in_degrees * pi / 180
    L = radius * tan(0.5*angle)

    C = L * (1-cmath.rect(1.0, angle))

    if draw_base:
        yield from arc(radius, angle_in_degrees,
                       start_decoration=NO_DECORATION, end_decoration=NO_DECORATION,
                       draw_base=True, draw_groove=False)
        yield from arc(radius, angle_in_degrees,
                       start_decoration=NO_DECORATION, end_decoration=NO_DECORATION,
                       draw_base=True, draw_groove=False) * (-1) + (2*L)
        yield from straight(2*L, draw_base=True, draw_groove=False)
        yield from straight(2*L, draw_base=True, draw_groove=False) * cmath.rect(1.0, angle) + C
    if draw_groove:
        yield from arc(radius, angle_in_degrees,
                       start_decoration=NO_DECORATION, end_decoration=NO_DECORATION,
                       draw_base=False, draw_groove=True)
        yield from arc(radius, angle_in_degrees,
                       start_decoration=NO_DECORATION, end_decoration=NO_DECORATION,
                       draw_base=False, draw_groove=True) * (-1) + (2*L)
        yield from straight(2*L, draw_base=False, draw_groove=True)
        yield from straight(2*L, draw_base=False, draw_groove=True) * cmath.rect(1.0, angle) + C


with open('woodtrack.svg', 'w') as f:
    f.write(items_to_svg(chain(
        place(straight(50), 30, 10, 90),
        place(straight(50, end_decoration=FEMALE_BASE), 30, 80,  90),
        place(straight(50, start_decoration=MALE_BASE), 30, 150, 90),
        place(arc(192.0, 45), 80, 10, 67.5),
        place(double_switch(165, 45), 200, 10, 90),
        )))
