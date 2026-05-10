"""
Lunar Phase Service - Calculates current moon phase
"""

import ephem
class LunarService:
    """Calculates moon phase and illumination"""

    PHASE_NAMES_ES = [
        "Luna Nueva",
        "Luna Creciente",
        "Cuarto Creciente",
        "Gibosa Creciente",
        "Luna Llena",
        "Gibosa Menguante",
        "Cuarto Menguante",
        "Luna Menguante"
    ]

    def __init__(self, lat=39.94, lon=-0.10):
        self.observer = ephem.Observer()
        self.observer.lat = str(lat)
        self.observer.lon = str(lon)
        self.moon = ephem.Moon()

    def get_phase(self):
        now = ephem.now()
        self.observer.date = now
        self.moon.compute(self.observer)

        prev_new = ephem.previous_new_moon(now)
        next_new = ephem.next_new_moon(now)
        cycle = float(next_new - prev_new)
        age = float(now - prev_new)
        phase = (age / cycle) % 1.0
        illumination = self.moon.phase

        phase_index = int(phase * 8 + 0.5) % 8
        phase_name = self.PHASE_NAMES_ES[phase_index]

        return {
            "phase": phase,
            "illumination": illumination,
            "phase_index": phase_index,
            "phase_name": phase_name
        }

    def get_phase_name(self):
        return self.get_phase()["phase_name"]

    def get_illumination(self):
        return self.get_phase()["illumination"]

    def get_phase_index(self):
        return self.get_phase()["phase_index"]
