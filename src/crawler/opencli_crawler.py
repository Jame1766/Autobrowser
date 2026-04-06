"""
OpenCLI 爬取模块
支持 Twitter/X 和 Reddit
"""
import subprocess
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class OpenCLICrawler:
    """OpenCLI 爬取器"""

    def __init__(self):
        self.sources = {
            'twitter': self._crawl_twitter,
            'reddit': self._crawl_reddit
        }

    def crawl(self, source: str, keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        爬取指定来源的内容

        Args:
            source: 来源 (twitter/reddit)
            keyword: 搜索关键词
            limit: 数量限制

        Returns:
            内容列表
        """
        if source not in self.sources:
            raise ValueError(f"不支持的数据源: {source}")

        return self.sources[source](keyword, limit)

    def _run_opencli(self, cmd: List[str]) -> List[Dict]:
        """执行 opencli 命令"""
        try:
            # OpenCLI 格式: opencli twitter search "keyword" --limit 10
            # 需要将 keyword 作为独立参数传递
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"OpenCLI 错误: {result.stderr}")
                return []
        except Exception as e:
            logger.error(f"执行 OpenCLI 失败: {e}")
            return []

    def _crawl_twitter(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """爬取 Twitter/X - 格式: opencli twitter search "keyword" --limit 10"""
        # OpenCLI 格式: opencli twitter search "keyword" --limit 10
        cmd = [
            'opencli', 'twitter', 'search', keyword,
            '--limit', str(limit),
            '--format', 'json'
        ]

        raw_data = self._run_opencli(cmd)

        # 标准化数据格式
        results = []
        for item in raw_data:
            results.append({
                'id': item.get('id', ''),
                'platform': 'twitter',
                'title': item.get('text', '')[:100],
                'content': item.get('text', ''),
                'url': f"https://twitter.com/i/web/status/{item.get('id', '')}",
                'author': item.get('username', ''),
                'created_at': item.get('created_at', ''),
                'engagement': {
                    'likes': item.get('likes', 0),
                    'retweets': item.get('retweets', 0),
                    'replies': item.get('replies', 0)
                },
                'raw_data': item
            })

        logger.info(f"Twitter 爬取完成: {len(results)} 条")
        return results

    def _crawl_reddit(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        """爬取 Reddit - 格式: opencli reddit search "keyword" --limit 10"""
        cmd = [
            'opencli', 'reddit', 'search', keyword,
            '--limit', str(limit),
            '--format', 'json'
        ]

        raw_data = self._run_opencli(cmd)

        # 标准化数据格式
        results = []
        for item in raw_data:
            results.append({
                'id': item.get('id', ''),
                'platform': 'reddit',
                'title': item.get('title', ''),
                'content': item.get('selftext', item.get('title', '')),
                'url': item.get('url', ''),
                'author': item.get('author', ''),
                'created_at': item.get('created_utc', ''),
                'engagement': {
                    'upvotes': item.get('ups', 0),
                    'comments': item.get('num_comments', 0)
                },
                'subreddit': item.get('subreddit', ''),
                'raw_data': item
            })

        logger.info(f"Reddit 爬取完成: {len(results)} 条")
        return results

class ContentCrawler:
    """内容爬取管理器"""

    def __init__(self, config):
        self.config = config
        self.opencli = OpenCLICrawler()

    def crawl_all(self) -> List[Dict[str, Any]]:
        """
        爬取所有配置的来源

        Returns:
            合并后的内容列表
        """
        all_content = []
        keywords = self.config.get('crawler.keywords', ['AI'])
        sources = self.config.get('crawler.sources', ['twitter', 'reddit'])
        limit = self.config.get('crawler.limit', 10)

        for source in sources:
            for keyword in keywords:
                try:
                    content = self.opencli.crawl(source, keyword, limit // len(keywords))
                    all_content.extend(content)
                except Exception as e:
                    logger.error(f"爬取 {source} 关键词 {keyword} 失败: {e}")

        logger.info(f"总共爬取 {len(all_content)} 条内容")
        return all_content
