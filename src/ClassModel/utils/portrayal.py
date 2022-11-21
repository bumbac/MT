def hex_to_rgb(value):
    """Return (red, green, blue) for the color given as #rrggbb."""
    value = value.lstrip('#')
    lv = len(value)
    return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))


def rgb_to_hex(red, green, blue):
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
    if hex:
        return rgb_to_hex(*color)

def agent_portrayal(agent):
    portrayal = {
        "Shape": "rect",
        "Color": agent.color,
        "Filled": "true",
        "Layer": 0,
        "w": 1,
        "h": 1}
    if agent.name.startswith("A"):
        portrayal = {
            "Shape": "circle",
            "Color": agent.color,
            "Filled": "true",
            "Layer": 1,
            "r": 0.5
        }

    if agent.name.startswith("F"):
        portrayal = {
            "Shape": "circle",
            "Color": agent.color,
            "Filled": "true",
            "Layer": 2,
            "r": 0.5
        }

    return portrayal
