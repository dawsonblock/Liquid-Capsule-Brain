"""Advanced security enhancement system with threat detection and response."""

import hashlib
import hmac
import logging
import os
import re
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger(__name__)


@dataclass
class SecurityEvent:
    """Security event data."""
    event_id: str
    event_type: str
    severity: str
    timestamp: float
    source_ip: str
    user_agent: str
    request_path: str
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    response_action: str = "logged"


@dataclass
class ThreatPattern:
    """Threat pattern for detection."""
    pattern_id: str
    name: str
    pattern: str
    severity: str
    description: str
    mitigation: str


class ThreatDetector:
    """Advanced threat detection system."""

    def __init__(self):
        """Initialize threat detector."""
        self.threat_patterns: List[ThreatPattern] = []
        self.detection_history: deque = deque(maxlen=1000)
        self.blocked_ips: Set[str] = set()
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        self.rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Load default threat patterns
        self._load_default_patterns()
        
        # Configuration
        self.max_requests_per_minute = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
        self.block_threshold = int(os.getenv("SECURITY_BLOCK_THRESHOLD", "5"))
        self.detection_enabled = os.getenv("THREAT_DETECTION_ENABLED", "true").lower() == "true"
        
        log.info("Threat Detector initialized")

    def _load_default_patterns(self) -> None:
        """Load default threat patterns."""
        default_patterns = [
            ThreatPattern(
                pattern_id="sql_injection",
                name="SQL Injection",
                pattern=r"(union|select|insert|update|delete|drop|create|alter|exec|execute).*?(from|into|where|set)",
                severity="high",
                description="SQL injection attempt detected",
                mitigation="Block request and log incident"
            ),
            ThreatPattern(
                pattern_id="xss_attempt",
                name="Cross-Site Scripting",
                pattern=r"<script[^>]*>.*?</script>|javascript:|on\w+\s*=",
                severity="high",
                description="XSS attempt detected",
                mitigation="Sanitize input and block request"
            ),
            ThreatPattern(
                pattern_id="path_traversal",
                name="Path Traversal",
                pattern=r"\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c",
                severity="medium",
                description="Path traversal attempt detected",
                mitigation="Block request and log incident"
            ),
            ThreatPattern(
                pattern_id="command_injection",
                name="Command Injection",
                pattern=r"[;&|`$(){}[\]\\]",
                severity="high",
                description="Command injection attempt detected",
                mitigation="Block request immediately"
            ),
            ThreatPattern(
                pattern_id="file_inclusion",
                name="File Inclusion",
                pattern=r"(include|require|file_get_contents|fopen|readfile).*?\.\./",
                severity="medium",
                description="File inclusion attempt detected",
                mitigation="Block request and sanitize input"
            )
        ]
        
        self.threat_patterns.extend(default_patterns)

    def detect_threats(self, request_data: Dict[str, Any]) -> List[SecurityEvent]:
        """Detect threats in request data."""
        if not self.detection_enabled:
            return []
        
        detected_threats = []
        current_time = time.time()
        
        # Check request content for threat patterns
        content_to_check = [
            request_data.get("path", ""),
            request_data.get("query_string", ""),
            request_data.get("body", ""),
            request_data.get("headers", {}).get("user-agent", ""),
            request_data.get("headers", {}).get("referer", "")
        ]
        
        for content in content_to_check:
            if not content:
                continue
                
            content_str = str(content).lower()
            
            for pattern in self.threat_patterns:
                if re.search(pattern.pattern, content_str, re.IGNORECASE):
                    event = SecurityEvent(
                        event_id=f"{pattern.pattern_id}_{int(current_time * 1000)}",
                        event_type=pattern.pattern_id,
                        severity=pattern.severity,
                        timestamp=current_time,
                        source_ip=request_data.get("source_ip", "unknown"),
                        user_agent=request_data.get("headers", {}).get("user-agent", "unknown"),
                        request_path=request_data.get("path", ""),
                        details={
                            "pattern": pattern.name,
                            "description": pattern.description,
                            "mitigation": pattern.mitigation,
                            "matched_content": content_str[:200]  # Truncate for logging
                        }
                    )
                    
                    detected_threats.append(event)
                    self.detection_history.append(event)
        
        return detected_threats

    def check_rate_limit(self, source_ip: str) -> Tuple[bool, str]:
        """Check if IP is within rate limits."""
        current_time = time.time()
        minute_window = int(current_time // 60)
        
        # Clean old entries
        ip_requests = self.rate_limits[source_ip]
        while ip_requests and ip_requests[0] < minute_window:
            ip_requests.popleft()
        
        # Check current rate
        if len(ip_requests) >= self.max_requests_per_minute:
            self.suspicious_ips[source_ip] += 1
            
            # Block IP if it exceeds threshold
            if self.suspicious_ips[source_ip] >= self.block_threshold:
                self.blocked_ips.add(source_ip)
                return False, "blocked"
            
            return False, "rate_limited"
        
        # Add current request
        ip_requests.append(minute_window)
        return True, "allowed"

    def is_ip_blocked(self, source_ip: str) -> bool:
        """Check if IP is blocked."""
        return source_ip in self.blocked_ips

    def unblock_ip(self, source_ip: str) -> None:
        """Unblock an IP address."""
        self.blocked_ips.discard(source_ip)
        self.suspicious_ips[source_ip] = 0
        log.info(f"IP {source_ip} has been unblocked")

    def get_threat_summary(self) -> Dict[str, Any]:
        """Get threat detection summary."""
        if not self.detection_enabled:
            return {"detection_enabled": False}
        
        # Calculate statistics
        total_threats = len(self.detection_history)
        threats_by_type = defaultdict(int)
        threats_by_severity = defaultdict(int)
        
        for event in self.detection_history:
            threats_by_type[event.event_type] += 1
            threats_by_severity[event.severity] += 1
        
        return {
            "detection_enabled": self.detection_enabled,
            "total_threats_detected": total_threats,
            "blocked_ips_count": len(self.blocked_ips),
            "suspicious_ips_count": len(self.suspicious_ips),
            "threats_by_type": dict(threats_by_type),
            "threats_by_severity": dict(threats_by_severity),
            "active_patterns": len(self.threat_patterns),
            "rate_limit_threshold": self.max_requests_per_minute,
            "block_threshold": self.block_threshold
        }


class SecurityEnhancer:
    """Advanced security enhancement system."""

    def __init__(self):
        """Initialize security enhancer."""
        self.threat_detector = ThreatDetector()
        self.security_events: deque = deque(maxlen=1000)
        self.encryption_key = os.getenv("SECURITY_ENCRYPTION_KEY", "default-key-change-in-production")
        self.security_enabled = os.getenv("SECURITY_ENHANCEMENT_ENABLED", "true").lower() == "true"
        
        # Security headers
        self.security_headers = {
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "no-referrer-when-downgrade",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=(), accelerometer=(), ambient-light-sensor=()"
        }
        
        log.info("Security Enhancer initialized")

    def analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze request for security threats."""
        if not self.security_enabled:
            return {"security_enabled": False}
        
        analysis_result = {
            "threats_detected": [],
            "rate_limit_status": "allowed",
            "ip_blocked": False,
            "security_score": 100,  # Start with perfect score
            "recommendations": []
        }
        
        source_ip = request_data.get("source_ip", "unknown")
        
        # Check if IP is blocked
        if self.threat_detector.is_ip_blocked(source_ip):
            analysis_result["ip_blocked"] = True
            analysis_result["security_score"] = 0
            analysis_result["recommendations"].append("Request blocked - IP is blacklisted")
            return analysis_result
        
        # Check rate limits
        rate_limit_ok, rate_limit_status = self.threat_detector.check_rate_limit(source_ip)
        analysis_result["rate_limit_status"] = rate_limit_status
        
        if not rate_limit_ok:
            analysis_result["security_score"] -= 20
            analysis_result["recommendations"].append("Rate limit exceeded")
        
        # Detect threats
        threats = self.threat_detector.detect_threats(request_data)
        analysis_result["threats_detected"] = threats
        
        # Adjust security score based on threats
        for threat in threats:
            if threat.severity == "high":
                analysis_result["security_score"] -= 30
            elif threat.severity == "medium":
                analysis_result["security_score"] -= 15
            elif threat.severity == "low":
                analysis_result["security_score"] -= 5
            
            analysis_result["recommendations"].append(threat.details.get("mitigation", "Review request"))
        
        # Record security event
        if threats or not rate_limit_ok:
            security_event = SecurityEvent(
                event_id=f"security_{int(time.time() * 1000)}",
                event_type="request_analysis",
                severity="medium" if threats else "low",
                timestamp=time.time(),
                source_ip=source_ip,
                user_agent=request_data.get("headers", {}).get("user-agent", "unknown"),
                request_path=request_data.get("path", ""),
                details=analysis_result
            )
            self.security_events.append(security_event)
        
        return analysis_result

    def sanitize_input(self, input_data: str) -> str:
        """Sanitize user input."""
        if not input_data:
            return ""
        
        # Remove HTML tags
        sanitized = re.sub(r'<[^>]+>', '', input_data)
        
        # Escape special characters
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')
        
        # Remove potential script content
        sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'data:text/html', '', sanitized, flags=re.IGNORECASE)
        
        return sanitized

    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token."""
        timestamp = str(int(time.time()))
        data = f"{session_id}:{timestamp}"
        token = hmac.new(
            self.encryption_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{token}:{timestamp}"

    def validate_csrf_token(self, token: str, session_id: str) -> bool:
        """Validate CSRF token."""
        try:
            token_part, timestamp_part = token.split(':')
            timestamp = int(timestamp_part)
            
            # Check if token is not too old (5 minutes)
            if time.time() - timestamp > 300:
                return False
            
            # Recreate expected token
            data = f"{session_id}:{timestamp_part}"
            expected_token = hmac.new(
                self.encryption_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(token_part, expected_token)
        except (ValueError, TypeError):
            return False

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers."""
        return self.security_headers.copy()

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security enhancement summary."""
        if not self.security_enabled:
            return {"security_enabled": False}
        
        # Calculate statistics
        total_events = len(self.security_events)
        events_by_type = defaultdict(int)
        events_by_severity = defaultdict(int)
        
        for event in self.security_events:
            events_by_type[event.event_type] += 1
            events_by_severity[event.severity] += 1
        
        return {
            "security_enabled": self.security_enabled,
            "threat_detection": self.threat_detector.get_threat_summary(),
            "total_security_events": total_events,
            "events_by_type": dict(events_by_type),
            "events_by_severity": dict(events_by_severity),
            "blocked_ips": list(self.threat_detector.blocked_ips),
            "security_headers_count": len(self.security_headers),
            "recommendations": self._generate_security_recommendations()
        }

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        # Check for high-severity threats
        high_severity_threats = [
            event for event in self.security_events
            if event.severity == "high"
        ]
        
        if high_severity_threats:
            recommendations.append(f"Address {len(high_severity_threats)} high-severity security events")
        
        # Check for blocked IPs
        if self.threat_detector.blocked_ips:
            recommendations.append(f"Review {len(self.threat_detector.blocked_ips)} blocked IP addresses")
        
        # Check for suspicious IPs
        suspicious_count = len(self.threat_detector.suspicious_ips)
        if suspicious_count > 10:
            recommendations.append(f"Monitor {suspicious_count} suspicious IP addresses")
        
        # General recommendations
        recommendations.append("Regularly update threat patterns and security rules")
        recommendations.append("Implement Web Application Firewall (WAF) for additional protection")
        recommendations.append("Enable security monitoring and alerting")
        
        return recommendations

    def export_security_data(self, filepath: str) -> None:
        """Export security data for analysis."""
        if not self.security_enabled:
            return
        
        import json
        
        security_data = {
            "summary": self.get_security_summary(),
            "security_events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "timestamp": event.timestamp,
                    "source_ip": event.source_ip,
                    "user_agent": event.user_agent,
                    "request_path": event.request_path,
                    "details": event.details,
                    "blocked": event.blocked,
                    "response_action": event.response_action
                }
                for event in self.security_events
            ],
            "threat_patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "name": pattern.name,
                    "pattern": pattern.pattern,
                    "severity": pattern.severity,
                    "description": pattern.description,
                    "mitigation": pattern.mitigation
                }
                for pattern in self.threat_detector.threat_patterns
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(security_data, f, indent=2, default=str)
        
        log.info(f"Security data exported to {filepath}")


# Global security enhancer instance
security_enhancer = SecurityEnhancer()
