"""
Redis caching service for search results and indexing operations
Implements LRU caching with configurable TTL per cache type
"""

import json
import hashlib
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.config import get_settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages Redis caching with fallback to in-memory cache
    Supports different TTLs for different cache types
    """
    
    _instance = None
    _redis_client = None
    _in_memory_cache = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if getattr(self, '_initialized', False):
            return
        
        self.settings = get_settings()
        self._initialized = True
        self.cache_enabled = self.settings.CACHE_ENABLED
        self.use_redis = False
        
        if self.cache_enabled and REDIS_AVAILABLE:
            try:
                self._redis_client = redis.Redis(
                    host=self.settings.REDIS_HOST,
                    port=self.settings.REDIS_PORT,
                    db=self.settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )
                self._redis_client.ping()
                self.use_redis = True
                logger.info(f"✅ Redis cache enabled ({self.settings.REDIS_HOST}:{self.settings.REDIS_PORT})")
            except Exception as e:
                logger.warning(f"⚠️  Redis connection failed: {e}. Using in-memory cache.")
                self._redis_client = None
                self.use_redis = False
        elif self.cache_enabled:
            logger.info("✅ In-memory cache enabled (Redis not available)")
    
    def get_ttl(self, cache_type: str) -> int:
        """Get TTL in seconds for cache type"""
        ttls = {
            'search': self.settings.CACHE_TTL_SEARCH,
            'index': self.settings.CACHE_TTL_INDEX,
            'general': self.settings.CACHE_TTL_GENERAL,
        }
        return ttls.get(cache_type, self.settings.CACHE_TTL_GENERAL)
    
    def _generate_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate cache key from prefix and data"""
        key_data = json.dumps(data, sort_keys=True, default=str)
        hash_suffix = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"{prefix}:{hash_suffix}"
    
    def get(self, prefix: str, data: Dict[str, Any]) -> Optional[Any]:
        """Get value from cache"""
        if not self.cache_enabled:
            return None
        
        key = self._generate_key(prefix, data)
        
        try:
            if self.use_redis:
                value = self._redis_client.get(key)
                if value:
                    logger.debug(f"Cache HIT (Redis): {key}")
                    return json.loads(value)
            else:
                if key in self._in_memory_cache:
                    entry = self._in_memory_cache[key]
                    if entry['expires_at'] > datetime.utcnow():
                        logger.debug(f"Cache HIT (Memory): {key}")
                        return entry['value']
                    else:
                        del self._in_memory_cache[key]
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")
        
        logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, prefix: str, data: Dict[str, Any], value: Any, cache_type: str = 'general') -> bool:
        """Set value in cache"""
        if not self.cache_enabled:
            return False
        
        key = self._generate_key(prefix, data)
        ttl = self.get_ttl(cache_type)
        
        try:
            if self.use_redis:
                self._redis_client.setex(key, ttl, json.dumps(value, default=str))
                logger.debug(f"Cache SET (Redis): {key} (TTL: {ttl}s)")
                return True
            else:
                self._in_memory_cache[key] = {
                    'value': value,
                    'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
                }
                logger.debug(f"Cache SET (Memory): {key} (TTL: {ttl}s)")
                return True
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")
            return False
    
    def delete(self, prefix: str, data: Dict[str, Any] = None) -> bool:
        """Delete cache entry"""
        if not self.cache_enabled:
            return False
        
        try:
            if data:
                key = self._generate_key(prefix, data)
                if self.use_redis:
                    self._redis_client.delete(key)
                    logger.debug(f"Cache DELETE (Redis): {key}")
                else:
                    if key in self._in_memory_cache:
                        del self._in_memory_cache[key]
                        logger.debug(f"Cache DELETE (Memory): {key}")
            else:
                if self.use_redis:
                    keys = self._redis_client.keys(f"{prefix}:*")
                    if keys:
                        self._redis_client.delete(*keys)
                        logger.debug(f"Cache DELETE (Redis): {len(keys)} keys")
                else:
                    keys_to_delete = [k for k in self._in_memory_cache.keys() if k.startswith(f"{prefix}:")]
                    for k in keys_to_delete:
                        del self._in_memory_cache[k]
                    logger.debug(f"Cache DELETE (Memory): {len(keys_to_delete)} keys")
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache"""
        if not self.cache_enabled:
            return False
        
        try:
            if self.use_redis:
                self._redis_client.flushdb()
                logger.info("Cache cleared (Redis)")
            else:
                self._in_memory_cache.clear()
                logger.info("Cache cleared (Memory)")
            return True
        except Exception as e:
            logger.warning(f"Cache CLEAR error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if self.use_redis:
                info = self._redis_client.info()
                return {
                    'backend': 'redis',
                    'enabled': self.cache_enabled,
                    'memory_usage': info.get('used_memory_human', 'N/A'),
                    'total_keys': self._redis_client.dbsize(),
                }
            else:
                return {
                    'backend': 'memory',
                    'enabled': self.cache_enabled,
                    'memory_usage': f"{len(self._in_memory_cache)} entries",
                    'total_keys': len(self._in_memory_cache),
                }
        except Exception as e:
            return {'backend': 'unknown', 'enabled': self.cache_enabled, 'error': str(e)}


cache_manager = CacheManager()


class SearchCache:
    """Helper class for search result caching"""
    
    PREFIX = "search"
    CACHE_TYPE = "search"
    
    @staticmethod
    def get(query: str, top_k: int = 5, repo_id: Optional[str] = None) -> Optional[Dict]:
        data = {"query": query, "top_k": top_k, "repo_id": repo_id}
        return cache_manager.get(SearchCache.PREFIX, data)
    
    @staticmethod
    def set(query: str, top_k: int, repo_id: Optional[str], results: Dict) -> bool:
        data = {"query": query, "top_k": top_k, "repo_id": repo_id}
        return cache_manager.set(SearchCache.PREFIX, data, results, SearchCache.CACHE_TYPE)
    
    @staticmethod
    def invalidate(repo_id: Optional[str] = None) -> bool:
        if repo_id:
            return True
        else:
            return cache_manager.delete(SearchCache.PREFIX)


class IndexCache:
    """Helper class for index operation caching"""
    
    PREFIX = "index"
    CACHE_TYPE = "index"
    
    @staticmethod
    def get(repo_url: str) -> Optional[Dict]:
        data = {"repo_url": repo_url}
        return cache_manager.get(IndexCache.PREFIX, data)
    
    @staticmethod
    def set(repo_url: str, status: Dict) -> bool:
        data = {"repo_url": repo_url}
        return cache_manager.set(IndexCache.PREFIX, data, status, IndexCache.CACHE_TYPE)
    
    @staticmethod
    def invalidate(repo_url: Optional[str] = None) -> bool:
        if repo_url:
            data = {"repo_url": repo_url}
            return cache_manager.delete(IndexCache.PREFIX, data)
        else:
            return cache_manager.delete(IndexCache.PREFIX)
