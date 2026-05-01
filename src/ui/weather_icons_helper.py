# ── Icon Cache ────────────────────────────────────────────────────────────────

_ASSET_CACHE: dict[tuple[str, int], Image.Image] = {}

def draw_weather_icon(img: Image.Image, description: str,
                      cx: int, cy: int, size: int = 52) -> None:
    """
    Dibuja un icono meteorológico. Intenta cargar un PNG de assets/weather,
    si falla, lo dibuja usando primitivas PIL.
    """
    import os
    try:
        from .theme import get_icon_key
        key_name = get_icon_key(description)
    except ImportError:
        # Fallback si no podemos importar theme
        key_name = "partly"
    
    # 1. Intentar cargar desde assets
    icon_filename = f"{key_name}.png"
    cache_key = (icon_filename, size)
    
    if cache_key not in _ASSET_CACHE:
        # Buscar la ruta de assets/weather
        base_dir = os.path.dirname(__file__)
        assets_path = os.path.join(base_dir, "..", "assets", "weather", icon_filename)
        
        if os.path.exists(assets_path):
            try:
                icon_img = Image.open(assets_path).convert("RGBA")
                icon_img = icon_img.resize((size, size), Image.LANCZOS)
                _ASSET_CACHE[cache_key] = icon_img
            except Exception:
                _ASSET_CACHE[cache_key] = None
        else:
            _ASSET_CACHE[cache_key] = None

    icon_asset = _ASSET_CACHE[cache_key]
    
    if icon_asset:
        # Pegar el asset con alpha
        img.paste(icon_asset, (cx - size // 2, cy - size // 2), icon_asset)
    else:
        # 2. Fallback: Dibujo manual (PIL Primitives)
        drawer = _DRAWERS.get(key_name, _draw_partly)
        drawer(img, cx, cy, size)
