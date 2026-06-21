"""
main.py
Entry point for the Jobs Auto-Apply Agent.
"""

import asyncio
import yaml
from core.orchestrator import Orchestrator


def load_config(path: str = "config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


async def main():
    config = load_config()
    agent = Orchestrator(config)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
