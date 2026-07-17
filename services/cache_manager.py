"""
Gerenciador de Cache com SQLite
Supporta versionamento de schema e migração automática
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
import pickle
import gzip

class CacheManager:
    """
    Gerenciador de cache com SQLite com versionamento de schema
    e rotação automática de logs
    """
    
    SCHEMA_VERSION = 2
    DB_PATH = "data/cache.db"
    
    def __init__(self):
        os.makedirs(os.path.dirname(self.DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(self.DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self._initialize_schema()
    
    def _get_current_version(self) -> int:
        """Obtém versão atual do schema"""
        try:
            cursor = self.conn.execute(
                "SELECT schema_version FROM cache_metadata LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else 0
        except sqlite3.OperationalError:
            return 0
    
    def _initialize_schema(self):
        """Inicializa ou migra schema se necessário"""
        current_version = self._get_current_version()
        
        if current_version < 1:
            self._migrate_to_v1()
        
        if current_version < 2:
            self._migrate_to_v2()
    
    def _migrate_to_v1(self):
        """Primeira versão do schema"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                id INTEGER PRIMARY KEY,
                schema_version INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value BLOB NOT NULL,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hits INTEGER DEFAULT 0
            )
        """)
        
        self.conn.execute("""
            CREATE INDEX idx_expires ON cache_entries(expires_at)
        """)
        
        self.conn.execute(
            "INSERT INTO cache_metadata (schema_version) VALUES (1)"
        )
        self.conn.commit()
    
    def _migrate_to_v2(self):
        """Versão 2: adicionar tracking de origem"""
        try:
            self.conn.execute("""
                ALTER TABLE cache_entries ADD COLUMN source TEXT DEFAULT 'unknown'
            """)
        except sqlite3.OperationalError:
            pass
        
        try:
            self.conn.execute("""
                ALTER TABLE cache_entries ADD COLUMN ttl_seconds INTEGER DEFAULT 2592000
            """)
        except sqlite3.OperationalError:
            pass
        
        self.conn.execute(
            "UPDATE cache_metadata SET schema_version = 2 WHERE id = 1"
        )
        self.conn.commit()
    
    def set(self, key: str, value: Any, ttl: int = 2592000, source: str = "unknown") -> bool:
        """Salva valor em cache com TTL"""
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        try:
            serialized = pickle.dumps(value)
            self.conn.execute("""
                INSERT OR REPLACE INTO cache_entries 
                (key, value, expires_at, ttl_seconds, source, hits)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (key, serialized, expires_at, ttl, source, 0))
            
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar em cache: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Recupera valor do cache se válido"""
        try:
            cursor = self.conn.execute("""
                SELECT value, expires_at FROM cache_entries 
                WHERE key = ? AND expires_at > CURRENT_TIMESTAMP
            """, (key,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Incrementar hits
            self.conn.execute("""
                UPDATE cache_entries SET hits = hits + 1 WHERE key = ?
            """, (key,))
            self.conn.commit()
            
            return pickle.loads(row[0])
        
        except Exception as e:
            print(f"❌ Erro ao ler cache: {e}")
            return None
    
    def cleanup_expired(self) -> int:
        """Remove entradas expiradas"""
        try:
            cursor = self.conn.execute("""
                DELETE FROM cache_entries 
                WHERE expires_at < CURRENT_TIMESTAMP
            """)
            
            deleted = cursor.rowcount
            self.conn.commit()
            return deleted
        except Exception as e:
            print(f"❌ Erro ao limpar cache: {e}")
            return 0
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        try:
            cursor = self.conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hits) as total_hits,
                    AVG(hits) as avg_hits,
                    (SELECT COUNT(*) FROM cache_entries WHERE expires_at < CURRENT_TIMESTAMP) as expired
                FROM cache_entries
            """)
            
            row = cursor.fetchone()
            
            return {
                "total_entries": row[0],
                "total_hits": row[1] or 0,
                "avg_hits": row[2] or 0,
                "expired_entries": row[3]
            }
        except Exception as e:
            return {"erro": str(e)}
    
    def close(self):
        """Fecha conexão"""
        self.conn.close()
