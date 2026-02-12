import sqlite3
import json
from typing import Dict, Any, List, Optional
import os # Added missing import
import logging
logger = logging.getLogger(__name__)

class UnifiedSymbolicSpace:
    """
    Represents a unified symbolic space for the AGI, managing symbols, their properties,
    and relationships within a SQLite database.
    """

    def __init__(self, db_path: str = 'unified_symbolic_space.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol_name TEXT UNIQUE NOT NULL,
                type TEXT,
                properties TEXT, -- JSON string for flexible properties
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_symbol_id INTEGER,
                target_symbol_id INTEGER,
                relationship_type TEXT NOT NULL,
                properties TEXT, -- JSON string for relationship properties
                FOREIGN KEY (source_symbol_id) REFERENCES symbols(id),
                FOREIGN KEY (target_symbol_id) REFERENCES symbols(id)
            )
        """)
        conn.commit()
        conn.close()

    def add_symbol(self, symbol_name: str, symbol_type: str, properties: Optional[Dict[str, Any]] = None) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        props_json = json.dumps(properties) if properties else ''
        try:
            cursor.execute("INSERT INTO symbols (symbol_name, type, properties) VALUES (?, ?, ?)",
                           (symbol_name, symbol_type, props_json))
            symbol_id = cursor.lastrowid
            conn.commit()
            return symbol_id
        except sqlite3.IntegrityError:
            print(f"Symbol '{symbol_name}' already exists. Updating properties.")
            # Directly update the symbol to avoid database locking issues
            if properties:
                current_symbol = self.get_symbol(symbol_name)
                current_props = current_symbol['properties'] if current_symbol and current_symbol['properties'] else {}
                current_props.update(properties)
                props_json = json.dumps(current_props)
            cursor.execute("UPDATE symbols SET type = ?, properties = ?, last_updated = CURRENT_TIMESTAMP WHERE symbol_name = ?",
                           (symbol_type, props_json, symbol_name))
            conn.commit()
            cursor.execute("SELECT id FROM symbols WHERE symbol_name = ?", (symbol_name,))
            result = cursor.fetchone()
            symbol_id = result[0] if result else None
            conn.close()
            return symbol_id
        finally:
            if 'conn' in locals() and conn:
                conn.close()

    def get_symbol(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, symbol_name, type, properties FROM symbols WHERE symbol_name = ?", (symbol_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'symbol_name': row[1],
                'type': row[2],
                'properties': json.loads(row[3]) if row[3] else {}
            }
        return None

    def update_symbol(self, symbol_name: str, new_symbol_name: Optional[str] = None, new_type: Optional[str] = None, properties: Optional[Dict[str, Any]] = None):
        # Get current properties first to avoid connection issues
        current_props = {}
        if properties:
            current_symbol = self.get_symbol(symbol_name)
            current_props = current_symbol['properties'] if current_symbol and current_symbol['properties'] else {}
            current_props.update(properties)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        updates = []
        params = []

        if new_symbol_name:
            updates.append("symbol_name = ?")
            params.append(new_symbol_name)
        if new_type:
            updates.append("type = ?")
            params.append(new_type)
        if properties:
            updates.append("properties = ?")
            params.append(json.dumps(current_props))

        if not updates:
            conn.close()
            return False

        params.append(symbol_name)
        query = f"UPDATE symbols SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE symbol_name = ?"
        cursor.execute(query, tuple(params))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

    def add_relationship(self, source_symbol_name: str, target_symbol_name: str, relationship_type: str, properties: Optional[Dict[str, Any]] = None) -> Optional[int]:
        # Get symbols first to avoid connection issues
        source_symbol = self.get_symbol(source_symbol_name)
        target_symbol = self.get_symbol(target_symbol_name)

        if not source_symbol or not target_symbol:
            print(f"Error: Source symbol '{source_symbol_name}' or target symbol '{target_symbol_name}' not found.")
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        props_json = json.dumps(properties) if properties else ''
        cursor.execute("INSERT INTO relationships (source_symbol_id, target_symbol_id, relationship_type, properties) VALUES (?, ?, ?, ?)",
                       (source_symbol['id'], target_symbol['id'], relationship_type, props_json))
        rel_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rel_id

    def get_relationships(self, symbol_name: str) -> List[Dict[str, Any]]:
        # Get symbol first to avoid connection issues
        symbol = self.get_symbol(symbol_name)
        if not symbol:
            return []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.id, s_src.symbol_name, s_tgt.symbol_name, r.relationship_type, r.properties
            FROM relationships r
            JOIN symbols s_src ON r.source_symbol_id = s_src.id
            JOIN symbols s_tgt ON r.target_symbol_id = s_tgt.id
            WHERE s_src.symbol_name = ? OR s_tgt.symbol_name = ?
        """, (symbol_name, symbol_name))

        relationships = []
        for row in cursor.fetchall():
            relationships.append({
                'id': row[0],
                'source': row[1],
                'target': row[2],
                'type': row[3],
                'properties': json.loads(row[4]) if row[4] else {}
            })
        conn.close()
        return relationships

    def delete_symbol(self, symbol_name: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        symbol = self.get_symbol(symbol_name)
        if not symbol:
            conn.close()
            return False

        # Delete associated relationships first
        cursor.execute("DELETE FROM relationships WHERE source_symbol_id = ? OR target_symbol_id = ?", (symbol['id'], symbol['id']))
        cursor.execute("DELETE FROM symbols WHERE id = ?", (symbol['id'],))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

    def delete_relationship(self, rel_id: int) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM relationships WHERE id = ?", (rel_id,))
        conn.commit()
        rows_affected = cursor.rowcount
        conn.close()
        return rows_affected > 0

if __name__ == '__main__':
    # Example Usage
    uss = UnifiedSymbolicSpace('test_symbolic_space.db')

    # Add symbols
    uss.add_symbol('AI Assistant', 'Agent', {'version': '1.0', 'status': 'active'})
    uss.add_symbol('Sarah', 'Person', {'age': 30, 'occupation': 'engineer'})
    uss.add_symbol('Likes', 'Verb')
    uss.add_symbol('Python', 'ProgrammingLanguage', {'version': '3.9'})

    # Update symbol properties
    uss.update_symbol('AI Assistant', properties={'status': 'learning', 'model_type': 'AlphaDeepModel'})

    # Add relationships
    uss.add_relationship('Sarah', 'AI Assistant', 'likes', {'strength': 0.9})
    uss.add_relationship('AI Assistant', 'Python', 'uses', {'proficiency': 'high'})

    # Get symbols and relationships
    ai_assistant_symbol = uss.get_symbol('AI Assistant')
    print(f"\nAI Assistant Symbol: {ai_assistant_symbol}")

    sarah_relationships = uss.get_relationships('Sarah')
    print(f"Sarah's Relationships: {sarah_relationships}")

    ai_relationships = uss.get_relationships('AI Assistant')
    print(f"AI Assistant's Relationships: {ai_relationships}")

    # Delete a relationship
    if sarah_relationships:
        uss.delete_relationship(sarah_relationships[0]['id'])
        print(f"\nDeleted relationship: {sarah_relationships[0]['id']}")
        print(f"Sarah's Relationships after deletion: {uss.get_relationships('Sarah')}")

    # Delete a symbol
    uss.delete_symbol('Likes')
    print(f"\nLikes symbol after deletion: {uss.get_symbol('Likes')}")

    print("\nUnified Symbolic Space operations completed.")

    # Clean up test database
    if os.path.exists('test_symbolic_space.db'):
        os.remove('test_symbolic_space.db')
        print("Cleaned up test_symbolic_space.db")
