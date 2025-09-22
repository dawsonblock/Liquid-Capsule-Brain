"""Advanced debugging system with interactive debugging capabilities."""

import asyncio
import functools
import logging
import pdb
import sys
import traceback
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime

log = logging.getLogger(__name__)


class Debugger:
    """Advanced debugging system with interactive debugging capabilities."""
    
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.breakpoints: Dict[str, List[int]] = {}
        self.watch_expressions: List[str] = []
        self.debug_log: List[Dict[str, Any]] = []
        self.max_log_size = 1000
        
    def set_breakpoint(self, filename: str, line_number: int) -> None:
        """Set a breakpoint at a specific file and line."""
        if filename not in self.breakpoints:
            self.breakpoints[filename] = []
        if line_number not in self.breakpoints[filename]:
            self.breakpoints[filename].append(line_number)
            log.debug(f"Breakpoint set at {filename}:{line_number}")
    
    def remove_breakpoint(self, filename: str, line_number: int) -> None:
        """Remove a breakpoint at a specific file and line."""
        if filename in self.breakpoints and line_number in self.breakpoints[filename]:
            self.breakpoints[filename].remove(line_number)
            log.debug(f"Breakpoint removed at {filename}:{line_number}")
    
    def add_watch_expression(self, expression: str) -> None:
        """Add a watch expression to monitor during debugging."""
        if expression not in self.watch_expressions:
            self.watch_expressions.append(expression)
            log.debug(f"Watch expression added: {expression}")
    
    def log_debug_event(self, event_type: str, message: str, 
                       context: Optional[Dict[str, Any]] = None) -> None:
        """Log a debug event with context."""
        if not self.enabled:
            return
            
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "message": message,
            "context": context or {},
            "traceback": traceback.format_stack()[-3:-1]  # Skip current and caller
        }
        
        self.debug_log.append(event)
        
        # Keep log size manageable
        if len(self.debug_log) > self.max_log_size:
            self.debug_log = self.debug_log[-self.max_log_size:]
        
        log.debug(f"Debug event: {event_type} - {message}")
    
    def get_debug_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent debug log entries."""
        return self.debug_log[-limit:]
    
    def clear_debug_log(self) -> None:
        """Clear the debug log."""
        self.debug_log.clear()
        log.debug("Debug log cleared")
    
    @asynccontextmanager
    async def debug_context(self, context_name: str, 
                          context_data: Optional[Dict[str, Any]] = None):
        """Context manager for debugging specific code sections."""
        start_time = datetime.now()
        self.log_debug_event("context_start", f"Entering {context_name}", context_data)
        
        try:
            yield
        except Exception as e:
            self.log_debug_event("context_error", f"Error in {context_name}: {str(e)}", {
                "error": str(e),
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
            raise
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            self.log_debug_event("context_end", f"Exiting {context_name}", {
                "duration_seconds": duration
            })
    
    def interactive_debug(self, frame=None) -> None:
        """Start interactive debugging session."""
        if not self.enabled:
            return
            
        if frame is None:
            frame = sys._getframe(1)
        
        self.log_debug_event("interactive_debug", "Starting interactive debug session")
        
        # Set up debugger with current frame
        debugger = pdb.Pdb()
        debugger.set_trace(frame)
    
    def check_breakpoint(self, filename: str, line_number: int) -> bool:
        """Check if there's a breakpoint at the given location."""
        return (self.enabled and 
                filename in self.breakpoints and 
                line_number in self.breakpoints[filename])
    
    def evaluate_watch_expressions(self, frame) -> Dict[str, Any]:
        """Evaluate all watch expressions in the given frame."""
        if not self.enabled or not self.watch_expressions:
            return {}
        
        results = {}
        for expression in self.watch_expressions:
            try:
                results[expression] = eval(expression, frame.f_globals, frame.f_locals)
            except Exception as e:
                results[expression] = f"Error: {str(e)}"
        
        return results
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state for debugging."""
        return {
            "enabled": self.enabled,
            "breakpoints": self.breakpoints,
            "watch_expressions": self.watch_expressions,
            "log_size": len(self.debug_log),
            "recent_events": self.get_debug_log(10)
        }
    
    def enable(self) -> None:
        """Enable debugging."""
        self.enabled = True
        log.info("Debugging enabled")
    
    def disable(self) -> None:
        """Disable debugging."""
        self.enabled = False
        log.info("Debugging disabled")


# Global debugger instance
debugger = Debugger(enabled=False)


def debug_breakpoint(filename: str, line_number: int) -> None:
    """Decorator to add breakpoint checking to functions."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if debugger.check_breakpoint(filename, line_number):
                debugger.interactive_debug()
            return func(*args, **kwargs)
        return wrapper
    return decorator


def debug_log(event_type: str, message: str, context: Optional[Dict[str, Any]] = None):
    """Convenience function to log debug events."""
    debugger.log_debug_event(event_type, message, context)
