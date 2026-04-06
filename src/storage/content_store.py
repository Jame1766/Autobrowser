"""
内容存储模块
使用 SQLite 存储爬取的内容和发布记录
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContentStore:
    """内容存储管理器"""

    def __init__(self, db_path: str = "data/content.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contents (
                    id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT,
                    author TEXT,
                    created_at TEXT,
                    engagement TEXT,
                    raw_data TEXT,
                    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    score REAL DEFAULT 0.0
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    platform TEXT,
                    status TEXT,
                    message TEXT,
                    FOREIGN KEY (content_id) REFERENCES contents(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS crawl_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    keyword TEXT,
                    count INTEGER,
                    status TEXT
                )
            """)

            conn.commit()
        logger.info("数据库初始化完成")

    def save_contents(self, contents: List[Dict[str, Any]]):
        """保存爬取的内容"""
        with sqlite3.connect(self.db_path) as conn:
            for item in contents:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO contents
                        (id, platform, title, content, url, author, created_at, engagement, raw_data, crawled_at, status, score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item['id'],
                        item['platform'],
                        item['title'],
                        item['content'],
                        item['url'],
                        item['author'],
                        item['created_at'],
                        json.dumps(item.get('engagement', {})),
                        json.dumps(item.get('raw_data', {})),
                        datetime.now().isoformat(),
                        item.get('status', 'pending'),
                        item.get('score', 0.0)
                    ))
                except Exception as e:
                    logger.error(f"保存内容失败 {item.get('id')}: {e}")
            conn.commit()
        logger.info(f"保存 {len(contents)} 条内容到数据库")

    def get_pending_contents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取待处理的内容"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM contents WHERE status = 'pending' ORDER BY score DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()

            results = []
            for row in rows:
                item = dict(row)
                item['engagement'] = json.loads(item.get('engagement', '{}'))
                item['raw_data'] = json.loads(item.get('raw_data', '{}'))
                results.append(item)

            return results

    def update_content_status(self, content_id: str, status: str, score: Optional[float] = None):
        """更新内容状态"""
        with sqlite3.connect(self.db_path) as conn:
            if score is not None:
                conn.execute(
                    "UPDATE contents SET status = ?, score = ? WHERE id = ?",
                    (status, score, content_id)
                )
            else:
                conn.execute(
                    "UPDATE contents SET status = ? WHERE id = ?",
                    (status, content_id)
                )
            conn.commit()

    def log_crawl(self, source: str, keyword: str, count: int, status: str = 'success'):
        """记录爬取日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO crawl_logs (source, keyword, count, status) VALUES (?, ?, ?, ?)",
                (source, keyword, count, status)
            )
            conn.commit()

    def log_publication(self, content_id: str, platform: str, status: str, message: str = ''):
        """记录发布日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO publications (content_id, platform, status, message) VALUES (?, ?, ?, ?)",
                (content_id, platform, status, message)
            )
            conn.commit()

    def get_today_publication_count(self) -> int:
        """获取今日发布数量"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM publications WHERE DATE(published_at) = DATE('now') AND status = 'success'"
            )
            return cursor.fetchone()[0]
