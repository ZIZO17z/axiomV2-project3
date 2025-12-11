import pygame
import constants

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
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True 
        return False

    def draw(self, surface):
        color = constants.ACCENT_HOVER if self.hover else constants.BORDER
        pygame.draw.rect(surface, color, self.rect, border_radius=5)

        text_surf = self.font.render(self.text, True, constants.TEXT_MAIN)
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
        super().update(event)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_value_from_mouse(event.pos[0])
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if self.dragging:
                self.dragging = False
                return True

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                if pygame.mouse.get_pressed()[0]:
                    self.update_value_from_mouse(event.pos[0])
                    return True
                else:
                    self.dragging = False 
        
        return False

    def update_value_from_mouse(self, mouse_x):
        rel = (mouse_x - self.rect.x) / self.rect.w
        rel = max(0.0, min(1.0, rel))
        self.value = self.min + rel * (self.max - self.min)
        self.callback(self.value)

    def draw(self, surface):
        label_surf = self.font.render(f"{self.label}: {self.value:.2f}", True, constants.TEXT_SUB)
        surface.blit(label_surf, (self.rect.x, self.rect.y))

        track_rect = pygame.Rect(self.rect.x, self.rect.y + 25, self.rect.w, 4)
        pygame.draw.rect(surface, (40, 40, 50), track_rect, border_radius=2)

        progress = (self.value - self.min) / (self.max - self.min)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y + 25, self.rect.w * progress, 4)
        pygame.draw.rect(surface, constants.ACCENT, fill_rect, border_radius=2)

        handle_x = self.rect.x + self.rect.w * progress
        pygame.draw.circle(surface, constants.TEXT_MAIN, (int(handle_x), int(track_rect.centery)), 8)
        