import pygame
import math
import constants
from utils import Vector2D, get_spectrum_color

class Shape:
    def __init__(self, x, y, material):
        self.position = Vector2D(x, y)
        self.material = material
        self.rotation = 0.0
        self.selected = False
        self.scale = 1.0

    def move(self, delta):
        self.position = self.position + delta
    
    def rotate(self, angle):
        self.rotation += angle
    
    def get_intersection(self, origin, direction):
        return None, None
    
    def draw(self, surface):
        pass

    def contains(self, point):
        return False
    
class Polygon(Shape):
    def __init__(self, x, y, material, vertices):
        super().__init__(x, y, material)
        self.local_vertices = [Vector2D(v[0], v[1]) for v in vertices]

    def get_world_vertices(self):
        verts = []
        for v in self.local_vertices:
            rotated = v.rotate(self.rotation)
            scaled = rotated * self.scale
            verts.append(self.position + scaled)
        return verts
    
    def get_intersection(self, origin, direction):
        verts = self.get_world_vertices()
        closest_t = float('inf')
        closest_normal = None
        
        count = len(verts)
        for i in range(count):
            p1 = verts[i]
            p2 = verts[(i + 1) % count]
            
            edge = p2 - p1
            normal = Vector2D(edge.y, -edge.x).normalize()
            
            denom = normal.dot(direction)
            if abs(denom) < 1e-6: continue
            
            v = p1 - origin
            t = v.dot(normal) / denom
            
            if t < 0: continue
            
            hit_point = origin + direction * t
            
            edge_len_sq = edge.x**2 + edge.y**2
            vp = hit_point - p1
            proj = vp.dot(edge)
            
            if proj >= 0 and proj <= edge_len_sq:
                if t < closest_t:
                    closest_t = t
                    closest_normal = normal

        if closest_t == float('inf'): return None, None
        return closest_t, closest_normal

    def contains(self, point):
        verts = self.get_world_vertices()
        inside = False
        j = len(verts) - 1
        for i in range(len(verts)):
            if ((verts[i].y > point.y) != (verts[j].y > point.y)) and \
               (point.x < (verts[j].x - verts[i].x) * (point.y - verts[i].y) / (verts[j].y - verts[i].y) + verts[i].x):
                inside = not inside
            j = i
        return inside
    
    def draw(self, surface):
        verts = self.get_world_vertices()
        points = [v.to_int_tuple() for v in verts]
        
        if not points: return

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        w = max_x - min_x + 4
        h = max_y - min_y + 4
        
        if w > 0 and h > 0:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            offset_points = [(p[0] - min_x + 2, p[1] - min_y + 2) for p in points]
            pygame.draw.polygon(s, self.material.color, offset_points)
            surface.blit(s, (min_x - 2, min_y - 2))
            
        color = constants.ACCENT if self.selected else (100, 120, 140)
        pygame.draw.polygon(surface, color, points, 2)
        
        if self.selected:
            for p in points:
                pygame.draw.circle(surface, constants.SUCCESS, p, 3)

class CircleLens(Shape):
    def __init__(self, x, y, material, radius):
        super().__init__(x, y, material)
        self.radius = float(radius)

    def get_intersection(self, origin, direction):
        oc = origin - self.position
        a = direction.dot(direction)
        b = 2.0 * oc.dot(direction)
        c = oc.dot(oc) - self.radius * self.radius
        discriminant = b*b - 4*a*c
        
        if discriminant < 0: return None, None
        
        dist = math.sqrt(discriminant)
        t1 = (-b - dist) / (2*a)
        t2 = (-b + dist) / (2*a)
        
        t = None
        if t1 > 0.001: t = t1
        elif t2 > 0.001: t = t2
        else: return None, None
        
        hit_point = origin + direction * t
        normal = (hit_point - self.position).normalize()
        return t, normal

    def contains(self, point):
        return point.distance_to(self.position) < self.radius

    def draw(self, surface):
        r = int(self.radius)
        x = int(self.position.x)
        y = int(self.position.y)
        
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, self.material.color, (r, r), r)
        surface.blit(s, (x - r, y - r))
        
        color = constants.ACCENT if self.selected else (100, 120, 140)
        pygame.draw.circle(surface, color, (x, y), r, 2)

class LaserSource:
    def __init__(self, x, y):
        self.position = Vector2D(x, y)
        self.angle = 0.0
        self.active = True
        self.wavelength = 650
        self.beam_count = 1
        self.spread = 0.0

    def get_rays(self):
        if not self.active: return []
        
        rays = []
        main_dir = Vector2D.from_angle(self.angle)
        perp = Vector2D(-main_dir.y, main_dir.x)
        start = self.position + main_dir * 50
        
        if self.beam_count == 1:
            rays.append((start, main_dir, self.wavelength))
        else:
            for i in range(self.beam_count):
                offset_idx = i - (self.beam_count -1) / 2.0

                if self.spread > 0:
                    angle_offset = math.radians(offset_idx * self.spread)
                    d = main_dir.rotate(angle_offset)
                    rays.append((start, d, self.wavelength))
                else:
                    p = start + perp * (offset_idx * 3)
                    rays.append((p, main_dir, self.wavelength))

        return rays
    
    def draw(self, surface):
        pos = self.position.to_int_tuple()

        s= pygame.Surface((100, 50,), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 70, 80), (0, 10, 80, 30), border_radius=4)
        pygame.draw.rect(s, (40, 50, 60), (10, 15, 60, 20))

        color = get_spectrum_color(self.wavelength) if self.active else (50, 20, 20)
        pygame.draw.circle(s, color, (15, 25), 5)

        rotated = pygame.transform.rotate(s, -math.degrees(self.angle))
        rect = rotated.get_rect(center=pos)
        surface.blit(rotated, rect)


        handle = self.position - Vector2D.from_angle(self.angle) * 60
        pygame.draw.circle(surface, constants.LASER_HANDLE, handle.to_int_tuple(), 6)

    def contains(self, point):
        return self.position.distance_to(point) < 40