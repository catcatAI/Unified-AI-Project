"""Tests for GenesisManager - AI core identity component management."""

import pytest
from apps.backend.src.ai.genesis import GenesisManager


class TestGenesisManager:
    def test_create_genesis_secret_returns_uid_and_secret(self):
        secret, uid = GenesisManager.create_genesis_secret()
        assert uid.startswith("uid_")
        assert len(uid) > 4
        assert secret.startswith(uid + ":")
        assert len(secret) > len(uid)

    def test_create_genesis_secret_unique(self):
        secret1, uid1 = GenesisManager.create_genesis_secret()
        secret2, uid2 = GenesisManager.create_genesis_secret()
        assert uid1 != uid2
        assert secret1 != secret2

    def test_split_into_shards_returns_three(self):
        secret, _ = GenesisManager.create_genesis_secret()
        shards = GenesisManager.split_secret_into_shards(secret)
        assert len(shards) == 3
        for shard in shards:
            assert ":" in shard

    def test_recover_from_two_shards(self):
        secret, _ = GenesisManager.create_genesis_secret()
        shards = GenesisManager.split_secret_into_shards(secret)
        recovered = GenesisManager.recover_secret_from_shards(shards[:2])
        assert recovered == secret

    def test_recover_from_three_shards(self):
        secret, _ = GenesisManager.create_genesis_secret()
        shards = GenesisManager.split_secret_into_shards(secret)
        recovered = GenesisManager.recover_secret_from_shards(shards)
        assert recovered == secret

    def test_recover_fails_with_single_shard(self):
        secret, _ = GenesisManager.create_genesis_secret()
        shards = GenesisManager.split_secret_into_shards(secret)
        recovered = GenesisManager.recover_secret_from_shards(shards[:1])
        assert recovered is None

    def test_recover_fails_with_empty_list(self):
        recovered = GenesisManager.recover_secret_from_shards([])
        assert recovered is None
