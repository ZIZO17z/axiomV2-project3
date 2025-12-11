import pygame 
import math
import random

import constants
from utils import Vector2D
from materials import LIBRARY as MATERIALS_LIBRARY
from physics import PhysicsEngine
from objects import Polygon, CircleLens, LaserSource
from ui import UIButton, UISlider


class Scene:
    def __init__(self):
        self.objects = []
        self.env_material = MATERIALS_LIBRARY["AIR"]



class ParticlesSystem:
    def __init__(self):
        self.particles = []
        for i in range(100):
          self.particles.append({
              "pos": Vector2D(random.randint(0, constants.SCREEN_WIDTH), random.randint(0, constants.SCREEN_HEIGHT)),
              'vel': Vector2D(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)),
              'size': random.uniform(1,2)
          })


    def update(self):
        for p in self.particles:
            p['pos'] = p['pos'] + p['vel']
            if p['pos'].x < 0: p['pos'].x = constants.SCREEN_WIDTH
            if p['pos'].x > constants.SCREEN_WIDTH: p['pos'].x = 0
            if p['pos'].y < 0: p['pos'].y = constants.SCREEN_HEIGHT
            if p['pos'].y > constants.SCREEN_HEIGHT: p['pos'].y = 0



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




class LightLab:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
        pygame.display.set_caption("Professional Physics Engine v2.0")
        self.clock = pygame.time.Clock()

        self.scene = Scene()
        self.laser = LaserSource(100, constants.SCREEN_HEIGHT // 2)
        self.engine = PhysicsEngine()
        self.particles = ParticlesSystem()

        self.widgets = []
        self.build_ui()

        self.selected_object = None
        self.drag_offset = Vector2D(0,0)
        self.dragging_handle = False

        self.load_default_scene()
        self.rays = []

    def load_default_scene(self):
        prism_verts = [(-60, 50), (60, 50), (0, -50)]
        self.scene.objects.append(Polygon(500, 450, MATERIALS_LIBRARY["GLASS"], prism_verts))

        block_verts = [(-50, -80), (50, -80), (50, 80), (-50, 80)]
        self.scene.objects.append(Polygon(800, 450, MATERIALS_LIBRARY["WATER"], block_verts))

        self.scene.objects.append(CircleLens(650, 200, MATERIALS_LIBRARY["DIAMOND"], 60))

    def build_ui(self):
        p_x = constants.SCREEN_WIDTH - 280
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
        cx, cy = constants.SCREEN_WIDTH/2, constants.SCREEN_HEIGHT/2
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
        self.screen.fill(constants.BG_DARK)

        if self.scene.env_material.name == "Water":
            overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
            overlay.fill((20, 40, 60))
            overlay.set_alpha(100)
            self.screen.blit(overlay, (0,0))


        for x in range(0, constants.SCREEN_WIDTH, 50):
            pygame.draw.line(self.screen, (20, 25, 35), (x, 0), (x, constants.SCREEN_HEIGHT))
        for y in range(0, constants.SCREEN_HEIGHT, 50):
            pygame.draw.line(self.screen, (20, 25, 35), (0, y), (constants.SCREEN_WIDTH, y))

        self.particles.draw(self.screen, self.rays)

        for obj in self.scene.objects:
            obj.draw(self.screen)
        
        self.laser.draw(self.screen)


        ray_surface = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        for r in self.rays:
            start = r.p1.to_int_tuple()
            end = r.p2.to_int_tuple()


            alpha = int(r.intensity * 255)
            if alpha < 5: continue

            color = r.color + (alpha,)
            width  = max(1, int(r.intensity * 4))
            pygame.draw.line(ray_surface, color, start, end, width)
            if width > 2:
                pygame.draw.line(ray_surface, (255, 255, 255, alpha), start, end, 1)
        
        self.screen.blit(ray_surface, (0,0))


        pygame.draw.rect(self.screen, constants.BG_PANEL, (constants.SCREEN_WIDTH - 300, 0, 300, constants.SCREEN_HEIGHT))
        pygame.draw.line(self.screen, constants.BORDER, (constants.SCREEN_WIDTH - 300, 0), (constants.SCREEN_WIDTH - 300, constants.SCREEN_HEIGHT))

        for w in self.widgets:
            w.draw(self.screen)



        if self.selected_object:
            if hasattr(self.selected_object, 'material'):
                font = pygame.font.SysFont("Arial", 16)
                txt = font.render(f'selected: {self.selected_object.material.name}', True, constants.ACCENT)
                self.screen.blit(txt, (20, constants.SCREEN_HEIGHT - 40))

        pygame.display.flip()

    def run(self):
        while self.handle_input():
            self.update_physics()
            self.render()
            self.clock.tick(constants.FPS)
        pygame.quit()

if __name__ == "__main__":
    app = LightLab()
    app.run()