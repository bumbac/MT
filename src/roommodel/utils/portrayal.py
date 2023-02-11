def hex_to_rgb(value):
    """Return (red, green, blue) for the color given as #rrggbb."""
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(red, green, blue) -> str:
    """Return color as #rrggbb for the given color values."""
    return '#%02x%02x%02x' % (red, green, blue)


def create_color(agent, hex=True):
    color = [0, 0, 0]
    if agent.name.startswith("Cell"):
        color = [0, 255, 128]
    if agent.name.startswith("Leader"):
        color = [255, 0, 0]
    if agent.name.startswith("Follower"):
        color = [0, 0, 255]
    if agent.name.startswith("Follower Pair"):
        hash_value = hash(agent.name)
        r = hash_value % 256
        g = hash_value % 64
        b = hash_value % 128
        color = [r, g, b]
    if hex:
        return rgb_to_hex(*color)


def agent_portrayal(agent):
    portrayal = {
        "Shape": "rect",
        "Color": agent.color,
        "Filled": "true",
        "Layer": 0,
        "w": 1,
        "h": 1,
        "text": agent.pos,
        "text_color": "black"
    }
    if agent.name.startswith("Leader"):
        portrayal = {
            "Shape": "circle",
            "Color": agent.color,
            "Filled": "true",
            "Layer": 1,
            "r": 0.8,
            "text": agent.unique_id,
            "text_color": "black"
        }
        return portrayal

    if agent.name.startswith("Follower"):
        portrayal = {
            "Shape": "arrowHead",
            "scale": 1,
            "heading_x": agent.orientation.heading()[0],
            "heading_y": agent.orientation.heading()[1],
            "Color": agent.color,
            "Filled": "true",
            "Layer": 2,
            "text": agent.unique_id,
            "text_color": "white"
        }
        return portrayal
    return portrayal
