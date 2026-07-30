import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..core.enums import ResourceType
from .models import World
from .runner import create_demo_world


DEFAULT_API_BASE_URL = os.environ.get(
    "EVOREALM_API_BASE_URL",
    "http://127.0.0.1:8000",
)


@dataclass(frozen=True)
class SeedResult:
    created: bool
    world_id: str
    world_name: str
    seed: int


def _serialize_inventory(
    inventory: dict[ResourceType, int],
) -> dict[str, int]:
    return {
        resource_type.value: quantity
        for resource_type, quantity in inventory.items()
    }


def serialize_world_creation_payload(
    world: World,
) -> dict[str, object]:
    return {
        "name": world.name,
        "seed": world.seed,
        "starting_tick": world.current_tick,
        "locations": [
            {
                "id": location.id,
                "name": location.name,
                "location_type": location.location_type.value,
                "x": location.x,
                "y": location.y,
                "capacity": location.capacity,
                "inventory": _serialize_inventory(
                    location.inventory
                ),
            }
            for location in world.locations
        ],
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "occupation": agent.occupation.value,
                "location_id": agent.location_id,
                "status": agent.status.value,
                "hunger": agent.hunger,
                "energy": agent.energy,
                "health": agent.health,
                "money": agent.money,
                "inventory": _serialize_inventory(agent.inventory),
                "personality_traits": dict(
                    agent.personality_traits
                ),
                "active_goal": agent.active_goal,
            }
            for agent in world.agents
        ],
    }


def _request_json(
    method: str,
    url: str,
    payload: dict[str, object] | None = None,
) -> object:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        message = error.reason
        try:
            body = json.loads(error.read().decode("utf-8"))
            if isinstance(body, dict) and isinstance(
                body.get("detail"),
                str,
            ):
                message = body["detail"]
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        raise RuntimeError(
            f"API request failed with status {error.code}: {message}"
        ) from error
    except URLError as error:
        raise RuntimeError(
            f"Could not connect to EvoRealm API: {error.reason}"
        ) from error


def seed_demo_world(
    *,
    seed: int,
    api_base_url: str = DEFAULT_API_BASE_URL,
) -> SeedResult:
    demo_world = create_demo_world(seed)
    base_url = api_base_url.rstrip("/")
    worlds = _request_json("GET", f"{base_url}/api/worlds")
    if not isinstance(worlds, list):
        raise RuntimeError("World listing returned an invalid response.")

    for world in worlds:
        if (
            isinstance(world, dict)
            and world.get("name") == demo_world.name
            and world.get("seed") == demo_world.seed
            and isinstance(world.get("id"), str)
        ):
            return SeedResult(
                created=False,
                world_id=world["id"],
                world_name=demo_world.name,
                seed=demo_world.seed,
            )

    created_world = _request_json(
        "POST",
        f"{base_url}/api/worlds",
        serialize_world_creation_payload(demo_world),
    )
    if (
        not isinstance(created_world, dict)
        or not isinstance(created_world.get("id"), str)
    ):
        raise RuntimeError("World creation returned an invalid response.")

    return SeedResult(
        created=True,
        world_id=created_world["id"],
        world_name=demo_world.name,
        seed=demo_world.seed,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create the EvoRealm demo world through the REST API.",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--api-base-url",
        default=DEFAULT_API_BASE_URL,
    )
    arguments = parser.parse_args(argv)

    try:
        result = seed_demo_world(
            seed=arguments.seed,
            api_base_url=arguments.api_base_url,
        )
    except RuntimeError as error:
        print(f"Seed failed: {error}")
        return 1

    action = "Created" if result.created else "Reused"
    print(
        f"{action} {result.world_name} "
        f"(seed {result.seed}) with ID {result.world_id}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
