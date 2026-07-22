"""
Test script for GlobalStateStore and Decoupling
"""

import asyncio

from core.engine.state_matrix import StateMatrix4D
from core.system.state_store import state_store


async def test_state_decoupling() -> None:
    """Test state decoupling behavior."""
    print("Testing State Decoupling Phase 2...")

    # 1. Initialize StateMatrix (which now syncs to Store)
    matrix = StateMatrix4D()

    # 2. Define a subscriber to verify broadcast
    received_updates = []

    def on_alpha_update(domain, data) -> None:
        """Handle the alpha update event."""
        received_updates.append((domain, data))
        print(f"   [Subscriber] Received {domain} update: {data}")

    state_store.subscribe("alpha", on_alpha_update)

    # 3. Update Matrix and check Store
    print("\nUpdating Alpha dimension in Matrix...")
    matrix.update_alpha(energy=0.9, comfort=0.8)

    # Wait a bit for async sync if any (though currently sync is synchronous in _post_update)
    await asyncio.sleep(0.1)

    store_alpha = state_store.get_state("alpha")
    print(f"Store Alpha Energy: {store_alpha.get('energy')}")

    assert store_alpha.get("energy") == 0.9
    assert len(received_updates) > 0
    print("\n✅ State decoupling test passed!")


