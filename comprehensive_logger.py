#!/usr/bin/env python3
"""
AlleyBot Comprehensive Logging System
Logs ALL activities: coding, posting, platform interactions, API calls, errors, etc.
"""
import json
import os
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
from pathlib import Path

class ActivityType(Enum):
    """Types of activities to log"""
    CODING = "coding"
    PLATFORM_POST = "platform_post"
    PLATFORM_COMMENT = "platform_comment"
    PLATFORM_UPVOTE = "platform_upvote"
    API_CALL = "api_call"
    ERROR = "error"
    AUTONOMOUS_TASK = "autonomous_task"
    HUMAN_INTERACTION = "human_interaction"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    PERFORMANCE = "performance"

class LogLevel(Enum):
    """Log levels for filtering"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlleyBotLogger:
    """Comprehensive logging system for all AlleyBot activities"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = Path(logs_dir)
        self._lock = threading.Lock()
        self._setup_logs()
    
    def _setup_logs(self):
        """Setup log directory structure"""
        self.logs_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different log types
        subdirs = [
            "coding", "platforms", "api_calls", "errors", 
            "autonomous", "human", "system", "security", "performance"
        ]
        
        for subdir in subdirs:
            (self.logs_dir / subdir).mkdir(exist_ok=True)
        
        # Create daily log files
        self._create_daily_log_files()
    
    def _create_daily_log_files(self):
        """Create daily log files for each category"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        for category in ActivityType:
            log_dir = self.logs_dir / category.value
            log_dir.mkdir(parents=True, exist_ok=True)  # Create directory if it doesn't exist
            filepath = log_dir / f"alleybot_{today}.log"
            
            with open(filepath, 'w') as f:
                f.write(f"# AlleyBot {category.value.title()} Log - {today}\n")
                f.write(f"# Started at: {datetime.now().isoformat()}\n\n")
    
    def log_activity(self, 
                    activity_type: ActivityType,
                    action: str,
                    details: Dict[str, Any],
                    level: LogLevel = LogLevel.INFO,
                    platform: str = None,
                    user_id: str = None) -> str:
        """Log any activity with full context"""
        
        timestamp = datetime.now().isoformat()
        log_id = hashlib.md5(f"{timestamp}{action}{str(details)}".encode()).hexdigest()[:8]
        
        log_entry = {
            "log_id": log_id,
            "timestamp": timestamp,
            "activity_type": activity_type.value,
            "action": action,
            "level": level.value,
            "platform": platform,
            "user_id": user_id,
            "details": details,
            "thread_id": threading.current_thread().ident,
            "process_id": os.getpid()
        }
        
        # Write to appropriate log files
        self._write_to_logs(log_entry, activity_type)
        
        return log_id
    
    def _write_to_logs(self, log_entry: Dict, activity_type: ActivityType):
        """Write log entry to appropriate files"""
        with self._lock:
            date = datetime.now().strftime('%Y-%m-%d')
            
            # Main log file
            main_log = os.path.join(self.logs_dir, "main", f"alleybot_{date}.log")
            self._append_log(main_log, log_entry)
            
            # Category-specific log file
            category_map = {
                ActivityType.CODING: "coding",
                ActivityType.PLATFORM_POST: "platforms",
                ActivityType.PLATFORM_COMMENT: "platforms",
                ActivityType.PLATFORM_UPVOTE: "platforms",
                ActivityType.API_CALL: "api_calls",
                ActivityType.ERROR: "errors",
                ActivityType.AUTONOMOUS_TASK: "autonomous",
                ActivityType.HUMAN_INTERACTION: "human",
                ActivityType.SYSTEM_EVENT: "system",
                ActivityType.SECURITY_EVENT: "security",
                ActivityType.PERFORMANCE: "performance"
            }
            
            category = category_map.get(activity_type, "main")
            category_log = os.path.join(self.logs_dir, category, f"{category}_{date}.log")
            self._append_log(category_log, log_entry)
            
            # Error logs also go to main error file
            if activity_type == ActivityType.ERROR or log_entry["level"] in ["error", "critical"]:
                error_log = os.path.join(self.logs_dir, "errors", f"errors_{date}.log")
                self._append_log(error_log, log_entry)
    
    def _append_log(self, filepath: str, log_entry: Dict):
        """Append log entry to file"""
        try:
            with open(filepath, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            # Fallback logging
            print(f"Failed to write to log {filepath}: {e}")
    
    def log_platform_activity(self, 
                             platform: str,
                             action: str,  # post, comment, upvote, etc.
                             details: Dict,
                             success: bool = True,
                             error: str = None) -> str:
        """Log platform-specific activities"""
        
        activity_type = ActivityType.PLATFORM_POST
        if action == "comment":
            activity_type = ActivityType.PLATFORM_COMMENT
        elif action == "upvote":
            activity_type = ActivityType.PLATFORM_UPVOTE
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        log_details = {
            "platform": platform,
            "action": action,
            "success": success,
            **details
        }
        
        if error:
            log_details["error"] = error
        
        return self.log_activity(
            activity_type=activity_type,
            action=f"{platform}_{action}",
            details=log_details,
            level=level,
            platform=platform
        )
    
    def log_api_call(self, 
                     api_name: str,
                     endpoint: str,
                     method: str,
                     request_data: Dict = None,
                     response_data: Dict = None,
                     status_code: int = None,
                     response_time: float = None,
                     success: bool = True,
                     error: str = None) -> str:
        """Log API calls"""
        
        details = {
            "api_name": api_name,
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time": response_time,
            "success": success
        }
        
        if request_data:
            # Sanitize sensitive data
            details["request_data"] = self._sanitize_data(request_data)
        
        if response_data:
            details["response_data"] = self._sanitize_data(response_data)
        
        if error:
            details["error"] = error
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        return self.log_activity(
            activity_type=ActivityType.API_CALL,
            action=f"{api_name}_call",
            details=details,
            level=level
        )
    
    def log_autonomous_task(self,
                           task_name: str,
                           task_type: str,
                           details: Dict,
                           success: bool = True,
                           error: str = None,
                           execution_time: float = None) -> str:
        """Log autonomous task execution"""
        
        log_details = {
            "task_name": task_name,
            "task_type": task_type,
            "success": success,
            "execution_time": execution_time,
            **details
        }
        
        if error:
            log_details["error"] = error
        
        level = LogLevel.INFO if success else LogLevel.WARNING
        
        return self.log_activity(
            activity_type=ActivityType.AUTONOMOUS_TASK,
            action=f"autonomous_{task_name}",
            details=log_details,
            level=level
        )
    
    def log_coding_activity(self,
                           action: str,  # generate, test, approve, deploy
                           details: Dict,
                           success: bool = True,
                           error: str = None) -> str:
        """Log coding activities"""
        
        log_details = {
            "coding_action": action,
            "success": success,
            **details
        }
        
        if error:
            log_details["error"] = error
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        return self.log_activity(
            activity_type=ActivityType.CODING,
            action=f"coding_{action}",
            details=log_details,
            level=level
        )
    
    def log_human_interaction(self,
                             interaction_type: str,
                             details: Dict,
                             user_id: str = None) -> str:
        """Log human interactions"""
        
        return self.log_activity(
            activity_type=ActivityType.HUMAN_INTERACTION,
            action=f"human_{interaction_type}",
            details=details,
            user_id=user_id
        )
    
    def log_error(self,
                 error_type: str,
                 error_message: str,
                 context: Dict = None,
                 critical: bool = False) -> str:
        """Log errors"""
        
        details = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        level = LogLevel.CRITICAL if critical else LogLevel.ERROR
        
        return self.log_activity(
            activity_type=ActivityType.ERROR,
            action=f"error_{error_type}",
            details=details,
            level=level
        )
    
    def log_performance(self,
                       metric_name: str,
                       value: float,
                       unit: str,
                       context: Dict = None) -> str:
        """Log performance metrics"""
        
        details = {
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "context": context or {}
        }
        
        return self.log_activity(
            activity_type=ActivityType.PERFORMANCE,
            action=f"performance_{metric_name}",
            details=details,
            level=LogLevel.INFO
        )
    
    def _sanitize_data(self, data: Dict) -> Dict:
        """Remove sensitive data from logs"""
        sensitive_keys = [
            "api_key", "password", "token", "secret", "private_key",
            "api_key", "authorization", "auth", "credentials"
        ]
        
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) if isinstance(item, (dict, list)) else item for item in data]
        else:
            return data
    
    def get_logs(self,
                 activity_type: ActivityType = None,
                 date: str = None,
                 level: LogLevel = None,
                 platform: str = None,
                 limit: int = 100) -> List[Dict]:
        """Retrieve logs with filtering"""
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logs = []
        
        # Determine which log files to read
        if activity_type:
            category_map = {
                ActivityType.CODING: "coding",
                ActivityType.PLATFORM_POST: "platforms",
                ActivityType.PLATFORM_COMMENT: "platforms",
                ActivityType.PLATFORM_UPVOTE: "platforms",
                ActivityType.API_CALL: "api_calls",
                ActivityType.ERROR: "errors",
                ActivityType.AUTONOMOUS_TASK: "autonomous",
                ActivityType.HUMAN_INTERACTION: "human",
                ActivityType.SYSTEM_EVENT: "system",
                ActivityType.SECURITY_EVENT: "security",
                ActivityType.PERFORMANCE: "performance"
            }
            category = category_map.get(activity_type, "main")
            log_file = os.path.join(self.logs_dir, category, f"{category}_{date}.log")
        else:
            log_file = os.path.join(self.logs_dir, "main", f"alleybot_{date}.log")
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip() and not line.startswith('#'):
                            try:
                                log_entry = json.loads(line)
                                
                                # Apply filters
                                if level and log_entry.get("level") != level.value:
                                    continue
                                if platform and log_entry.get("platform") != platform:
                                    continue
                                
                                logs.append(log_entry)
                                
                                if len(logs) >= limit:
                                    break
                            except json.JSONDecodeError:
                                continue
            except Exception:
                pass
        
        return sorted(logs, key=lambda x: x["timestamp"], reverse=True)
    
    def get_activity_summary(self, date: str = None) -> Dict:
        """Get summary of activities for a date"""
        
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logs = self.get_logs(date=date, limit=10000)
        
        summary = {
            "date": date,
            "total_activities": len(logs),
            "by_type": {},
            "by_platform": {},
            "by_level": {},
            "success_rate": 0,
            "error_count": 0,
            "api_calls": 0,
            "platform_activities": 0,
            "coding_activities": 0,
            "autonomous_tasks": 0
        }
        
        success_count = 0
        
        for log in logs:
            # Count by type
            activity_type = log.get("activity_type", "unknown")
            summary["by_type"][activity_type] = summary["by_type"].get(activity_type, 0) + 1
            
            # Count by platform
            platform = log.get("platform")
            if platform:
                summary["by_platform"][platform] = summary["by_platform"].get(platform, 0) + 1
            
            # Count by level
            level = log.get("level", "info")
            summary["by_level"][level] = summary["by_level"].get(level, 0) + 1
            
            # Success rate
            if log.get("details", {}).get("success", True):
                success_count += 1
            
            # Specific counts
            if activity_type == ActivityType.ERROR.value:
                summary["error_count"] += 1
            elif activity_type == ActivityType.API_CALL.value:
                summary["api_calls"] += 1
            elif activity_type in [ActivityType.PLATFORM_POST.value, ActivityType.PLATFORM_COMMENT.value, ActivityType.PLATFORM_UPVOTE.value]:
                summary["platform_activities"] += 1
            elif activity_type == ActivityType.CODING.value:
                summary["coding_activities"] += 1
            elif activity_type == ActivityType.AUTONOMOUS_TASK.value:
                summary["autonomous_tasks"] += 1
        
        if summary["total_activities"] > 0:
            summary["success_rate"] = (success_count / summary["total_activities"]) * 100
        
        return summary

# Global logger instance
logger = AlleyBotLogger()
