#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DuckBot Window Management System Test Suite

Comprehensive testing for all window operations including:
- Basic window operations (create, focus, minimize, maximize, resize, close)
- Enhanced multi-directional resizing
- Window positioning and z-index management
- State persistence and cleanup
- Race conditions and performance testing
- Screen bounds handling and resolution support
- Memory management under heavy load
"""

import asyncio
import json
import logging
import os
import sys
import time
import threading
import multiprocessing
import tracemalloc
import psutil
import platform
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import unittest.mock as mock

# Add DuckBot to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from duckbot.integrations.bytebot_integration import ByteBotIntegration, TaskResult
    from duckbot.desktop_launcher import DesktopLauncher
    BYTEBOT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: DuckBot integrations not available: {e}")
    BYTEBOT_AVAILABLE = False

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    success: bool
    execution_time: float
    memory_usage: float
    cpu_usage: float
    error_message: Optional[str] = None
    artifacts: Optional[Dict] = None

@dataclass
class WindowState:
    """Window state representation"""
    id: str
    title: str
    x: int
    y: int
    width: int
    height: int
    z_index: int
    minimized: bool
    maximized: bool
    focused: bool

class WindowManagerTestSuite:
    """Comprehensive window management test suite"""

    def __init__(self):
        self.test_results = []
        self.bytebot = ByteBotIntegration() if BYTEBOT_AVAILABLE else None
        self.windows = {}
        self.next_z_index = 1000
        self.screen_width = 1920
        self.screen_height = 1080
        self.test_log = []
        self.memory_snapshots = []

        # Performance tracking
        self.start_time = time.time()
        self.operations_count = 0

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('window_management_tests.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def start_memory_tracking(self):
        """Start memory tracking"""
        tracemalloc.start()
        self.initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

    def take_memory_snapshot(self, snapshot_name: str):
        """Take memory snapshot for analysis"""
        current, peak = tracemalloc.get_traced_memory()
        process = psutil.Process()
        memory_info = process.memory_info()

        snapshot = {
            'name': snapshot_name,
            'timestamp': time.time(),
            'current_memory': current / 1024 / 1024,  # MB
            'peak_memory': peak / 1024 / 1024,  # MB
            'rss_memory': memory_info.rss / 1024 / 1024,  # MB
            'vms_memory': memory_info.vms / 1024 / 1024,  # MB
            'cpu_percent': process.cpu_percent(),
            'thread_count': process.num_threads(),
            'handle_count': process.num_handles() if hasattr(process, 'num_handles') else 0
        }
        self.memory_snapshots.append(snapshot)
        return snapshot

    def create_window(self, app_id: str, title: str, width: int = 900, height: int = 600) -> WindowState:
        """Create a new window"""
        window_id = f"{app_id}_{int(time.time() * 1000)}"

        # Generate random position within screen bounds
        max_x = max(0, self.screen_width - width)
        max_y = max(0, self.screen_height - height - 60)  # Account for taskbar
        x = random.randint(100, max_x)
        y = random.randint(80, max_y)

        window = WindowState(
            id=window_id,
            title=title,
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=self.next_z_index,
            minimized=False,
            maximized=False,
            focused=True
        )

        self.windows[window_id] = window
        self.next_z_index += 1
        self.operations_count += 1

        self.logger.info(f"Created window: {title} at ({x}, {y}) size {width}x{height}")
        return window

    def focus_window(self, window_id: str) -> bool:
        """Focus a window and update z-index"""
        if window_id not in self.windows:
            return False

        # Update z-index
        self.windows[window_id].z_index = self.next_z_index
        self.windows[window_id].focused = True
        self.next_z_index += 1

        # Unfocus other windows
        for wid, window in self.windows.items():
            if wid != window_id:
                window.focused = False

        self.operations_count += 1
        self.logger.debug(f"Focused window: {self.windows[window_id].title}")
        return True

    def minimize_window(self, window_id: str) -> bool:
        """Minimize a window"""
        if window_id not in self.windows:
            return False

        window = self.windows[window_id]
        window.minimized = True
        window.focused = False
        self.operations_count += 1

        self.logger.debug(f"Minimized window: {window.title}")
        return True

    def maximize_window(self, window_id: str) -> bool:
        """Maximize a window"""
        if window_id not in self.windows:
            return False

        window = self.windows[window_id]

        if window.maximized:
            # Restore to original size
            window.maximized = False
        else:
            # Store original size and maximize
            window.maximized = True
            window.x = 0
            window.y = 0
            window.width = self.screen_width
            window.height = self.screen_height - 60  # Account for taskbar

        self.operations_count += 1
        self.logger.debug(f"Maximized/Restored window: {window.title}")
        return True

    def resize_window(self, window_id: str, delta_width: int, delta_height: int) -> bool:
        """Resize a window with bounds checking"""
        if window_id not in self.windows:
            return False

        window = self.windows[window_id]

        # Calculate new size with bounds checking
        new_width = max(400, min(self.screen_width, window.width + delta_width))
        new_height = max(300, min(self.screen_height - 60, window.height + delta_height))

        # Update position if resizing would go out of bounds
        if window.x + new_width > self.screen_width:
            window.x = max(0, self.screen_width - new_width)
        if window.y + new_height > self.screen_height - 60:
            window.y = max(0, self.screen_height - 60 - new_height)

        window.width = new_width
        window.height = new_height
        self.operations_count += 1

        self.logger.debug(f"Resized window: {window.title} to {new_width}x{new_height}")
        return True

    def move_window(self, window_id: str, delta_x: int, delta_y: int) -> bool:
        """Move a window with bounds checking"""
        if window_id not in self.windows:
            return False

        window = self.windows[window_id]

        # Calculate new position with bounds checking
        new_x = max(0, min(self.screen_width - window.width, window.x + delta_x))
        new_y = max(0, min(self.screen_height - 60 - window.height, window.y + delta_y))

        window.x = new_x
        window.y = new_y
        self.operations_count += 1

        self.logger.debug(f"Moved window: {window.title} to ({new_x}, {new_y})")
        return True

    def close_window(self, window_id: str) -> bool:
        """Close a window"""
        if window_id not in self.windows:
            return False

        window = self.windows.pop(window_id)
        self.operations_count += 1

        # If this was the focused window, focus the top remaining window
        if window.focused and self.windows:
            top_window = max(self.windows.values(), key=lambda w: w.z_index)
            self.focus_window(top_window.id)

        self.logger.debug(f"Closed window: {window.title}")
        return True

    def get_window_state(self, window_id: str) -> Optional[Dict]:
        """Get current window state"""
        if window_id not in self.windows:
            return None
        return asdict(self.windows[window_id])

    def get_all_windows(self) -> List[Dict]:
        """Get all windows sorted by z-index"""
        return [asdict(w) for w in sorted(self.windows.values(), key=lambda w: w.z_index)]

    # Test Cases

    async def test_basic_window_operations(self) -> TestResult:
        """Test basic window operations (create, focus, minimize, maximize, resize, close)"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            self.logger.info("Starting basic window operations test")

            # Test window creation
            window1 = self.create_window("test_app_1", "Test Window 1")
            window2 = self.create_window("test_app_2", "Test Window 2")
            window3 = self.create_window("test_app_3", "Test Window 3")

            assert len(self.windows) == 3, f"Expected 3 windows, got {len(self.windows)}"

            # Test focus operations
            assert self.focus_window(window1.id), "Failed to focus window 1"
            assert self.windows[window1.id].focused, "Window 1 should be focused"
            assert not self.windows[window2.id].focused, "Window 2 should not be focused"

            assert self.focus_window(window2.id), "Failed to focus window 2"
            assert self.windows[window2.id].focused, "Window 2 should be focused"
            assert not self.windows[window1.id].focused, "Window 1 should not be focused"

            # Test minimize operations
            assert self.minimize_window(window1.id), "Failed to minimize window 1"
            assert self.windows[window1.id].minimized, "Window 1 should be minimized"

            # Test maximize operations
            assert self.maximize_window(window2.id), "Failed to maximize window 2"
            assert self.windows[window2.id].maximized, "Window 2 should be maximized"
            assert self.windows[window2.id].width == self.screen_width, "Window 2 should have screen width"

            # Test restore
            assert self.maximize_window(window2.id), "Failed to restore window 2"
            assert not self.windows[window2.id].maximized, "Window 2 should be restored"

            # Test resize operations
            original_width = window3.width
            original_height = window3.height
            assert self.resize_window(window3.id, 100, 50), "Failed to resize window 3"
            assert self.windows[window3.id].width == original_width + 100, "Window width should increase by 100"
            assert self.windows[window3.id].height == original_height + 50, "Window height should increase by 50"

            # Test move operations
            original_x = window3.x
            original_y = window3.y
            assert self.move_window(window3.id, 50, -30), "Failed to move window 3"
            assert self.windows[window3.id].x == original_x + 50, "Window x position should increase by 50"
            assert self.windows[window3.id].y == original_y - 30, "Window y position should decrease by 30"

            # Test close operations
            assert self.close_window(window1.id), "Failed to close window 1"
            assert window1.id not in self.windows, "Window 1 should be removed"
            assert len(self.windows) == 2, f"Expected 2 windows, got {len(self.windows)}"

            assert self.close_window(window2.id), "Failed to close window 2"
            assert self.close_window(window3.id), "Failed to close window 3"
            assert len(self.windows) == 0, f"Expected 0 windows, got {len(self.windows)}"

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            return TestResult(
                test_name="basic_window_operations",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                artifacts={
                    "operations_performed": self.operations_count,
                    "windows_created": 3,
                    "total_operations": 12
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            self.logger.error(f"Basic window operations test failed: {e}")
            return TestResult(
                test_name="basic_window_operations",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_message=str(e)
            )

    async def test_enhanced_resizing(self) -> TestResult:
        """Test enhanced multi-directional resizing with edge cases"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            self.logger.info("Starting enhanced resizing test")

            # Create test window
            window = self.create_window("resize_test", "Resize Test Window", 500, 400)

            # Test multi-directional resizing from different corners
            resize_operations = [
                (100, 100),   # Bottom-right resize
                (-50, 75),    # Top-left resize (should adjust position)
                (200, -100),   # Bottom-left resize
                (-150, -200),  # Top-right resize (should adjust position)
                (0, 50),       # Only height change
                (75, 0),       # Only width change
                (-100, 0),     # Width reduction
                (0, -75),      # Height reduction
            ]

            original_x, original_y = window.x, window.y
            original_width, original_height = window.width, window.height

            for i, (delta_w, delta_h) in enumerate(resize_operations):
                self.resize_window(window.id, delta_w, delta_h)

                # Verify bounds checking
                current_window = self.windows[window.id]
                assert current_window.width >= 400, f"Window width too small: {current_window.width}"
                assert current_window.height >= 300, f"Window height too small: {current_window.height}"
                assert current_window.width <= self.screen_width, f"Window width too large: {current_window.width}"
                assert current_window.height <= self.screen_height - 60, f"Window height too large: {current_window.height}"

                # Verify position adjustment for negative deltas
                if delta_w < 0 and current_window.x > original_x:
                    assert current_window.x + current_window.width <= self.screen_width, "Window extends beyond screen width"
                if delta_h < 0 and current_window.y > original_y:
                    assert current_window.y + current_window.height <= self.screen_height - 60, "Window extends beyond screen height"

            # Test boundary conditions
            # Minimum size
            self.resize_window(window.id, -1000, -1000)  # Try to make very small
            current_window = self.windows[window.id]
            assert current_window.width == 400, f"Window should be minimum width: {current_window.width}"
            assert current_window.height == 300, f"Window should be minimum height: {current_window.height}"

            # Maximum size
            self.resize_window(window.id, 2000, 2000)  # Try to make very large
            current_window = self.windows[window.id]
            assert current_window.width == self.screen_width, f"Window should be screen width: {current_window.width}"
            assert current_window.height == self.screen_height - 60, f"Window should be screen height: {current_window.height}"

            # Test rapid resizing (potential race condition)
            rapid_resize_ops = [(50, 30), (-25, 15), (75, -20), (-40, 10), (30, 25)]
            original_state = self.get_window_state(window.id)

            for delta_w, delta_h in rapid_resize_ops:
                self.resize_window(window.id, delta_w, delta_h)

            final_state = self.get_window_state(window.id)
            assert final_state['width'] != original_state['width'], "Window size should have changed"
            assert final_state['height'] != original_state['height'], "Window size should have changed"

            # Cleanup
            self.close_window(window.id)

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            return TestResult(
                test_name="enhanced_resizing",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                artifacts={
                    "resize_operations": len(resize_operations) + len(rapid_resize_ops) + 2,
                    "boundary_tests": 2,
                    "rapid_operations": len(rapid_resize_ops)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            self.logger.error(f"Enhanced resizing test failed: {e}")
            return TestResult(
                test_name="enhanced_resizing",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_message=str(e)
            )

    async def test_z_index_management(self) -> TestResult:
        """Test z-index management and window ordering"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            self.logger.info("Starting z-index management test")

            # Create multiple windows
            windows = []
            for i in range(10):
                window = self.create_window(f"z_test_{i}", f"Z-Test Window {i}")
                windows.append(window)

            # Verify z-index assignment
            for i, window in enumerate(windows):
                assert window.z_index == 1000 + i, f"Window {i} has incorrect z-index: {window.z_index}"

            # Test focus brings to front
            middle_window = windows[5]  # Focus a middle window
            original_z_index = middle_window.z_index

            self.focus_window(middle_window.id)
            assert middle_window.z_index > original_z_index, "Focused window should have higher z-index"
            assert middle_window.z_index == self.next_z_index - 1, "Focused window should have highest z-index"

            # Test that other windows maintain relative order
            remaining_windows = [w for w in windows if w.id != middle_window.id]
            for i in range(len(remaining_windows) - 1):
                assert remaining_windows[i].z_index < remaining_windows[i + 1].z_index, "Windows should maintain relative order"

            # Test rapid focus changes (potential race condition)
            focus_order = [2, 7, 1, 8, 3, 9, 0, 6, 4]  # Random focus order

            for window_idx in focus_order:
                target_window = windows[window_idx]
                self.focus_window(target_window.id)
                assert target_window.z_index == self.next_z_index - 1, f"Window {window_idx} should have highest z-index"

            # Test window list ordering
            all_windows = self.get_all_windows()
            for i in range(len(all_windows) - 1):
                assert all_windows[i]['z_index'] < all_windows[i + 1]['z_index'], "Window list should be sorted by z-index"

            # Test window closing and z-index reassignment
            closed_window = windows[0]
            original_next_z = self.next_z_index

            self.close_window(closed_window.id)
            assert self.next_z_index == original_next_z, "Next z-index should not change on window close"

            # Focus remaining top window
            if self.windows:
                top_window = max(self.windows.values(), key=lambda w: w.z_index)
                self.focus_window(top_window.id)

            # Cleanup
            for window in windows[1:]:
                if window.id in self.windows:
                    self.close_window(window.id)

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            return TestResult(
                test_name="z_index_management",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                artifacts={
                    "windows_created": 10,
                    "focus_operations": len(focus_order) + 2,
                    "z_index_checks": len(windows) + len(focus_order) + 3
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            self.logger.error(f"Z-index management test failed: {e}")
            return TestResult(
                test_name="z_index_management",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_message=str(e)
            )

    async def test_race_conditions_and_cleanup(self) -> TestResult:
        """Test race conditions and proper cleanup during rapid operations"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            self.logger.info("Starting race conditions and cleanup test")

            # Create many windows for stress testing
            num_windows = 50
            windows = []
            for i in range(num_windows):
                window = self.create_window(f"race_test_{i}", f"Race Test Window {i}")
                windows.append(window)

            assert len(self.windows) == num_windows, f"Expected {num_windows} windows, got {len(self.windows)}"

            # Test concurrent operations using threading
            def concurrent_worker(worker_id: int, operations: List[Tuple[str, str]]):
                """Worker function for concurrent operations"""
                results = []
                for op_type, window_id in operations:
                    try:
                        if op_type == "focus":
                            self.focus_window(window_id)
                        elif op_type == "minimize":
                            self.minimize_window(window_id)
                        elif op_type == "maximize":
                            self.maximize_window(window_id)
                        elif op_type == "resize":
                            self.resize_window(window_id, 50, 30)
                        elif op_type == "move":
                            self.move_window(window_id, 10, -10)
                        results.append(True)
                    except Exception as e:
                        results.append(False)
                        self.logger.warning(f"Worker {worker_id} failed on {op_type}: {e}")
                return results

            # Generate random operations for each worker
            num_workers = 10
            operations_per_worker = 20
            all_operations = []

            for _ in range(num_workers * operations_per_worker):
                op_type = random.choice(["focus", "minimize", "maximize", "resize", "move"])
                window_id = random.choice([w.id for w in windows])
                all_operations.append((op_type, window_id))

            # Split operations among workers
            chunk_size = len(all_operations) // num_workers
            worker_operations = [all_operations[i:i + chunk_size] for i in range(0, len(all_operations), chunk_size)]

            # Execute concurrently
            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures = [executor.submit(concurrent_worker, i, ops) for i, ops in enumerate(worker_operations)]
                all_results = []

                for future in as_completed(futures):
                    try:
                        worker_results = future.result(timeout=10)
                        all_results.extend(worker_results)
                    except Exception as e:
                        self.logger.error(f"Worker thread failed: {e}")

            success_rate = sum(all_results) / len(all_results) if all_results else 0
            assert success_rate > 0.9, f"Concurrent operation success rate too low: {success_rate:.2f}"

            # Test rapid create/delete cycles
            create_delete_cycles = 20
            for i in range(create_delete_cycles):
                temp_window = self.create_window(f"temp_{i}", f"Temporary Window {i}")
                self.focus_window(temp_window.id)
                self.resize_window(temp_window.id, 100, 50)
                self.close_window(temp_window.id)

            assert len(self.windows) == num_windows, f"Window count should be {num_windows} after temp operations, got {len(self.windows)}"

            # Test cleanup of all windows
            window_count_before = len(self.windows)
            for window in windows[:]:  # Copy list to avoid modification during iteration
                self.close_window(window.id)

            assert len(self.windows) == 0, f"AllWindows should be closed, {len(self.windows)} remaining"

            # Verify z-index counter hasn't grown excessively
            z_index_growth = self.next_z_index - 1000
            expected_operations = num_windows + len(all_operations) + create_delete_cycles * 4
            assert z_index_growth <= expected_operations * 1.5, f"Z-index grew too much: {z_index_growth} vs expected {expected_operations}"

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            return TestResult(
                test_name="race_conditions_and_cleanup",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                artifacts={
                    "windows_created": num_windows + create_delete_cycles,
                    "concurrent_operations": len(all_operations),
                    "workers": num_workers,
                    "success_rate": success_rate,
                    "z_index_growth": z_index_growth,
                    "temp_cycles": create_delete_cycles
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            self.logger.error(f"Race conditions test failed: {e}")
            return TestResult(
                test_name="race_conditions_and_cleanup",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_message=str(e)
            )

    async def test_memory_management_performance(self) -> TestResult:
        """Test memory management and performance under heavy load"""
        start_time = time.time()

        try:
            self.logger.info("Starting memory management and performance test")
            self.start_memory_tracking()

            # Initial memory snapshot
            initial_snapshot = self.take_memory_snapshot("initial_state")

            # Test 1: Heavy window creation
            heavy_window_count = 1000
            self.logger.info(f"Creating {heavy_window_count} windows for memory stress test")

            create_start = time.time()
            heavy_windows = []
            for i in range(heavy_window_count):
                window = self.create_window(f"heavy_test_{i}", f"Heavy Load Window {i}")
                heavy_windows.append(window)

                # Periodic memory checks
                if i % 100 == 0:
                    snapshot = self.take_memory_snapshot(f"creation_batch_{i}")
                    self.logger.info(f"Created {i} windows, memory: {snapshot['rss_memory']:.2f}MB")

            create_time = time.time() - create_start
            creation_snapshot = self.take_memory_snapshot("after_creation")

            # Verify memory usage is reasonable
            memory_per_window = (creation_snapshot['rss_memory'] - initial_snapshot['rss_memory']) / heavy_window_count
            assert memory_per_window < 0.1, f"Memory per window too high: {memory_per_window:.3f}MB"

            # Test 2: Rapid operations on all windows
            self.logger.info("Performing rapid operations on all windows")

            rapid_start = time.time()
            operations_performed = 0

            # Focus all windows in sequence
            for window in heavy_windows:
                self.focus_window(window.id)
                operations_performed += 1

            # Minimize and restore all windows
            for window in heavy_windows:
                self.minimize_window(window.id)
                self.maximize_window(window.id)  # Should restore
                operations_performed += 2

            # Resize all windows
            for window in heavy_windows:
                self.resize_window(window.id, random.randint(-50, 100), random.randint(-50, 100))
                operations_performed += 1

            # Move all windows
            for window in heavy_windows:
                self.move_window(window.id, random.randint(-100, 100), random.randint(-100, 100))
                operations_performed += 1

            rapid_time = time.time() - rapid_start
            operations_per_second = operations_performed / rapid_time
            rapid_snapshot = self.take_memory_snapshot("after_rapid_operations")

            # Test 3: Performance benchmarks
            self.logger.info("Running performance benchmarks")

            # Small operations benchmark
            small_start = time.time()
            for _ in range(1000):
                temp_window = self.create_window("temp_bench", "Benchmark Window")
                self.focus_window(temp_window.id)
                self.close_window(temp_window.id)
            small_benchmark_time = time.time() - small_start

            # Large operations benchmark
            large_start = time.time()
            batch_windows = []
            for i in range(100):
                window = self.create_window(f"batch_{i}", f"Batch Window {i}")
                batch_windows.append(window)

            for window in batch_windows:
                self.focus_window(window.id)
                self.resize_window(window.id, 50, 30)

            for window in batch_windows:
                self.close_window(window.id)
            large_benchmark_time = time.time() - large_start

            benchmark_snapshot = self.take_memory_snapshot("after_benchmarks")

            # Test 4: Cleanup and memory recovery
            self.logger.info("Testing cleanup and memory recovery")

            cleanup_start = time.time()
            for window in heavy_windows:
                self.close_window(window.id)
            cleanup_time = time.time() - cleanup_start

            final_snapshot = self.take_memory_snapshot("after_cleanup")

            # Verify memory cleanup
            memory_leak = final_snapshot['rss_memory'] - initial_snapshot['rss_memory']
            assert memory_leak < 10, f"Memory leak detected: {memory_leak:.2f}MB"

            execution_time = time.time() - start_time

            return TestResult(
                test_name="memory_management_performance",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_leak,
                cpu_usage=psutil.Process().cpu_percent(),
                artifacts={
                    "heavy_windows_created": heavy_window_count,
                    "creation_time": create_time,
                    "operations_performed": operations_performed,
                    "operations_per_second": operations_per_second,
                    "small_benchmark_time": small_benchmark_time,
                    "large_benchmark_time": large_benchmark_time,
                    "cleanup_time": cleanup_time,
                    "memory_per_window": memory_per_window,
                    "memory_leak": memory_leak,
                    "memory_snapshots": len(self.memory_snapshots),
                    "total_operations": self.operations_count
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_before = getattr(self, 'initial_memory', memory_after)
            memory_usage = memory_after - memory_before

            self.logger.error(f"Memory management test failed: {e}")
            return TestResult(
                test_name="memory_management_performance",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=psutil.Process().cpu_percent(),
                error_message=str(e)
            )

    async def test_screen_bounds_resolutions(self) -> TestResult:
        """Test screen bounds handling and different screen resolutions"""
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024

        try:
            self.logger.info("Starting screen bounds and resolution test")

            # Test different screen resolutions
            test_resolutions = [
                (1920, 1080),  # Full HD
                (1366, 768),   # HD
                (1280, 720),   # HD 720p
                (2560, 1440),  # 2K
                (3840, 2160),  # 4K
                (800, 600),    # Small screen
                (1024, 768),   # Standard
            ]

            test_results = []

            for screen_width, screen_height in test_resolutions:
                self.logger.info(f"Testing resolution: {screen_width}x{screen_height}")

                # Temporarily change screen resolution for testing
                original_width, original_height = self.screen_width, self.screen_height
                self.screen_width = screen_width
                self.screen_height = screen_height

                # Test window creation at edges
                edge_windows = []

                # Corner windows
                corner_positions = [
                    (0, 0),  # Top-left
                    (screen_width - 400, 0),  # Top-right
                    (0, screen_height - 360),  # Bottom-left
                    (screen_width - 400, screen_height - 360),  # Bottom-right
                ]

                for x, y in corner_positions:
                    window = self.create_window(f"corner_{x}_{y}", f"Corner Window {x},{y}")
                    edge_windows.append(window)

                    # Verify window is within bounds
                    assert window.x >= 0, f"Window x position negative: {window.x}"
                    assert window.y >= 0, f"Window y position negative: {window.y}"
                    assert window.x + window.width <= screen_width, f"Window extends beyond right edge: {window.x + window.width} > {screen_width}"
                    assert window.y + window.height <= screen_height - 60, f"Window extends beyond bottom edge: {window.y + window.height} > {screen_height - 60}"

                # Test maximum size window
                max_window = self.create_window("max_size", "Maximum Size Window")
                self.resize_window(max_window.id, screen_width, screen_height)

                assert max_window.width <= screen_width, f"Max window too wide: {max_window.width} > {screen_width}"
                assert max_window.height <= screen_height - 60, f"Max window too tall: {max_window.height} > {screen_height - 60}"

                # Test window movement to boundaries
                test_window = self.create_window("boundary_test", "Boundary Test Window")

                # Test movement to all edges
                self.move_window(test_window.id, -screen_width, -screen_height)  # Try to move far off-screen
                assert test_window.x == 0, f"Window should be at left edge: {test_window.x}"
                assert test_window.y == 0, f"Window should be at top edge: {test_window.y}"

                self.move_window(test_window.id, screen_width * 2, screen_height * 2)  # Try to move far off-screen
                expected_x = max(0, screen_width - test_window.width)
                expected_y = max(0, screen_height - 60 - test_window.height)
                assert test_window.x == expected_x, f"Window should be at right edge: {test_window.x} != {expected_x}"
                assert test_window.y == expected_y, f"Window should be at bottom edge: {test_window.y} != {expected_y}"

                # Test maximized window
                self.maximize_window(test_window.id)
                assert test_window.x == 0, f"Maximized window x should be 0: {test_window.x}"
                assert test_window.y == 0, f"Maximized window y should be 0: {test_window.y}"
                assert test_window.width == screen_width, f"Maximized window width should match screen: {test_window.width} != {screen_width}"
                assert test_window.height == screen_height - 60, f"Maximized window height should account for taskbar: {test_window.height} != {screen_height - 60}"

                # Test very small screen handling
                if screen_width < 1000 or screen_height < 700:
                    small_window = self.create_window("small_screen", "Small Screen Test", 300, 200)
                    self.resize_window(small_window.id, 50, 30)  # Try to make very small
                    assert small_window.width >= 400, f"Window should enforce minimum width: {small_window.width}"
                    assert small_window.height >= 300, f"Window should enforce minimum height: {small_window.height}"

                # Cleanup
                for window in edge_windows + [max_window, test_window]:
                    if window.id in self.windows:
                        self.close_window(window.id)

                # Restore original resolution
                self.screen_width = original_width
                self.screen_height = original_height

                resolution_result = {
                    "resolution": f"{screen_width}x{screen_height}",
                    "windows_tested": len(edge_windows) + 2,
                    "boundary_tests": 4,
                    "max_size_test": 1,
                    "success": True
                }
                test_results.append(resolution_result)

            # Test dynamic resolution changes
            self.logger.info("Testing dynamic resolution changes")

            # Create windows at default resolution
            res_test_windows = []
            for i in range(5):
                window = self.create_window(f"res_test_{i}", f"Resolution Test Window {i}")
                res_test_windows.append(window)

            # Change resolution and verify window adaptation
            self.screen_width = 1280
            self.screen_height = 720

            for window in res_test_windows:
                # Verify windows are still within bounds
                assert window.x + window.width <= self.screen_width, f"Window extends beyond screen after resize: {window.x + window.width} > {self.screen_width}"
                assert window.y + window.height <= self.screen_height - 60, f"Window extends beyond screen after resize: {window.y + window.height} > {self.screen_height - 60}"

                # Test operations still work
                self.focus_window(window.id)
                self.resize_window(window.id, 50, 30)
                self.move_window(window.id, 20, 10)

            # Cleanup
            for window in res_test_windows:
                self.close_window(window.id)

            # Restore default resolution
            self.screen_width = 1920
            self.screen_height = 1080

            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            return TestResult(
                test_name="screen_bounds_resolutions",
                success=True,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                artifacts={
                    "resolutions_tested": len(test_resolutions),
                    "resolution_results": test_results,
                    "dynamic_res_test_windows": len(res_test_windows),
                    "boundary_positions_tested": len(test_resolutions) * 4,
                    "total_resolution_checks": sum(r['windows_tested'] for r in test_results)
                }
            )

        except Exception as e:
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            memory_usage = memory_after - memory_before
            cpu_usage = psutil.Process().cpu_percent()

            self.logger.error(f"Screen bounds test failed: {e}")
            return TestResult(
                test_name="screen_bounds_resolutions",
                success=False,
                execution_time=execution_time,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                error_message=str(e)
            )

    async def run_all_tests(self) -> List[TestResult]:
        """Run all window management tests"""
        self.logger.info("Starting comprehensive window management test suite")

        tests = [
            self.test_basic_window_operations,
            self.test_enhanced_resizing,
            self.test_z_index_management,
            self.test_race_conditions_and_cleanup,
            self.test_memory_management_performance,
            self.test_screen_bounds_resolutions
        ]

        results = []

        for test_func in tests:
            try:
                self.logger.info(f"Running test: {test_func.__name__}")
                result = await test_func()
                results.append(result)
                self.test_results.append(result)

                if result.success:
                    self.logger.info(f"✅ {test_func.__name__} passed in {result.execution_time:.3f}s")
                else:
                    self.logger.error(f"❌ {test_func.__name__} failed: {result.error_message}")

            except Exception as e:
                self.logger.error(f"💥 {test_func.__name__} crashed: {e}")
                error_result = TestResult(
                    test_name=test_func.__name__,
                    success=False,
                    execution_time=0,
                    memory_usage=0,
                    cpu_usage=0,
                    error_message=str(e)
                )
                results.append(error_result)
                self.test_results.append(error_result)

        return results

    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.success)
        failed_tests = total_tests - passed_tests

        total_execution_time = sum(r.execution_time for r in self.test_results)
        avg_memory_usage = sum(r.memory_usage for r in self.test_results) / total_tests if total_tests > 0 else 0
        avg_cpu_usage = sum(r.cpu_usage for r in self.test_results) / total_tests if total_tests > 0 else 0

        # Memory analysis
        memory_growth = 0
        if len(self.memory_snapshots) >= 2:
            initial_memory = self.memory_snapshots[0]['rss_memory']
            final_memory = self.memory_snapshots[-1]['rss_memory']
            memory_growth = final_memory - initial_memory

        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "total_execution_time": total_execution_time,
                "average_memory_usage": avg_memory_usage,
                "average_cpu_usage": avg_cpu_usage,
                "memory_growth": memory_growth,
                "total_operations_performed": self.operations_count
            },
            "test_results": [asdict(result) for result in self.test_results],
            "memory_snapshots": self.memory_snapshots,
            "system_info": {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "python_version": sys.version,
                "total_memory_gb": psutil.virtual_memory().total / (1024**3),
                "available_memory_gb": psutil.virtual_memory().available / (1024**3),
                "cpu_count": psutil.cpu_count(),
                "bytebot_available": BYTEBOT_AVAILABLE
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for failures
        failed_tests = [r for r in self.test_results if not r.success]
        if failed_tests:
            recommendations.append(f"🔧 Fix {len(failed_tests)} failing tests: {', '.join([r.test_name for r in failed_tests])}")

        # Check memory usage
        avg_memory = sum(r.memory_usage for r in self.test_results) / len(self.test_results) if self.test_results else 0
        if avg_memory > 50:
            recommendations.append("🧠 Optimize memory usage - average memory per test is high")

        # Check performance
        slow_tests = [r for r in self.test_results if r.execution_time > 10]
        if slow_tests:
            recommendations.append(f"⚡ Optimize performance for slow tests: {', '.join([r.test_name for r in slow_tests])}")

        # Check memory leaks
        if len(self.memory_snapshots) >= 2:
            memory_leak = self.memory_snapshots[-1]['rss_memory'] - self.memory_snapshots[0]['rss_memory']
            if memory_leak > 10:
                recommendations.append("🧹 Investigate memory leaks - significant memory growth detected")

        # General recommendations
        recommendations.extend([
            "📊 Implement continuous monitoring of window operations",
            "🔒 Add input validation for window coordinates and sizes",
            "🚀 Consider implementing window operation queuing for high-frequency operations",
            "📈 Add performance metrics collection for production monitoring",
            "🛡️ Implement rate limiting for rapid window operations"
        ])

        return recommendations

    def save_report(self, report: Dict[str, Any], filename: str = "window_management_test_report.json"):
        """Save test report to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"Test report saved to {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save report: {e}")

async def main():
    """Main test execution"""
    print("🚀 DuckBot Window Management System Test Suite")
    print("=" * 60)

    test_suite = WindowManagerTestSuite()

    try:
        # Run all tests
        results = await test_suite.run_all_tests()

        # Generate and save report
        report = test_suite.generate_test_report()
        test_suite.save_report(report)

        # Print summary
        print("\n📊 Test Results Summary:")
        print(f"Total Tests: {report['test_summary']['total_tests']}")
        print(f"Passed: {report['test_summary']['passed_tests']}")
        print(f"Failed: {report['test_summary']['failed_tests']}")
        print(f"Success Rate: {report['test_summary']['success_rate']:.1%}")
        print(f"Total Time: {report['test_summary']['total_execution_time']:.3f}s")
        print(f"Memory Growth: {report['test_summary']['memory_growth']:.2f}MB")
        print(f"Operations Performed: {report['test_summary']['total_operations_performed']}")

        if report['test_summary']['failed_tests'] > 0:
            print("\n❌ Failed Tests:")
            for result in results:
                if not result.success:
                    print(f"  - {result.test_name}: {result.error_message}")

        print("\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        print(f"\n📄 Full report saved to: window_management_test_report.json")

        # Return exit code
        return 0 if report['test_summary']['failed_tests'] == 0 else 1

    except Exception as e:
        print(f"💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)