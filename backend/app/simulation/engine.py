from .models import World


def advance_tick(world: World) -> World:
    world.current_tick += 1

    for agent in world.agents:
        agent.hunger = min(agent.hunger + 2, 100)

    return world
