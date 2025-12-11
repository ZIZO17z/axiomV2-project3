import math

class Vector2D:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    @staticmethod
    def from_angle(angle_radians):
        return Vector2D(math.cos(angle_radians), math.sin(angle_radians))
    
    def __add__(self, other):
        return Vector2D(self.x + other.x, self.y + other.y)



    def __sub__(self, other):
        return Vector2D(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):
        return Vector2D(self.x * scalar, self.y * scalar)
    
    def __truediv__(self, scalar):
        if scalar == 0: return Vector2D(0, 0)
        return Vector2D(self.x / scalar, self.y / scalar)
    


    def __neg__(self):
        return Vector2D(-self.x, -self.y)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y
    
    def cross(self, other):
        return self.x * other.y - self.y * other.x
    
    def magnitude(self):
        return math.sqrt(self.x**2 + self.y**2)

    def normalize(self):
        m = self.magnitude()
        if m == 0: return Vector2D(0, 0)
        return Vector2D(self.x / m, self.y / m)


    def rotate(self, angle_radians):
        ca = math.cos(angle_radians)
        sa = math.sin(angle_radians)
        return Vector2D(self.x * ca - self.y * sa, self.x * sa + self.y * ca)
    
    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_tuple(self):
        return (self.x, self.y)
    
    def to_int_tuple(self):
        return (int(self.x), int(self.y))
    
    def copy(self):
        return Vector2D(self.x, self.y)
    
    def reflect(self, normal):
        d = self.dot(normal)
        return self - normal * (2 * d)
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}
    



def get_spectrum_color(wavelength):
    w = float(wavelength)
    if w < 380: w = 380
    if w > 780: w = 780

    if 380 <= w < 440:
        r, g, b = -(w - 440)/(440 - 380), 0.0, 1.0
    elif 440 <= w < 490:
        r, g, b = 0.0, (w - 440)/(490 - 440), 1.0
    elif 490 <= w < 510:
        r, g, b = 0.0, 1.0, -(w - 510)/(510 - 490)
    elif 510 <= w < 580:
        r, g, b = (w - 510)/(580 - 510), 1.0, 0.0
    elif 580 <= w < 645:
        r, g, b = 1.0, -(w - 645)/(645 - 580), 0.0
    elif 645 <= w <= 780:
        r, g, b = 1.0, 0.0, 0.0
    else:
        r, g, b = 0.0, 0.0, 0.0

    factor = 1.0
    if 380 <= w < 420:
        factor = 0.3 + 0.7 * (w - 380) / (420 - 380)
    elif 700 <= w <= 780:
        factor = 0.3 + 0.7 * (780 - w) / (780 - 700)

    gamma = 0.8
    R = int(max(0, (r * factor) ** gamma) * 255)
    G = int(max(0, (g * factor) ** gamma) * 255)
    B = int(max(0, (b * factor) ** gamma) * 255)
    return (R, G, B)