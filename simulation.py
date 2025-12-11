import pygame
import math
import random
import time

SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
FPS = 60
PIXELS_PER_METER = 2000.0

C_BG_DARK = (12, 18, 28)
C_BG_PANEL = (28, 34, 45)
C_BORDER = (50, 58, 70)
C_ACCENT = (0, 160, 255)
C_ACCENT_HOVER = (60, 190, 255)
C_TEXT_MAIN = (235, 235, 235)
C_TEXT_SUB = (130, 140, 150)
C_DANGER = (230, 70, 70)
C_SUCCESS = (50, 200, 100)

MAX_RECURSION = 12
MIN_INTENSITY = 0.005
RAY_STEP = 5000

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

    def angle_to(self, other):
        return math.atan2(other.y - self.y, other.x - self.x)

    def reflect(self, normal):
        d = self.dot(normal)
        return self - normal * (2 * d)

    def __str__(self):
        return f"({self.x:.2f}, {self.y:.2f})"

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

class MaterialData:
    def __init__(self, name, ior_base, dispersion, opacity, color):
        self.name = name
        self.ior_base = ior_base
        self.dispersion = dispersion
        self.opacity = opacity
        self.color = color

    def get_ior(self, wavelength):
        wl_um = wavelength / 1000.0
        return self.ior_base + (self.dispersion / (wl_um ** 2))

MATERIALS_LIBRARY = {
    "VACUUM": MaterialData("Vacuum", 1.0, 0.0, 0.0, (0,0,0,0)),
    "AIR": MaterialData("Air", 1.0003, 0.0, 0.001, (240, 240, 255, 5)),
    "WATER": MaterialData("Water", 1.333, 0.003, 0.05, (100, 200, 255, 40)),
    "GLASS": MaterialData("Glass (BK7)", 1.5168, 0.004, 0.1, (200, 255, 250, 60)),
    "FLINT": MaterialData("Flint Glass", 1.62, 0.01, 0.2, (220, 220, 255, 70)),
    "DIAMOND": MaterialData("Diamond", 2.417, 0.018, 0.0, (200, 255, 255, 90)),
    "ACRYLIC": MaterialData("Acrylic", 1.49, 0.002, 0.1, (240, 240, 240, 50)),
    "OIL": MaterialData("Oil", 1.47, 0.005, 0.3, (255, 255, 100, 80))
}

class RayHit:
    def __init__(self, t, point, normal, obj):
        self.t = t
        self.point = point
        self.normal = normal
        self.obj = obj

class RaySegment:
    def __init__(self, p1, p2, intensity, wavelength, color):
        self.p1 = p1
        self.p2 = p2
        self.intensity = intensity
        self.wavelength = wavelength
        self.color = color

class PhysicsEngine:
    def __init__(self):
        self.epsilon = 0.001

    def solve_scene(self, scene, ray_origins):
        all_segments = []
        for origin, direction, wavelength in ray_origins:
            self.cast_ray(scene, origin, direction, wavelength, 1.0, scene.env_material, 0, all_segments)
        return all_segments

    def cast_ray(self, scene, origin, direction, wavelength, intensity, current_medium, depth, output_list):
        if depth > MAX_RECURSION or intensity < MIN_INTENSITY:
            return

        hit = self.find_closest_intersection(scene, origin, direction)

        if hit is None:
            end_point = origin + direction * RAY_STEP
            output_list.append(RaySegment(origin, end_point, intensity, wavelength, get_spectrum_color(wavelength)))
            return

        dist = hit.point.distance_to(origin)
        transmission_loss = math.exp(-current_medium.opacity * (dist / 100.0))
        final_intensity = intensity * transmission_loss

        output_list.append(RaySegment(origin, hit.point, final_intensity, wavelength, get_spectrum_color(wavelength)))

        if hit.obj == "WALL":
            return

        is_entering = direction.dot(hit.normal) < 0
        
        n1 = current_medium.get_ior(wavelength)
        n2 = hit.obj.material.get_ior(wavelength)

        normal = hit.normal
        
        if not is_entering:
            n1 = hit.obj.material.get_ior(wavelength)
            n2 = scene.env_material.get_ior(wavelength)
            normal = -hit.normal

        ratio = n1 / n2
        cos_i = -normal.dot(direction)
        sin_t2 = ratio * ratio * (1.0 - cos_i * cos_i)

        reflectivity = 1.0
        is_tir = True

        if sin_t2 <= 1.0:
            is_tir = False
            cos_t = math.sqrt(1.0 - sin_t2)
            
            r_orth = (n1 * cos_i - n2 * cos_t) / (n1 * cos_i + n2 * cos_t)
            r_par = (n2 * cos_i - n1 * cos_t) / (n2 * cos_i + n1 * cos_t)
            reflectivity = (r_orth * r_orth + r_par * r_par) / 2.0

        reflect_dir = direction.reflect(normal).normalize()
        reflect_start = hit.point + reflect_dir * self.epsilon
        
        if reflectivity > 0.05:
            self.cast_ray(scene, reflect_start, reflect_dir, wavelength, final_intensity * reflectivity, current_medium, depth + 1, output_list)

        if not is_tir:
            transmission_ratio = 1.0 - reflectivity
            if transmission_ratio > 0.05:
                k = 1.0 - ratio * ratio * (1.0 - cos_i * cos_i)
                refract_dir = (direction * ratio + normal * (ratio * cos_i - math.sqrt(k))).normalize()
                refract_start = hit.point + refract_dir * self.epsilon
                
                new_medium = hit.obj.material if is_entering else scene.env_material
                self.cast_ray(scene, refract_start, refract_dir, wavelength, final_intensity * transmission_ratio, new_medium, depth + 1, output_list)

    def find_closest_intersection(self, scene, origin, direction):
        closest_t = float('inf')
        closest_hit = None

        
        for obj in scene.objects:
            t, normal = obj.get_intersection(origin, direction)
            if t is not None and t > self.epsilon and t < closest_t:
                closest_t = t
                point = origin + direction * t
                closest_hit = RayHit(t, point, normal, obj)

        
        walls = [
            (Vector2D(0, 0), Vector2D(0, 1)),
            (Vector2D(SCREEN_WIDTH, 0), Vector2D(-1, 0)),
            (Vector2D(0, SCREEN_HEIGHT), Vector2D(0, -1)),
            (Vector2D(0, 0), Vector2D(1, 0))
        ]
        
        
        if direction.y < 0:
            t = -origin.y / direction.y
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(0, 1), "WALL")
        
        if direction.y > 0:
            t = (SCREEN_HEIGHT - origin.y) / direction.y
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(0, -1), "WALL")
        
        if direction.x < 0:
            t = -origin.x / direction.x
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(1, 0), "WALL")
        
        if direction.x > 0:
            t = (SCREEN_WIDTH - origin.x) / direction.x
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(-1, 0), "WALL")

        return closest_hit

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
            
        color = C_ACCENT if self.selected else (100, 120, 140)
        pygame.draw.polygon(surface, color, points, 2)
        
        if self.selected:
            for p in points:
                pygame.draw.circle(surface, C_SUCCESS, p, 3)

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
        
        color = C_ACCENT if self.selected else (100, 120, 140)
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
                offset_idx = i - (self.beam_count - 1) / 2.0
                
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
        
        s = pygame.Surface((100, 50), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 70, 80), (0, 10, 80, 30), border_radius=4)
        pygame.draw.rect(s, (40, 50, 60), (10, 15, 60, 20))
        
        color = get_spectrum_color(self.wavelength) if self.active else (50, 20, 20)
        pygame.draw.circle(s, color, (15, 25), 5)
        
        rotated = pygame.transform.rotate(s, -math.degrees(self.angle))
        rect = rotated.get_rect(center=pos)
        surface.blit(rotated, rect)
        
        handle = self.position - Vector2D.from_angle(self.angle) * 60
        pygame.draw.circle(surface, (150, 150, 150), handle.to_int_tuple(), 6)

    def contains(self, point):
        return self.position.distance_to(point) < 40

class ParticleSystem:
    def __init__(self):
        self.particles = []
        for i in range(100):
            self.particles.append({
                'pos': Vector2D(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)),
                'vel': Vector2D(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)),
                'size': random.uniform(1, 2)
            })

    def update(self):
        for p in self.particles:
            p['pos'] = p['pos'] + p['vel']
            if p['pos'].x < 0: p['pos'].x = SCREEN_WIDTH
            if p['pos'].x > SCREEN_WIDTH: p['pos'].x = 0
            if p['pos'].y < 0: p['pos'].y = SCREEN_HEIGHT
            if p['pos'].y > SCREEN_HEIGHT: p['pos'].y = 0

    def draw(self, surface, rays):
        for p in self.particles:
            brightness = 20
            
            for r in rays:
                
                l2 = r.p1.distance_to(r.p2)**2
                if l2 == 0: continue
                t = ((p['pos'].x - r.p1.x) * (r.p2.x - r.p1.x) + (p['pos'].y - r.p1.y) * (r.p2.y - r.p1.y)) / l2
                t = max(0, min(1, t))
                proj = r.p1 + (r.p2 - r.p1) * t
                dist = p['pos'].distance_to(proj)
                
                if dist < 10:
                    brightness = min(255, brightness + 200 * (1.0 - dist/10.0) * r.intensity)

            col = (brightness, brightness, brightness)
            if brightness > 30:
                pygame.draw.circle(surface, col, p['pos'].to_int_tuple(), 1)



class Widget:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.hover = False
    
    def update(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        return False

class UIButton(Widget):
    def __init__(self, x, y, w, h, text, callback):
        super().__init__(x, y, w, h)
        self.text = text
        self.callback = callback
        self.font = pygame.font.SysFont("Segoe UI", 14, bold=True)

    def update(self, event):
        super().update(event)
        if event.type == pygame.MOUSEBUTTONDOWN and self.hover:
            self.callback()
            return True
        return False

    def draw(self, surface):
        color = C_ACCENT_HOVER if self.hover else C_BORDER
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        
        text_surf = self.font.render(self.text, True, C_TEXT_MAIN)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class UISlider(Widget):
    def __init__(self, x, y, w, min_val, max_val, start_val, label, callback):
        super().__init__(x, y, w, 40)
        self.min = min_val
        self.max = max_val
        self.value = start_val
        self.label = label
        self.callback = callback
        self.dragging = False
        self.font = pygame.font.SysFont("Segoe UI", 12)

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        
        if self.dragging and pygame.mouse.get_pressed()[0]:
            mx = pygame.mouse.get_pos()[0]
            rel = (mx - self.rect.x) / self.rect.w
            rel = max(0.0, min(1.0, rel))
            self.value = self.min + rel * (self.max - self.min)
            self.callback(self.value)
            return True
        return False

    def draw(self, surface):
        label_surf = self.font.render(f"{self.label}: {self.value:.2f}", True, C_TEXT_SUB)
        surface.blit(label_surf, (self.rect.x, self.rect.y))
        
        track_rect = pygame.Rect(self.rect.x, self.rect.y + 20, self.rect.w, 4)
        pygame.draw.rect(surface, (40, 40, 50), track_rect, border_radius=2)
        
        progress = (self.value - self.min) / (self.max - self.min)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y + 20, self.rect.w * progress, 4)
        pygame.draw.rect(surface, C_ACCENT, fill_rect, border_radius=2)
        
        handle_x = self.rect.x + self.rect.w * progress
        pygame.draw.circle(surface, C_TEXT_MAIN, (int(handle_x), int(track_rect.centery)), 8)


class Scene:
    def __init__(self):
        self.objects = []
        self.env_material = MATERIALS_LIBRARY["AIR"]

class LightLab:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Professional Physics Engine")
        self.clock = pygame.time.Clock()
        
        self.scene = Scene()
        self.laser = LaserSource(100, SCREEN_HEIGHT // 2)
        self.engine = PhysicsEngine()
        self.particles = ParticleSystem()
        
        self.widgets = []
        self.build_ui()
        
        self.selected_object = None
        self.drag_offset = Vector2D(0, 0)
        self.dragging_handle = False
        
        self.load_default_scene()

    def load_default_scene(self):
        prism_verts = [(-60, 50), (60, 50), (0, -50)]
        self.scene.objects.append(Polygon(500, 450, MATERIALS_LIBRARY["GLASS"], prism_verts))
        
        block_verts = [(-50, -80), (50, -80), (50, 80), (-50, 80)]
        self.scene.objects.append(Polygon(800, 450, MATERIALS_LIBRARY["WATER"], block_verts))
        
        self.scene.objects.append(CircleLens(650, 200, MATERIALS_LIBRARY["DIAMOND"], 60))

    def build_ui(self):
        p_x = SCREEN_WIDTH - 280
        y = 20
        
        self.widgets.append(UISlider(p_x, y, 250, 380, 750, 650, "Wavelength (nm)", self.set_wavelength))
        y += 60
        self.widgets.append(UIButton(p_x, y, 120, 35, "White Light", self.set_white_mode))
        self.widgets.append(UIButton(p_x + 130, y, 120, 35, "Single Ray", self.set_single_mode))
        y += 50
        self.widgets.append(UISlider(p_x, y, 250, 1, 10, 1, "Beam Count", self.set_beam_count))
        y += 60
        self.widgets.append(UISlider(p_x, y, 250, 0, 20, 0, "Spread (Deg)", self.set_spread))
        
        y += 60
        self.widgets.append(UIButton(p_x, y, 250, 35, "Clear Scene", self.clear_scene))
        y += 45
        self.widgets.append(UIButton(p_x, y, 80, 35, "+ Prism", lambda: self.add_obj('prism')))
        self.widgets.append(UIButton(p_x+85, y, 80, 35, "+ Block", lambda: self.add_obj('block')))
        self.widgets.append(UIButton(p_x+170, y, 80, 35, "+ Lens", lambda: self.add_obj('lens')))
        
        y += 60
        self.widgets.append(UIButton(p_x, y, 250, 35, "Toggle Env (Air/Water)", self.toggle_env))
        
        y += 60
        mat_names = list(MATERIALS_LIBRARY.keys())
        for i, name in enumerate(mat_names):
            if name == "VACUUM": continue
            bx = p_x if i % 2 == 0 else p_x + 130
            by = y + (i // 2) * 40
            self.widgets.append(UIButton(bx, by, 120, 30, name, lambda n=name: self.set_material(n)))



    def set_wavelength(self, val): self.laser.wavelength = val
    def set_white_mode(self): 
        self.laser.beam_count = 5
        self.laser.spread = 1.0
        self.laser.wavelength = -1 
    def set_single_mode(self): self.laser.beam_count = 1
    def set_beam_count(self, val): self.laser.beam_count = int(val)
    def set_spread(self, val): self.laser.spread = val
    def clear_scene(self): self.scene.objects = []
    def toggle_env(self):
        if self.scene.env_material.name == "Air":
            self.scene.env_material = MATERIALS_LIBRARY["WATER"]
        else:
            self.scene.env_material = MATERIALS_LIBRARY["AIR"]
    def set_material(self, name):
        if self.selected_object:
            self.selected_object.material = MATERIALS_LIBRARY[name]


    def add_obj(self, type):
        cx, cy = SCREEN_WIDTH/2, SCREEN_HEIGHT/2
        if type == 'prism':
            self.scene.objects.append(Polygon(cx, cy, MATERIALS_LIBRARY["GLASS"], [(-60,50),(60,50),(0,-50)]))
        elif type == 'block':
            self.scene.objects.append(Polygon(cx, cy, MATERIALS_LIBRARY["GLASS"], [(-50,-50),(50,-50),(50,50),(-50,50)]))
        elif type == 'lens':
            self.scene.objects.append(CircleLens(cx, cy, MATERIALS_LIBRARY["GLASS"], 50))



    def handle_input(self):
        events = pygame.event.get()
        mouse_pos = Vector2D(*pygame.mouse.get_pos())
        
        for e in events:
            if e.type == pygame.QUIT: return False
            
            ui_captured = False
            for w in self.widgets:
                if w.update(e): ui_captured = True
            
            if ui_captured: continue
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.laser.contains(mouse_pos):
                        self.selected_object = self.laser
                        self.drag_offset = self.laser.position - mouse_pos
                    else:
                        handle_pos = self.laser.position - Vector2D.from_angle(self.laser.angle) * 60
                        if handle_pos.distance_to(mouse_pos) < 15:
                            self.dragging_handle = True
                        else:
                            hit = False
                            for obj in reversed(self.scene.objects):
                                if obj.contains(mouse_pos):
                                    self.selected_object = obj
                                    self.drag_offset = obj.position - mouse_pos
                                    obj.selected = True
                                    hit = True
                                    for o in self.scene.objects: 
                                        if o != obj: o.selected = False
                                    break
                            if not hit:
                                self.selected_object = None
                                for o in self.scene.objects: o.selected = False

                elif e.button == 3: 
                    for obj in self.scene.objects:
                        if obj.contains(mouse_pos):
                            obj.rotation += math.radians(45)

            elif e.type == pygame.MOUSEBUTTONUP:
                self.selected_object = None
                self.dragging_handle = False

        if self.selected_object:
            self.selected_object.position = mouse_pos + self.drag_offset

        if self.dragging_handle:
            diff = mouse_pos - self.laser.position
            self.laser.angle = math.atan2(diff.y, diff.x) + math.pi

        return True



    def update_physics(self):
        self.particles.update()
        
        rays_to_cast = []
        if self.laser.wavelength == -1: 
            for i in range(10):
                wl = 400 + (i / 9.0) * 300
                main_dir = Vector2D.from_angle(self.laser.angle)
                start = self.laser.position + main_dir * 50
                perp = Vector2D(-main_dir.y, main_dir.x)
                p = start + perp * ((i - 4.5) * 1.5)
                rays_to_cast.append((p, main_dir, wl))
        else:
            rays_to_cast = self.laser.get_rays()
            
        self.rays = self.engine.solve_scene(self.scene, rays_to_cast)

    def render(self):
        self.screen.fill(C_BG_DARK)
        
        if self.scene.env_material.name == "Water":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.fill((20, 40, 60))
            overlay.set_alpha(100)
            self.screen.blit(overlay, (0,0))

        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, (20, 25, 35), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, (20, 25, 35), (0, y), (SCREEN_WIDTH, y))

        self.particles.draw(self.screen, self.rays)

        for obj in self.scene.objects:
            obj.draw(self.screen)

        self.laser.draw(self.screen)

        ray_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for r in self.rays:
            start = r.p1.to_int_tuple()
            end = r.p2.to_int_tuple()
            
            alpha = int(r.intensity * 255)
            if alpha < 5: continue
            
            color = r.color + (alpha,)
            width = max(1, int(r.intensity * 4))
            
            pygame.draw.line(ray_surface, color, start, end, width)
            if width > 2:
                pygame.draw.line(ray_surface, (255, 255, 255, alpha), start, end, 1)
        
        self.screen.blit(ray_surface, (0,0))



        pygame.draw.rect(self.screen, C_BG_PANEL, (SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, C_BORDER, (SCREEN_WIDTH - 300, 0), (SCREEN_WIDTH - 300, SCREEN_HEIGHT))
        
        for w in self.widgets:
            w.draw(self.screen)

        if self.selected_object:
            if hasattr(self.selected_object, 'material'):
                font = pygame.font.SysFont("Arial", 16)
                txt = font.render(f"Selected: {self.selected_object.material.name}", True, C_ACCENT)
                self.screen.blit(txt, (20, SCREEN_HEIGHT - 40))

        pygame.display.flip()

    def run(self):
        while self.handle_input():
            self.update_physics()
            self.render()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    app = LightLab()
    app.run()