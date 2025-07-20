"""Window caching for faster lookups"""

import time
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class WindowCache:
    """Cache window information to avoid repeated lookups"""
    
    def __init__(self, ttl: float = 60.0):
        self.ttl = ttl  # Time to live in seconds
        self.cache = {}  # {user_session: {title_pattern: (window_data, timestamp)}}
        self.hwnd_cache = {}  # {hwnd: (window_data, timestamp)}
        
    def set_windows(self, user_session: str, windows: List[Dict[str, Any]]):
        """Cache all windows for a user session"""
        timestamp = time.time()
        
        if user_session not in self.cache:
            self.cache[user_session] = {}
            
        # Clear old cache for this session
        self.cache[user_session].clear()
        
        # Cache each window by partial title
        for window in windows:
            title = window.get('title', '')
            hwnd = window.get('hwnd')
            
            # Cache by full title
            self.cache[user_session][title.lower()] = (window, timestamp)
            
            # Also cache by hwnd
            if hwnd:
                self.hwnd_cache[hwnd] = (window, timestamp)
                
            # Cache by common patterns
            if 'cursor' in title.lower():
                self.cache[user_session]['cursor'] = (window, timestamp)
            elif 'vscode' in title.lower() or 'visual studio code' in title.lower():
                self.cache[user_session]['vscode'] = (window, timestamp)
            elif 'chrome' in title.lower():
                self.cache[user_session]['chrome'] = (window, timestamp)
                
        logger.info(f"Cached {len(windows)} windows for {user_session}")
        
    def find_window(self, user_session: str, title_pattern: str) -> Optional[Dict[str, Any]]:
        """Find window by title pattern"""
        if user_session not in self.cache:
            return None
            
        current_time = time.time()
        pattern_lower = title_pattern.lower()
        
        # Direct lookup first
        if pattern_lower in self.cache[user_session]:
            window, timestamp = self.cache[user_session][pattern_lower]
            if current_time - timestamp < self.ttl:
                logger.debug(f"Cache hit for pattern: {title_pattern}")
                return window
                
        # Pattern matching
        for cached_title, (window, timestamp) in self.cache[user_session].items():
            if current_time - timestamp < self.ttl:
                if pattern_lower in cached_title:
                    logger.debug(f"Cache hit (pattern match) for: {title_pattern}")
                    return window
                    
        logger.debug(f"Cache miss for pattern: {title_pattern}")
        return None
        
    def get_window_by_hwnd(self, hwnd: int) -> Optional[Dict[str, Any]]:
        """Get window by hwnd"""
        if hwnd in self.hwnd_cache:
            window, timestamp = self.hwnd_cache[hwnd]
            if time.time() - timestamp < self.ttl:
                return window
        return None
        
    def invalidate(self, user_session: str = None):
        """Invalidate cache"""
        if user_session:
            self.cache.pop(user_session, None)
            logger.info(f"Invalidated cache for {user_session}")
        else:
            self.cache.clear()
            self.hwnd_cache.clear()
            logger.info("Invalidated all cache")
            
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_windows = sum(len(session_cache) for session_cache in self.cache.values())
        return {
            'sessions': len(self.cache),
            'total_windows': total_windows,
            'hwnd_entries': len(self.hwnd_cache),
            'ttl': self.ttl
        }