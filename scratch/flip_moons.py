from PIL import Image
import os

def flip_image(source, dest):
    if os.path.exists(source):
        img = Image.open(source)
        flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
        flipped.save(dest)
        print(f"Flipped {source} to {dest}")
    else:
        print(f"Source {source} not found")

base_path = r"d:\Reloj_despertador\src\assets\moon_phases"

# Main stylized moons
flip_image(os.path.join(base_path, "waxing_crescent.png"), os.path.join(base_path, "waning_crescent.png"))
flip_image(os.path.join(base_path, "first_quarter.png"), os.path.join(base_path, "last_quarter.png"))
flip_image(os.path.join(base_path, "waxing_gibbous.png"), os.path.join(base_path, "waning_gibbous.png"))

# Kawaii moons
kawaii_path = os.path.join(base_path, "kawaii")
flip_image(os.path.join(kawaii_path, "waxing_crescent.png"), os.path.join(kawaii_path, "waning_crescent.png"))
flip_image(os.path.join(kawaii_path, "first_quarter.png"), os.path.join(kawaii_path, "last_quarter.png"))
# Note: waxing_gibbous_kawaii is missing, so we can't flip it yet.
