from dataclasses import dataclass

@dataclass
class Polygon:
    points: list
    color: str

    def __add__(self, offset):
        return Polygon([p + offset for p in self.points], self.color)

    def __mul__(self, rotation):
        return Polygon([p * rotation for p in self.points], self.color)

    def to_svg(self):
        points = ' '.join(f'{pt.real},{pt.imag}' for pt in self.points)
        return f'<polygon points="{points}" fill="{self.color}"/>'


@dataclass
class Circle:
    center: complex
    radius: float
    color: str

    def __add__(self, offset):
        return Circle(self.center + offset, self.radius, self.color)

    def __mul__(self, rotation):
        return Circle(self.center * rotation, self.radius * abs(rotation), self.color)

    def to_svg(self):
        return f'<circle cx="{self.center.real}" cy="{self.center.imag}" r="{self.radius}" fill="{self.color}"/>'
