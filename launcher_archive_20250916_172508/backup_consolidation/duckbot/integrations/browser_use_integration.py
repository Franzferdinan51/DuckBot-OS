#!/usr/bin/env python3
"""
Browser-Use Integration for DuckBot
Integrates browser-use/browser-use for web automation and browsing capabilities
"""

import os
import json
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    from browser_use import BrowserUse
    from browser_use.browser import Browser
    from browser_use.controller import Controller
    from browser_use.agent import Agent
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    logger.warning("Browser-Use not available - install with: pip install browser-use")
    BrowserUse = None
    Browser = None
    Controller = None
    Agent = None

@dataclass
class BrowserUseConfig:
    """Configuration for Browser-Use integration"""
    headless: bool = False
    browser_type: str = "chrome"  # chrome, firefox, edge
    timeout: int = 30
    user_data_dir: Optional[str] = None
    extensions: List[str] = None
    proxy: Optional[str] = None
    window_size: tuple = (1920, 1080)
    disable_images: bool = False
    disable_javascript: bool = False

class BrowserUseIntegration:
    """DuckBot integration for browser-use/browser-use"""

    def __init__(self, config: Optional[BrowserUseConfig] = None):
        self.config = config or BrowserUseConfig()
        self.available = BROWSER_USE_AVAILABLE
        self.browser = None
        self.controller = None
        self.agent = None
        
        if self.available:
            self._initialize_browser_use()
        else:
            logger.warning("Browser-Use integration not available")

    def _initialize_browser_use(self):
        """Initialize Browser-Use components"""
        try:
            # Initialize browser with configuration
            browser_options = {
                "headless": self.config.headless,
                "browser_type": self.config.browser_type,
                "timeout": self.config.timeout,
                "window_size": self.config.window_size,
                "disable_images": self.config.disable_images,
                "disable_javascript": self.config.disable_javascript
            }
            
            if self.config.user_data_dir:
                browser_options["user_data_dir"] = self.config.user_data_dir
                
            if self.config.proxy:
                browser_options["proxy"] = self.config.proxy
                
            self.browser = Browser(**browser_options)
            self.controller = Controller(browser=self.browser)
            self.agent = Agent(controller=self.controller)
            
            logger.info("Browser-Use integration initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Browser-Use: {e}")
            self.available = False

    async def navigate_to_url(self, url: str) -> Dict[str, Any]:
        """Navigate to a specific URL"""
        if not self.available or not self.browser:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            await self.browser.go_to_url(url)
            return {"success": True, "url": url, "message": f"Navigated to {url}"}
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return {"success": False, "error": str(e)}

    async def search_web(self, query: str, search_engine: str = "google") -> Dict[str, Any]:
        """Perform web search using specified search engine"""
        if not self.available or not self.browser:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            # Construct search URL based on engine
            search_urls = {
                "google": f"https://www.google.com/search?q={query}",
                "bing": f"https://www.bing.com/search?q={query}",
                "duckduckgo": f"https://duckduckgo.com/?q={query}"
            }
            
            search_url = search_urls.get(search_engine, search_urls["google"])
            await self.browser.go_to_url(search_url)
            
            return {"success": True, "query": query, "search_engine": search_engine, "url": search_url}
        except Exception as e:
            logger.error(f"Failed to search web for '{query}': {e}")
            return {"success": False, "error": str(e)}

    async def extract_text_content(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Extract text content from current page or specific element"""
        if not self.available or not self.browser:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            if selector:
                # Extract text from specific element
                element = await self.browser.get_element(selector)
                if element:
                    text = await element.get_text()
                    return {"success": True, "text": text, "selector": selector}
                else:
                    return {"success": False, "error": f"Element not found: {selector}"}
            else:
                # Extract all text content from page
                text = await self.browser.get_text()
                return {"success": True, "text": text, "full_page": True}
        except Exception as e:
            logger.error(f"Failed to extract text content: {e}")
            return {"success": False, "error": str(e)}

    async def take_screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Take screenshot of current page"""
        if not self.available or not self.browser:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            if filename:
                screenshot_path = Path(filename)
            else:
                # Generate unique filename
                timestamp = int(asyncio.get_event_loop().time())
                screenshot_path = Path.cwd() / "screenshots" / f"screenshot_{timestamp}.png"
                
            # Ensure directory exists
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Take screenshot
            await self.browser.take_screenshot(str(screenshot_path))
            
            return {"success": True, "path": str(screenshot_path), "filename": screenshot_path.name}
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return {"success": False, "error": str(e)}

    async def click_element(self, selector: str) -> Dict[str, Any]:
        """Click on element identified by selector"""
        if not self.available or not self.controller:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            await self.controller.click(selector)
            return {"success": True, "selector": selector, "action": "click"}
        except Exception as e:
            logger.error(f"Failed to click element '{selector}': {e}")
            return {"success": False, "error": str(e)}

    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Type text into element identified by selector"""
        if not self.available or not self.controller:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            await self.controller.type_text(selector, text)
            return {"success": True, "selector": selector, "text": text, "action": "type"}
        except Exception as e:
            logger.error(f"Failed to type text into '{selector}': {e}")
            return {"success": False, "error": str(e)}

    async def execute_agent_task(self, task: str) -> Dict[str, Any]:
        """Execute task using Browser-Use agent"""
        if not self.available or not self.agent:
            return {"success": False, "error": "Browser-Use agent not available"}
            
        try:
            result = await self.agent.run(task)
            return {"success": True, "result": result, "task": task}
        except Exception as e:
            logger.error(f"Agent task execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def close_browser(self) -> Dict[str, Any]:
        """Close browser and cleanup resources"""
        if not self.available or not self.browser:
            return {"success": False, "error": "Browser-Use not available"}
            
        try:
            await self.browser.close()
            return {"success": True, "message": "Browser closed successfully"}
        except Exception as e:
            logger.error(f"Failed to close browser: {e}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get integration status"""
        return {
            "available": self.available,
            "browser_open": self.browser is not None,
            "controller_active": self.controller is not None,
            "agent_ready": self.agent is not None,
            "config": {
                "headless": self.config.headless,
                "browser_type": self.config.browser_type,
                "timeout": self.config.timeout
            }
        }

# Global instance
browser_use_integration = BrowserUseIntegration()

async def initialize_browser_use() -> bool:
    """Initialize Browser-Use integration"""
    if not BROWSER_USE_AVAILABLE:
        logger.warning("Browser-Use not installed - install with: pip install browser-use")
        return False
        
    try:
        global browser_use_integration
        browser_use_integration = BrowserUseIntegration()
        return browser_use_integration.available
    except Exception as e:
        logger.error(f"Failed to initialize Browser-Use: {e}")
        return False

async def navigate_to_url(url: str) -> Dict[str, Any]:
    """Navigate to URL using Browser-Use"""
    return await browser_use_integration.navigate_to_url(url)

async def search_web(query: str, search_engine: str = "google") -> Dict[str, Any]:
    """Search web using Browser-Use"""
    return await browser_use_integration.search_web(query, search_engine)

async def extract_text_content(selector: Optional[str] = None) -> Dict[str, Any]:
    """Extract text content using Browser-Use"""
    return await browser_use_integration.extract_text_content(selector)

async def take_screenshot(filename: Optional[str] = None) -> Dict[str, Any]:
    """Take screenshot using Browser-Use"""
    return await browser_use_integration.take_screenshot(filename)

async def click_element(selector: str) -> Dict[str, Any]:
    """Click element using Browser-Use"""
    return await browser_use_integration.click_element(selector)

async def type_text(selector: str, text: str) -> Dict[str, Any]:
    """Type text using Browser-Use"""
    return await browser_use_integration.type_text(selector, text)

async def execute_agent_task(task: str) -> Dict[str, Any]:
    """Execute agent task using Browser-Use"""
    return await browser_use_integration.execute_agent_task(task)

async def close_browser() -> Dict[str, Any]:
    """Close browser using Browser-Use"""
    return await browser_use_integration.close_browser()

def get_browser_use_status() -> Dict[str, Any]:
    """Get Browser-Use status"""
    return browser_use_integration.get_status()

def is_browser_use_available() -> bool:
    """Check if Browser-Use is available"""
    return browser_use_integration.available