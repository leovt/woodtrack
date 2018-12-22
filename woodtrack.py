from itertools import chain
from math import sin, cos, tan, pi

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
    return ('polygon', color, complex(x1, y1), complex(x2, y1), complex(x2, y2), complex(x1, y2))

MALE_BASE = [
    rectangle('black', MALE_OVERHANG, 0.5*MALE_SHAFT_WIDTH, -MALE_LENGTH+0.5*MALE_DIAM, -0.5*MALE_SHAFT_WIDTH),
    ('circle', 'black', complex(-MALE_LENGTH + 0.5*MALE_DIAM, 0.0), 0.5*MALE_DIAM)
]

FEMALE_BASE = [
    rectangle('white', -FEMALE_OVERHANG, 0.5*FEMALE_SHAFT_WIDTH, FEMALE_LENGTH-0.5*FEMALE_DIAM, -0.5*FEMALE_SHAFT_WIDTH),
    ('circle', 'white', complex(FEMALE_LENGTH - 0.5*FEMALE_DIAM, 0.0), 0.5*FEMALE_DIAM)
]


def item_to_svg(item):
    if item[0] == 'circle':
        _, color, center, r = item
        return f'<circle cx="{center.real}" cy="{center.imag}" r="{r}" fill="{color}"/>'
    elif item[0] == 'polygon':
        points = ' '.join(f'{pt.real},{pt.imag}' for pt in item[2:])
        return f'<polygon points="{points}" fill="{item[1]}"/>'

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
    return preamble + '\n'.join(item_to_svg(it) for it in items) + '\n</svg>\n'

class Transformation(tuple):
    def __new__(cls, content):
        self = tuple.__new__(cls, content)
        if len(self) != 6:
            raise ValueError('Transformation: Expected six components')
        return self

    def transform(self, item):
        if isinstance(item, tuple):
            if item[0] == 'polygon':
                return item[:2] + tuple(self.transform(pt) for pt in item[2:])
            elif item[0] == 'circle':
                return item[:2] + (self.transform(item[2]), item[3])
            else:
                assert False, f'unknown shape {item!r}'

        x,y = item.real, item.imag
        return complex(self[0]*x + self[1]*y + self[2], self[3]*x + self[4]*y + self[5])

    @classmethod
    def translate(cls, x, y):
        return cls((1.0, 0.0, x, 0.0, 1.0, y))

    def __add__(self, offset):
        return Transformation(self[:4]+(self[4]+offset.real, self[5]+offset.imag))


def place(start, direction, items):
    dd = abs(direction)
    dn = direction / dd
    dxn, dyn = dn.real, dn.imag
    trs = Transformation((dxn, -dyn, start.real, dyn, dxn, start.imag))
    return map(trs.transform, items)


def straight(start, end, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    return place(start, (end-start)/abs(end-start),
                 _straight(abs(end-start), start_decoration, end_decoration, draw_base, draw_groove))


def _straight(length, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    base = rectangle('black', 0.0, 0.5*TRACK_WIDTH, length, -0.5*TRACK_WIDTH)
    tre = Transformation((-1.0, 0.0, length, 0.0, 1.0, 0.0))

    if draw_base:
        yield base
        for item in start_decoration:
            yield item
        for item in end_decoration:
            yield tre.transform(item)

    if draw_groove:
        for sign in (1.0, -1.0):
            groove = rectangle('grey', -GROOVE_OVERHANG, sign*CENTER_WIDTH*0.5, length + GROOVE_OVERHANG, sign*(CENTER_WIDTH*0.5+GROOVE_WIDTH))
            yield groove

def arc(start, direction, radius, angle, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    return place(start, direction,
                 _arc(radius, angle, start_decoration, end_decoration, draw_base, draw_groove))

def _arc(radius, angle, start_decoration=FEMALE_BASE, end_decoration=MALE_BASE, draw_base=True, draw_groove=True):
    steps = int(radius*angle)
    dp = angle / steps

    dn = 1.0
    dxn, dyn = dn.real, dn.imag

    dxe = dxn * cos(angle+pi) - dyn * sin(angle+pi)
    dye = dxn * sin(angle+pi) + dyn * cos(angle+pi)

    end = complex(radius * sin(angle), radius * (1-cos(angle)))

    ro = radius + 0.5*TRACK_WIDTH
    ri = radius - 0.5*TRACK_WIDTH
    points = [complex(ro * sin(i*dp), radius - ro * cos(i*dp)) for i in range(steps+1)]
    points += [complex(ri * sin(i*dp), radius - ri * cos(i*dp)) for i in range(steps, -1, -1)]

    base = ('polygon', 'black',) + tuple(points)

    tre = Transformation((dxe, -dye, end.real, dye, dxe, end.imag))

    if draw_base:
        yield base
        for item in start_decoration:
            yield item
        for item in end_decoration:
            yield tre.transform(item)

    if draw_groove:
        amin = -GROOVE_OVERHANG / radius
        amax = angle + GROOVE_OVERHANG / radius
        steps = int(radius*(amax-amin))
        dp = (amax-amin) / steps
        for ro, ri in ((radius+0.5*CENTER_WIDTH+GROOVE_WIDTH, radius+0.5*CENTER_WIDTH),
                       (radius-0.5*CENTER_WIDTH, radius-0.5*CENTER_WIDTH-GROOVE_WIDTH)):
            points = [complex(ro * sin(amin+i*dp), radius - ro * cos(amin+i*dp)) for i in range(steps+1)]
            points += [complex(ri * sin(amin+i*dp), radius - ri * cos(amin+i*dp)) for i in range(steps, -1, -1)]

            groove = ('polygon', 'grey',) + tuple(points)
            yield groove

def double_switch(start, direction, radius, angle, draw_base=True, draw_groove=True):
    return place(start, direction,
                 _double_switch(radius, angle, draw_base, draw_groove))

def _double_switch(radius, angle, draw_base=True, draw_groove=True):
    L = radius * tan(0.5*angle)

    A = 0.0
    B = 2*L
    C = complex(L*(1-cos(angle)), -L*sin(angle))
    D = complex(L*(1+cos(angle)), L*sin(angle))

    dn = 1.0
    dxn, dyn = dn.real, dn.imag

    if draw_base:
        yield from arc(A, 1.0, radius, angle,
                       start_decoration=(), end_decoration=(),
                       draw_base=True, draw_groove=False)
        yield from arc(B, -1.0, radius, angle,
                       start_decoration=(), end_decoration=(),
                       draw_base=True, draw_groove=False)
        yield from straight(A, B, draw_base=True, draw_groove=False)
        yield from straight(C, D, draw_base=True, draw_groove=False)
    if draw_groove:
        yield from arc(A, 1.0, radius, angle,
                       start_decoration=(), end_decoration=(),
                       draw_base=False, draw_groove=True)
        yield from arc(B, -1.0, radius, angle,
                       start_decoration=(), end_decoration=(),
                       draw_base=False, draw_groove=True)
        yield from straight(A, B, draw_base=False, draw_groove=True)
        yield from straight(C, D, draw_base=False, draw_groove=True)


with open('woodtrack.svg', 'w') as f:
    f.write(items_to_svg(chain(
        straight(30.0+10.0j, 30.0+60.0j),
        straight(30.0+80.0j, 30.0+130.0j, end_decoration=FEMALE_BASE),
        straight(30.0+150.0j, 30.0+200.0j, start_decoration=MALE_BASE),
        arc(80.0+10.0j, complex(cos(67.5*pi/180), sin(67.5*pi/180)), 192.0, pi/4),
        double_switch(200+10.0j, 1.0j, 165, pi/4),
        )))
