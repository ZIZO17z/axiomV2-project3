import math 
import pygame
import constants
from utils import Vector2D, get_spectrum_color

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
        if depth > constants.MAX_RECURSION or intensity < constants.MIN_INTENSITY:
            return
        
        hit = self.find_closest_intersection(scene, origin, direction)

        if hit  is None:
            end_point = origin + direction * constants.RAY_STEP
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
                point  = origin + direction * t
                closest_hit = RayHit(t, point, normal, obj)


        walls = [
            (Vector2D(0,0), Vector2D(0,1)),
            (Vector2D(constants.SCREEN_WIDTH, 0), Vector2D(-1, 0)),
            (Vector2D(0, constants.SCREEN_HEIGHT), Vector2D(0, -1)),
            (Vector2D(0,0), Vector2D(1,0))
        ]

        if direction.y < 0:
             t = -origin.y / direction.y
             if t > self.epsilon and t < closest_t:
                 closest_t = t
                 closest_hit = RayHit(t, origin + direction * t, Vector2D(0, 1), "WALL")
      
        
        if direction.y > 0:
            t = (constants.SCREEN_HEIGHT - origin.y) / direction.y
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(0,-1), "WALL")
            
        if direction.x < 0:
            t = -origin.x / direction.x
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(1, 0), "WALL")
        
        if direction.x > 0:
            t = (constants.SCREEN_WIDTH - origin.x) / direction.x
            if t > self.epsilon and t < closest_t:
                closest_t = t
                closest_hit = RayHit(t, origin + direction * t, Vector2D(-1, 0), "WALL")
        
        return closest_hit