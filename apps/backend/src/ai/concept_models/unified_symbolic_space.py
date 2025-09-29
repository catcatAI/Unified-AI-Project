"""
统一符号空间
实现完整的符号空间功能，包括符号管理、关系管理和查询接口
"""

import asyncio
import logging
import json
import sqlite3
from enum import Enum

logger: Any = logging.getLogger(__name__)

class SymbolType(Enum):
    """符号类型"""
    ENTITY = "entity"
    CONCEPT = "concept"
    ACTION = "action"
    PROPERTY = "property"
    RELATIONSHIP = "relationship"
    MEMORY = "memory"
    GIST = "gist"
    FEEDBACK = "feedback"
    UNKNOWN = "unknown"

@dataclass
class Symbol:
    """符号"""
    id: int
    name: str
    type: SymbolType
    properties: Dict[str, Any]
    last_updated: float

@dataclass
class Relationship:
    """关系"""
    id: int
    source_symbol_id: int
    target_symbol_id: int
    type: str
    properties: Dict[str, Any]

class UnifiedSymbolicSpace:
    """统一符号空间"""
    
    def __init__(self, db_path: str = 'unified_symbolic_space.db') -> None:
        self.db_path = db_path
        self._init_db
        self.logger = logging.getLogger(__name__)
        
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        # 创建符号表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                properties TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_symbol_id INTEGER NOT NULL,
                target_symbol_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                properties TEXT,
                _ = FOREIGN KEY (source_symbol_id) REFERENCES symbols(id),
                _ = FOREIGN KEY (target_symbol_id) REFERENCES symbols(id)
            )
        """)
        
        # 创建索引以提高查询性能
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_symbol_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_symbol_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(type)")
        
        conn.commit
        conn.close
        
    async def add_symbol(self, name: str, symbol_type: SymbolType, 
                        properties: Optional[Dict[str, Any]] = None) -> int:
        """添加符号"""
        logger.debug(f"Adding symbol: {name} of type {symbol_type.value}")
        _ = await asyncio.sleep(0.005)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        props_json = json.dumps(properties) if properties else ''
        
        try:
            cursor.execute("""
                _ = INSERT INTO symbols (name, type, properties) 
                _ = VALUES (?, ?, ?)
            _ = """, (name, symbol_type.value, props_json))
            symbol_id = cursor.lastrowid
            conn.commit
            logger.info(f"Symbol '{name}' added with ID {symbol_id}")
            return symbol_id
        except sqlite3.IntegrityError:
            logger.warning(f"Symbol '{name}' already exists. Updating properties.")
            # 更新现有符号
            if properties:
                current_symbol = await self.get_symbol_by_name(name)
                if current_symbol:
                    current_props = current_symbol.properties
                    current_props.update(properties)
                    props_json = json.dumps(current_props)
            cursor.execute("""
                UPDATE symbols 
                SET type = ?, properties = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE name = ?
            _ = """, (symbol_type.value, props_json, name))
            conn.commit
            
            # 获取更新后的符号ID
            cursor.execute("SELECT id FROM symbols WHERE name = ?", (name,))
            row = cursor.fetchone
            symbol_id = row[0] if row else -1
            
        finally:
            conn.close
            
        return symbol_id
        
    async def get_symbol_by_name(self, name: str) -> Optional[Symbol]:
        """根据名称获取符号"""
        logger.debug(f"Getting symbol by name: {name}")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        cursor.execute("""
            SELECT id, name, type, properties, last_updated 
            FROM symbols 
            WHERE name = ?
        _ = """, (name,))
        row = cursor.fetchone
        conn.close
        
        if row:
            return Symbol(
                id=row[0],
                name=row[1],
                type=SymbolType(row[2]),
                properties=json.loads(row[3]),
                last_updated=row[4]
            )
        return None
        
    async def get_symbol_by_id(self, symbol_id: int) -> Optional[Symbol]:
        """根据ID获取符号"""
        logger.debug(f"Getting symbol by ID: {symbol_id}")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        cursor.execute("""
            SELECT id, name, type, properties, last_updated 
            FROM symbols 
            WHERE id = ?
        _ = """, (symbol_id,))
        row = cursor.fetchone
        conn.close
        
        if row:
            return Symbol(
                id=row[0],
                name=row[1],
                type=SymbolType(row[2]),
                properties=json.loads(row[3]),
                last_updated=row[4]
            )
        return None
        
    async def update_symbol(self, symbol_id: int, name: Optional[str] = None, 
                           symbol_type: Optional[SymbolType] = None, 
                           properties: Optional[Dict[str, Any]] = None) -> bool:
        """更新符号"""
        logger.debug(f"Updating symbol ID: {symbol_id}")
        _ = await asyncio.sleep(0.005)
        
        # 获取当前符号以合并属性
        current_symbol = await self.get_symbol_by_id(symbol_id)
        if not current_symbol:
            logger.error(f"Symbol with ID {symbol_id} not found")
            return False
            
        current_props = current_symbol.properties
        if properties:
            current_props.update(properties)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        updates = []
        params = [] 

        if name:
            updates.append("name = ?")
            params.append(name)
        if symbol_type:
            updates.append("type = ?")
            params.append(symbol_type.value)
        if properties:
            updates.append("properties = ?")
            params.append(json.dumps(current_props))
            
        if not updates:
            conn.close
            return False

        params.append(symbol_id)
        query = f"UPDATE symbols SET {', '.join(updates)}, last_updated = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, tuple(params))
        conn.commit
        rows_affected = cursor.rowcount
        conn.close
        
        if rows_affected > 0:
            logger.info(f"Symbol ID {symbol_id} updated successfully")
        else:
            logger.warning(f"No rows affected when updating symbol ID {symbol_id}")
            
        return rows_affected > 0
        
    async def delete_symbol(self, symbol_id: int) -> bool:
        """删除符号"""
        logger.debug(f"Deleting symbol ID: {symbol_id}")
        _ = await asyncio.sleep(0.005)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        # 先删除相关的关系
        cursor.execute("DELETE FROM relationships WHERE source_symbol_id = ? OR target_symbol_id = ?", 
                      (symbol_id, symbol_id))
        
        # 删除符号
        cursor.execute("DELETE FROM symbols WHERE id = ?", (symbol_id,))
        conn.commit
        rows_affected = cursor.rowcount
        conn.close
        
        if rows_affected > 0:
            logger.info(f"Symbol ID {symbol_id} deleted successfully")
        else:
            logger.warning(f"No rows affected when deleting symbol ID {symbol_id}")
            
        return rows_affected > 0
        
    async def list_symbols(self, symbol_type: Optional[SymbolType] = None, 
                          limit: int = 100) -> List[Symbol]:
        """列出符号"""
        logger.debug(f"Listing symbols (type: {symbol_type}, limit: {limit})")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        if symbol_type:
            cursor.execute("""
                SELECT id, name, type, properties, last_updated 
                FROM symbols 
                WHERE type = ? 
                ORDER BY last_updated DESC 
                LIMIT ?
            _ = """, (symbol_type.value, limit))
        else:
            cursor.execute("""
                SELECT id, name, type, properties, last_updated 
                FROM symbols 
                ORDER BY last_updated DESC 
                LIMIT ?
            _ = """, (limit,))
            
        symbols = 
        for row in cursor.fetchall:
            symbol = Symbol(
                id=row[0],
                name=row[1],
                type=SymbolType(row[2]),
                properties=json.loads(row[3]),
                last_updated=row[4]
            )
            symbols.append(symbol)
            
        conn.close
        return symbols
        
    async def add_relationship(self, source_symbol_id: int, target_symbol_id: int, 
                              relationship_type: str, 
                              properties: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """添加关系"""
        logger.debug(f"Adding relationship: {source_symbol_id} --{relationship_type}--> {target_symbol_id}")
        _ = await asyncio.sleep(0.005)
        
        # 验证符号是否存在
        source_symbol = await self.get_symbol_by_id(source_symbol_id)
        target_symbol = await self.get_symbol_by_id(target_symbol_id)
        
        if not source_symbol or not target_symbol:
            logger.error(f"Source symbol {source_symbol_id} or target symbol {target_symbol_id} not found")
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        props_json = json.dumps(properties) if properties else ''
        
        try:
            cursor.execute("""
                INSERT INTO relationships 
                (source_symbol_id, target_symbol_id, type, properties) 
                _ = VALUES (?, ?, ?, ?)
            _ = """, (source_symbol_id, target_symbol_id, relationship_type, props_json))
            relationship_id = cursor.lastrowid
            conn.commit
            logger.info(f"Relationship added with ID {relationship_id}")
            return relationship_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Error adding relationship: {e}")
            return None
        finally:
            conn.close
            
    async def get_relationships_by_symbol(self, symbol_id: int) -> List[Relationship]:
        """获取与符号相关的关系"""
        logger.debug(f"Getting relationships for symbol ID: {symbol_id}")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        cursor.execute("""
            SELECT id, source_symbol_id, target_symbol_id, type, properties
            FROM relationships 
            WHERE source_symbol_id = ? OR target_symbol_id = ?
        _ = """, (symbol_id, symbol_id))
        
        relationships = 
        for row in cursor.fetchall:
            relationship = Relationship(
                id=row[0],
                source_symbol_id=row[1],
                target_symbol_id=row[2],
                type=row[3],
                properties=json.loads(row[4])
            )
            relationships.append(relationship)
            
        conn.close
        return relationships
        
    async def get_relationships_by_type(self, relationship_type: str, 
                                      limit: int = 100) -> List[Relationship]:
        """根据类型获取关系"""
        logger.debug(f"Getting relationships of type: {relationship_type}")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        cursor.execute("""
            SELECT id, source_symbol_id, target_symbol_id, type, properties
            FROM relationships 
            WHERE type = ? 
            LIMIT ?
        _ = """, (relationship_type, limit))
        
        relationships = 
        for row in cursor.fetchall:
            relationship = Relationship(
                id=row[0],
                source_symbol_id=row[1],
                target_symbol_id=row[2],
                type=row[3],
                properties=json.loads(row[4])
            )
            relationships.append(relationship)
            
        conn.close
        return relationships
        
    async def delete_relationship(self, relationship_id: int) -> bool:
        """删除关系"""
        logger.debug(f"Deleting relationship ID: {relationship_id}")
        _ = await asyncio.sleep(0.005)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        cursor.execute("DELETE FROM relationships WHERE id = ?", (relationship_id,))
        conn.commit
        rows_affected = cursor.rowcount
        conn.close
        
        if rows_affected > 0:
            logger.info(f"Relationship ID {relationship_id} deleted successfully")
        else:
            logger.warning(f"No rows affected when deleting relationship ID {relationship_id}")
            
        return rows_affected > 0
        
    async def query_symbols_by_property(self, property_key: str, 
                                      property_value: Any) -> List[Symbol]:
        """根据属性查询符号"""
        logger.debug(f"Querying symbols by property: {property_key} = {property_value}")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        # 注意：这是一个简化的实现，实际应用中可能需要更复杂的JSON查询
        cursor.execute("""
            SELECT id, name, type, properties, last_updated 
            FROM symbols 
            WHERE json_extract(properties, ?) = ?
        _ = """, (f"$.{property_key}", property_value))
        
        symbols = 
        for row in cursor.fetchall:
            symbol = Symbol(
                id=row[0],
                name=row[1],
                type=SymbolType(row[2]),
                properties=json.loads(row[3]),
                last_updated=row[4]
            )
            symbols.append(symbol)
            
        conn.close
        return symbols
        
    async def find_connected_symbols(self, symbol_id: int, 
                                   max_depth: int = 3) -> Dict[int, List[int]]:
        """查找连接的符号（图遍历）"""
        logger.debug(f"Finding connected symbols for ID {symbol_id} (max depth: {max_depth})")
        _ = await asyncio.sleep(0.01)
        
        connected = {0: [symbol_id]}  # 按深度分组
        visited = set([symbol_id])
        current_level = [symbol_id]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        for depth in range(1, max_depth + 1):
            next_level = 
            
            for current_symbol_id in current_level:
                # 查找直接连接的符号
                cursor.execute("""
                    SELECT source_symbol_id, target_symbol_id
                    FROM relationships 
                    WHERE source_symbol_id = ? OR target_symbol_id = ?
                _ = """, (current_symbol_id, current_symbol_id))
                
                for row in cursor.fetchall:
                    source_id, target_id = row
                    # 确定邻居ID（不是当前符号的另一个符号）
                    neighbor_id = target_id if source_id == current_symbol_id else source_id
                    
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        next_level.append(neighbor_id)
                        
            if not next_level:
                break
                
            connected[depth] = next_level
            current_level = next_level
            
        conn.close
        return connected
        
    async def get_symbol_statistics(self) -> Dict[str, Any]:
        """获取符号空间统计信息"""
        logger.debug("Getting symbol space statistics")
        _ = await asyncio.sleep(0.01)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor
        
        # 符号总数
        cursor.execute("SELECT COUNT(*) FROM symbols")
        total_symbols = cursor.fetchone[0]
        
        # 按类型分组的符号数量
        cursor.execute("SELECT type, COUNT(*) FROM symbols GROUP BY type")
        symbols_by_type = dict(cursor.fetchall)
        
        # 关系总数
        cursor.execute("SELECT COUNT(*) FROM relationships")
        total_relationships = cursor.fetchone[0]
        
        # 按类型分组的关系数量
        cursor.execute("SELECT type, COUNT(*) FROM relationships GROUP BY type")
        relationships_by_type = dict(cursor.fetchall)
        
        conn.close
        
        return {
            "total_symbols": total_symbols,
            "symbols_by_type": symbols_by_type,
            "total_relationships": total_relationships,
            "relationships_by_type": relationships_by_type
        }

# 测试代码
if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建统一符号空间
    symbolic_space = UnifiedSymbolicSpace("test_symbolic_space.db")
    
    # 创建测试数据
    async def test_symbolic_space -> None:
        # 添加符号
        print("Adding symbols...")
        ai_assistant_id = await symbolic_space.add_symbol(
            "AI Assistant", 
            SymbolType.ENTITY, 
            {"version": "1.0", "status": "active"}
        )
        print(f"AI Assistant symbol ID: {ai_assistant_id}")
        
        sarah_id = await symbolic_space.add_symbol(
            "Sarah", 
            SymbolType.ENTITY, 
            {"age": 30, "occupation": "engineer"}
        )
        print(f"Sarah symbol ID: {sarah_id}")
        
        likes_id = await symbolic_space.add_symbol(
            "Likes", 
            SymbolType.RELATIONSHIP, 
            
        )
        print(f"Likes symbol ID: {likes_id}")
        
        python_id = await symbolic_space.add_symbol(
            "Python", 
            SymbolType.CONCEPT, 
            {"version": "3.9"}
        )
        print(f"Python symbol ID: {python_id}")
        
        # 更新符号属性
        await symbolic_space.update_symbol(
            ai_assistant_id, 
            properties={"status": "learning", "model_type": "AlphaDeepModel"}
        )
        print("Updated AI Assistant symbol")
        
        # 添加关系
        print("\nAdding relationships...")
        relationship_id = await symbolic_space.add_relationship(
            sarah_id, 
            python_id, 
            "likes", 
            {"strength": 0.8, "reason": "programming"}
        )
        print(f"Relationship ID: {relationship_id}")
        
        # 查询符号
        print("\nQuerying symbols...")
        ai_symbol = await symbolic_space.get_symbol_by_name("AI Assistant")
        print(f"AI Assistant symbol: {ai_symbol}")
        
        sarah_symbol = await symbolic_space.get_symbol_by_id(sarah_id)
        print(f"Sarah symbol: {sarah_symbol}")
        
        # 查询关系
        print("\nQuerying relationships...")
        relationships = await symbolic_space.get_relationships_by_symbol(sarah_id)
        print(f"Sarah relationships: {len(relationships)} found")
        for rel in relationships:
            source = await symbolic_space.get_symbol_by_id(rel.source_symbol_id)
            target = await symbolic_space.get_symbol_by_id(rel.target_symbol_id)
            print(f"  {source.name} --{rel.type}--> {target.name}")
            
        # 列出符号
        print("\nListing symbols...")
        all_symbols = await symbolic_space.list_symbols(limit=10)
        print(f"Total symbols: {len(all_symbols)}")
        for symbol in all_symbols:
            print(f"  {symbol.name} ({symbol.type.value})")
            
        # 按类型列出符号
        print("\nListing entity symbols...")
        entity_symbols = await symbolic_space.list_symbols(SymbolType.ENTITY, limit=10)
        print(f"Entity symbols: {len(entity_symbols)} found")
        for symbol in entity_symbols:
            print(f"  {symbol.name}")
            
        # 查找连接的符号
        print("\nFinding connected symbols...")
        connected = await symbolic_space.find_connected_symbols(sarah_id, max_depth=2)
        print(f"Connected symbols: {connected}")
        
        # 获取统计信息
        print("\nGetting statistics...")
        stats = await symbolic_space.get_symbol_statistics
        print(f"Statistics: {stats}")
        
        # 根据属性查询符号
        print("\nQuerying symbols by property...")
        python_symbols = await symbolic_space.query_symbols_by_property("version", "3.9")
        print(f"Symbols with version 3.9: {len(python_symbols)} found")
        for symbol in python_symbols:
            print(f"  {symbol.name}")
    
    # 运行测试
    asyncio.run(test_symbolic_space)