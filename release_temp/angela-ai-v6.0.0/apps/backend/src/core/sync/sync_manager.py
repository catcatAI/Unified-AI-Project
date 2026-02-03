import asyncio
from collections.abc import Callable
from typing import Any


class SyncManager:
    """Manages data synchronization across different modules and potentially external systems."""

    def __init__(self):
        """Initializes the SyncManager."""
        self._sync_targets: dict[str, Callable[[dict[str, Any]], Any]] = {}
        print("SyncManager initialized.")

    def register_sync_target(
        self,
        target_name: str,
        sync_function: Callable[[dict[str, Any]], Any],
    ):
        """Registers a function that will be called to synchronize data to a specific target.

        Args:
            target_name (str): A unique name for the synchronization target.
            sync_function (Callable): An async or sync function that accepts data to be synchronized.

        """
        if target_name in self._sync_targets:
            print(
                f"Warning: Sync target '{target_name}' is already registered and will be overwritten.",
            )
        self._sync_targets[target_name] = sync_function
        print(f"Sync target '{target_name}' registered.")

    async def synchronize_data(
        self,
        data: dict[str, Any],
        target_names: list[str] | None = None,
    ):
        """Synchronizes data to registered targets.

        Args:
            data (Dict[str, Any]): The data to be synchronized.
            target_names (Optional[List[str]]): A list of specific targets to synchronize to.
                                                If None, synchronizes to all registered targets.

        """
        targets_to_sync = (
            target_names
            if target_names is not None
            else list(self._sync_targets.keys())
        )

        if not targets_to_sync:
            print("No synchronization targets registered or specified.")
            return

        print(f"Synchronizing data to targets: {targets_to_sync}")
        for target_name in targets_to_sync:
            sync_function = self._sync_targets.get(target_name)
            if sync_function:
                try:
                    if asyncio.iscoroutinefunction(sync_function):
                        await sync_function(data)
                    else:
                        sync_function(data)
                    print(f"Successfully synchronized data to '{target_name}'.")
                except Exception as e:
                    print(f"Error synchronizing data to '{target_name}': {e}")
            else:
                print(f"Warning: Sync target '{target_name}' not found.")


if __name__ == "__main__":

    async def main():
        manager = SyncManager()

        # Example sync functions
        def console_logger(data: dict[str, Any]):
            print(f"Console Log Sync: {data}")

        async def remote_api_sync(data: dict[str, Any]):
            await asyncio.sleep(0.05)  # Simulate API call
            print(f"Remote API Sync: Sent {data}")

        # Register targets
        manager.register_sync_target("console_log", console_logger)
        manager.register_sync_target("remote_api", remote_api_sync)

        # Synchronize data
        print("\n--- Synchronizing all targets ---")
        await manager.synchronize_data({"event": "user_login", "user_id": "test_user"})

        print("\n--- Synchronizing specific target ---")
        await manager.synchronize_data(
            {"event": "data_update", "item_id": "item123"},
            target_names=["remote_api"],
        )

        print("\n--- Synchronizing non-existent target ---")
        await manager.synchronize_data({"event": "test"}, target_names=["non_existent"])

    asyncio.run(main())
