import shutil
import os

def copy_ui():
    os.makedirs('src/assets/menu_icons', exist_ok=True)
    
    # 1. UI files
    ui_files = ['weather_icons.py', 'round_home.py', 'rect_ui.py', 'theme.py']
    for f in ui_files:
        src = os.path.join('src', 'deploy', 'src', 'ui', f)
        dst = os.path.join('src', 'ui', f)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {src} -> {dst}")

    # 2. Assets from deploy
    src_icons1 = os.path.join('src', 'deploy', 'src', 'assets', 'menu_icons')
    if os.path.exists(src_icons1):
        for f in os.listdir(src_icons1):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(src_icons1, f), os.path.join('src', 'assets', 'menu_icons', f))
                print(f"Copied icon {f} from deploy")

    # 3. Assets from deploy2 (newer icons)
    src_icons2 = os.path.join('src', 'deploy2', 'src', 'assets', 'menu_icons')
    if os.path.exists(src_icons2):
        for f in os.listdir(src_icons2):
            if f.endswith('.png'):
                shutil.copy2(os.path.join(src_icons2, f), os.path.join('src', 'assets', 'menu_icons', f))
                print(f"Copied icon {f} from deploy2")

if __name__ == "__main__":
    copy_ui()
