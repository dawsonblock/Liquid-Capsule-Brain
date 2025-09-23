"""Static code analysis integration for early issue detection."""

import ast
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

log = logging.getLogger(__name__)


@dataclass
class CodeIssue:
    """Code issue detected by static analysis."""
    file_path: str
    line_number: int
    column_number: int
    issue_type: str
    severity: str
    message: str
    rule_id: str
    fix_suggestion: Optional[str] = None


@dataclass
class SecurityIssue:
    """Security issue detected by static analysis."""
    file_path: str
    line_number: int
    issue_type: str
    severity: str
    description: str
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result of static code analysis."""
    total_issues: int
    issues_by_severity: Dict[str, int] = field(default_factory=dict)
    issues_by_type: Dict[str, int] = field(default_factory=dict)
    security_issues: List[SecurityIssue] = field(default_factory=list)
    code_issues: List[CodeIssue] = field(default_factory=list)
    files_analyzed: int = 0
    analysis_time: float = 0.0


class StaticAnalyzer:
    """Static code analysis system with multiple analyzers."""

    def __init__(self) -> None:
        """Initialize the static analyzer."""
        self.analysis_enabled = os.getenv("STATIC_ANALYSIS_ENABLED", "true").lower() == "true"
        self.security_analysis_enabled = os.getenv("SECURITY_ANALYSIS_ENABLED", "true").lower() == "true"
        self.quality_analysis_enabled = os.getenv("QUALITY_ANALYSIS_ENABLED", "true").lower() == "true"
        
        # Analysis tools configuration
        self.tools = {
            "ruff": {"enabled": True, "command": "ruff"},
            "mypy": {"enabled": True, "command": "mypy"},
            "bandit": {"enabled": self.security_analysis_enabled, "command": "bandit"},
            "safety": {"enabled": self.security_analysis_enabled, "command": "safety"},
            "pylint": {"enabled": False, "command": "pylint"},  # Disabled by default
        }
        
        # Issue severity mapping
        self.severity_mapping = {
            "error": "high",
            "warning": "medium",
            "info": "low",
            "hint": "low",
            "critical": "critical",
            "high": "high",
            "medium": "medium",
            "low": "low"
        }
        
        log.info("Static Analyzer initialized")

    def analyze_codebase(self, paths: List[str] = None) -> AnalysisResult:
        """Analyze the entire codebase."""
        if not self.analysis_enabled:
            return AnalysisResult(total_issues=0)
        
        import time
        start_time = time.time()
        
        if paths is None:
            paths = ["capsule_brain", "tests"]
        
        result = AnalysisResult(total_issues=0)
        result.files_analyzed = self._count_files(paths)
        
        # Run different analyzers
        if self.tools["ruff"]["enabled"]:
            self._run_ruff_analysis(paths, result)
        
        if self.tools["mypy"]["enabled"]:
            self._run_mypy_analysis(paths, result)
        
        if self.tools["bandit"]["enabled"]:
            self._run_bandit_analysis(paths, result)
        
        if self.tools["safety"]["enabled"]:
            self._run_safety_analysis(result)
        
        # Calculate final statistics
        result.total_issues = len(result.code_issues) + len(result.security_issues)
        result.analysis_time = time.time() - start_time
        
        # Group issues by severity
        for issue in result.code_issues:
            severity = self.severity_mapping.get(issue.severity, "medium")
            result.issues_by_severity[severity] = result.issues_by_severity.get(severity, 0) + 1
            result.issues_by_type[issue.issue_type] = result.issues_by_type.get(issue.issue_type, 0) + 1
        
        for issue in result.security_issues:
            result.issues_by_severity[issue.severity] = result.issues_by_severity.get(issue.severity, 0) + 1
            result.issues_by_type["security"] = result.issues_by_type.get("security", 0) + 1
        
        log.info(f"Static analysis completed: {result.total_issues} issues found in {result.files_analyzed} files")
        
        return result

    def _count_files(self, paths: List[str]) -> int:
        """Count files to be analyzed."""
        count = 0
        for path in paths:
            path_obj = Path(path)
            if path_obj.is_file() and path_obj.suffix == '.py':
                count += 1
            elif path_obj.is_dir():
                count += len(list(path_obj.rglob("*.py")))
        return count

    def _run_ruff_analysis(self, paths: List[str], result: AnalysisResult) -> None:
        """Run Ruff analysis."""
        try:
            cmd = [self.tools["ruff"]["command"], "check", "--output-format=json"] + paths
            output = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if output.returncode == 0:
                return  # No issues found
            
            # Parse JSON output
            import json
            try:
                ruff_data = json.loads(output.stdout)
                for item in ruff_data:
                    issue = CodeIssue(
                        file_path=item["filename"],
                        line_number=item["location"]["row"],
                        column_number=item["location"]["column"],
                        issue_type=item["code"],
                        severity=self.severity_mapping.get(item["level"], "medium"),
                        message=item["message"],
                        rule_id=item["code"]
                    )
                    result.code_issues.append(issue)
            except json.JSONDecodeError:
                log.warning("Failed to parse Ruff JSON output")
                
        except subprocess.TimeoutExpired:
            log.warning("Ruff analysis timed out")
        except Exception as e:
            log.error(f"Ruff analysis failed: {e}")

    def _run_mypy_analysis(self, paths: List[str], result: AnalysisResult) -> None:
        """Run MyPy analysis."""
        try:
            cmd = [self.tools["mypy"]["command"], "--show-error-codes", "--no-error-summary"] + paths
            output = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Parse MyPy output
            for line in output.stdout.split('\n'):
                if ':' in line and ('error:' in line or 'warning:' in line or 'note:' in line):
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        file_path = parts[0].strip()
                        line_number = int(parts[1]) if parts[1].strip().isdigit() else 0
                        severity = "error" if "error:" in line else "warning" if "warning:" in line else "info"
                        message = parts[3].strip()
                        
                        issue = CodeIssue(
                            file_path=file_path,
                            line_number=line_number,
                            column_number=0,
                            issue_type="type_check",
                            severity=self.severity_mapping.get(severity, "medium"),
                            message=message,
                            rule_id="mypy"
                        )
                        result.code_issues.append(issue)
                        
        except subprocess.TimeoutExpired:
            log.warning("MyPy analysis timed out")
        except Exception as e:
            log.error(f"MyPy analysis failed: {e}")

    def _run_bandit_analysis(self, paths: List[str], result: AnalysisResult) -> None:
        """Run Bandit security analysis."""
        try:
            cmd = [self.tools["bandit"]["command"], "-r", "-f", "json"] + paths
            output = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            # Parse JSON output
            import json
            try:
                bandit_data = json.loads(output.stdout)
                for issue_data in bandit_data.get("results", []):
                    issue = SecurityIssue(
                        file_path=issue_data["filename"],
                        line_number=issue_data["line_number"],
                        issue_type=issue_data["test_name"],
                        severity=self.severity_mapping.get(issue_data["issue_severity"], "medium"),
                        description=issue_data["issue_text"],
                        cwe_id=issue_data.get("issue_cwe", {}).get("id"),
                        owasp_category=issue_data.get("issue_cwe", {}).get("owasp")
                    )
                    result.security_issues.append(issue)
            except json.JSONDecodeError:
                log.warning("Failed to parse Bandit JSON output")
                
        except subprocess.TimeoutExpired:
            log.warning("Bandit analysis timed out")
        except Exception as e:
            log.error(f"Bandit analysis failed: {e}")

    def _run_safety_analysis(self, result: AnalysisResult) -> None:
        """Run Safety dependency analysis."""
        try:
            cmd = [self.tools["safety"]["command"], "check", "--json"]
            output = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # Parse JSON output
            import json
            try:
                safety_data = json.loads(output.stdout)
                for issue_data in safety_data:
                    issue = SecurityIssue(
                        file_path="requirements.txt",  # Safety doesn't provide file paths
                        line_number=0,
                        issue_type="vulnerable_dependency",
                        severity="high",  # Safety issues are typically high severity
                        description=f"Vulnerable package: {issue_data.get('package', 'unknown')} - {issue_data.get('advisory', 'No description')}",
                        cwe_id=issue_data.get("cwe"),
                        owasp_category="A06:2021"  # Vulnerable Components
                    )
                    result.security_issues.append(issue)
            except json.JSONDecodeError:
                log.warning("Failed to parse Safety JSON output")
                
        except subprocess.TimeoutExpired:
            log.warning("Safety analysis timed out")
        except Exception as e:
            log.error(f"Safety analysis failed: {e}")

    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        if not self.analysis_enabled:
            return {"analysis_enabled": False}
        
        # Run quick analysis
        result = self.analyze_codebase()
        
        return {
            "analysis_enabled": self.analysis_enabled,
            "security_analysis_enabled": self.security_analysis_enabled,
            "quality_analysis_enabled": self.quality_analysis_enabled,
            "total_issues": result.total_issues,
            "issues_by_severity": result.issues_by_severity,
            "issues_by_type": result.issues_by_type,
            "security_issues_count": len(result.security_issues),
            "code_issues_count": len(result.code_issues),
            "files_analyzed": result.files_analyzed,
            "analysis_time": result.analysis_time,
            "tools_enabled": {name: config["enabled"] for name, config in self.tools.items()}
        }

    def get_detailed_report(self) -> Dict[str, Any]:
        """Get detailed analysis report."""
        if not self.analysis_enabled:
            return {"analysis_enabled": False}
        
        result = self.analyze_codebase()
        
        # Generate recommendations
        recommendations = self._generate_analysis_recommendations(result)
        
        return {
            "summary": self.get_analysis_summary(),
            "security_issues": [
                {
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "cwe_id": issue.cwe_id,
                    "owasp_category": issue.owasp_category
                }
                for issue in result.security_issues
            ],
            "code_issues": [
                {
                    "file": issue.file_path,
                    "line": issue.line_number,
                    "column": issue.column_number,
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "message": issue.message,
                    "rule_id": issue.rule_id,
                    "fix_suggestion": issue.fix_suggestion
                }
                for issue in result.code_issues
            ],
            "recommendations": recommendations
        }

    def _generate_analysis_recommendations(self, result: AnalysisResult) -> List[str]:
        """Generate analysis recommendations."""
        recommendations = []
        
        # Security recommendations
        if result.security_issues:
            high_severity_security = [i for i in result.security_issues if i.severity == "high"]
            if high_severity_security:
                recommendations.append(f"Address {len(high_severity_security)} high-severity security issues immediately")
            
            vulnerable_deps = [i for i in result.security_issues if i.issue_type == "vulnerable_dependency"]
            if vulnerable_deps:
                recommendations.append(f"Update {len(vulnerable_deps)} vulnerable dependencies")
        
        # Code quality recommendations
        if result.code_issues:
            high_severity_code = [i for i in result.code_issues if i.severity == "high"]
            if high_severity_code:
                recommendations.append(f"Fix {len(high_severity_code)} high-severity code issues")
            
            # Check for common issue types
            issue_types = {}
            for issue in result.code_issues:
                issue_types[issue.issue_type] = issue_types.get(issue.issue_type, 0) + 1
            
            most_common = max(issue_types.items(), key=lambda x: x[1]) if issue_types else None
            if most_common and most_common[1] > 5:
                recommendations.append(f"Focus on fixing {most_common[0]} issues ({most_common[1]} occurrences)")
        
        # General recommendations
        if result.total_issues > 50:
            recommendations.append("Consider implementing automated code quality checks in CI/CD")
        
        if result.security_issues:
            recommendations.append("Implement security scanning in the development workflow")
        
        return recommendations

    def export_analysis_data(self, filepath: str) -> None:
        """Export analysis data to file."""
        if not self.analysis_enabled:
            return
        
        import json
        
        analysis_data = {
            "summary": self.get_analysis_summary(),
            "detailed_report": self.get_detailed_report()
        }
        
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2, default=str)
        
        log.info(f"Analysis data exported to {filepath}")


# Global static analyzer instance
static_analyzer = StaticAnalyzer()
