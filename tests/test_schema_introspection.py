import asyncio
import os
import unittest
from src.utils.schema_inspector import SchemaInspector, ANCHOR_POSITIONS


def get_game_db_dsn() -> str:
    url = os.getenv("GAME_DATABASE_URL")
    if not url:
        return "postgresql+asyncpg://postgres:postgres@localhost:5430/game_db"
    if "postgres:5432" in url:
        return url.replace("postgres:5432", "localhost:5430")
    return url


class TestSchemaIntrospection(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.dsn = get_game_db_dsn()
        self.inspector = SchemaInspector(self.dsn)

    async def test_inspect_tables_contains_battle_military_unit(self):
        try:
            schema = await self.inspector.get_schema(refresh=True)
        except Exception as e:
            self.skipTest(f"game_db at {self.dsn} is not reachable ({e})")

        self.assertIn("nodes", schema)
        self.assertIn("edges", schema)

        nodes = schema["nodes"]
        edges = schema["edges"]

        node_ids = {n["id"] for n in nodes}
        expected_tables = {
            "battle",
            "battle_enemy_unit",
            "battle_military_unit",
            "enemy_unit",
            "equipment",
            "equipment_assignment",
            "medal",
            "military_service",
            "military_unit",
            "soldier",
            "soldier_medal",
        }
        for tbl in expected_tables:
            self.assertIn(tbl, node_ids, f"Table {tbl} must be present in schema nodes")

        # Verify battle_military_unit structure
        bmu_node = next((n for n in nodes if n["id"] == "battle_military_unit"), None)
        self.assertIsNotNone(bmu_node, "battle_military_unit node must exist")
        col_names = [c["title"] for c in bmu_node["data"]["columns"]]
        self.assertIn("battle_id", col_names)
        self.assertIn("unit_id", col_names)

        # Verify foreign keys for battle_military_unit
        bmu_edges = [
            e for e in edges
            if e["source"] == "battle_military_unit" or e["target"] == "battle_military_unit"
        ]
        self.assertGreaterEqual(len(bmu_edges), 2, "battle_military_unit must have edges to battle and military_unit")

        targets_or_sources = {
            e["target"] if e["source"] == "battle_military_unit" else e["source"]
            for e in bmu_edges
        }
        self.assertIn("battle", targets_or_sources)
        self.assertIn("military_unit", targets_or_sources)

    async def test_all_nodes_have_valid_coordinates(self):
        try:
            schema = await self.inspector.get_schema()
        except Exception as e:
            self.skipTest(f"game_db at {self.dsn} is not reachable ({e})")

        nodes = schema["nodes"]
        for node in nodes:
            pos = node["position"]
            self.assertIsInstance(pos["x"], (int, float))
            self.assertIsInstance(pos["y"], (int, float))

    async def test_cache_reuse(self):
        try:
            schema1 = await self.inspector.get_schema()
            schema2 = await self.inspector.get_schema(refresh=False)
        except Exception as e:
            self.skipTest(f"game_db at {self.dsn} is not reachable ({e})")

        self.assertIs(schema1, schema2, "Repeated call without refresh must return cached object")


if __name__ == "__main__":
    unittest.main()
