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
    


LIBRARY = {
    "VACUUM": MaterialData("Vacuum", 1.0, 0.0, 0.0, (0,0,0,0)),
    "AIR": MaterialData("Air", 1.0003, 0.0, 0.001, (240, 240, 255, 5)),
    "WATER": MaterialData("Water", 1.333, 0.003, 0.05, (100, 200, 255, 40)),
    "GLASS": MaterialData("Glass (BK7)", 1.5168, 0.004, 0.1, (200, 255, 250, 60)),
    "FLINT": MaterialData("Flint Glass", 1.62, 0.01, 0.2, (220, 220, 255, 70)),
    "DIAMOND": MaterialData("Diamond", 2.417, 0.018, 0.0, (200, 255, 255, 90)),
    "ACRYLIC": MaterialData("Acrylic", 1.49, 0.002, 0.1, (240, 240, 240, 50)),
    "OIL": MaterialData("Oil", 1.47, 0.005, 0.3, (255, 255, 100, 80))
}