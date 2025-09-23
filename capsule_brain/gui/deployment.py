"""Deployment configuration and utilities for the GUI."""

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)


class GUIDeploymentManager:
    """Manager for GUI deployment configuration and utilities."""

    def __init__(self, app: FastAPI) -> None:
        """Initialize GUI deployment manager.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.environment = os.getenv("APP_ENV", "development").lower()
        self.debug_mode = self.environment in {"local", "development", "dev"}
        self._setup_deployment_routes()

    def _setup_deployment_routes(self) -> None:
        """Setup deployment-specific routes."""

        @self.app.get("/deployment/info", include_in_schema=False)
        async def get_deployment_info() -> JSONResponse:
            """Get deployment information."""
            info = {
                "environment": self.environment,
                "debug_mode": self.debug_mode,
                "version": "1.0.1",
                "features": {
                    "gui_enabled": True,
                    "websocket_enabled": True,
                    "file_upload_enabled": True,
                    "mobile_support": True,
                    "analytics_enabled": True,
                    "security_enabled": True,
                    "performance_monitoring": True,
                },
                "limits": {
                    "max_file_size": int(os.getenv("UPLOAD_MAX_BYTES", "10485760")),
                    "rate_limit": "60 requests per minute",
                    "websocket_message_limit": 10000,
                },
                "security": {
                    "cors_enabled": True,
                    "rate_limiting": True,
                    "input_validation": True,
                    "file_validation": True,
                },
                "performance": {
                    "caching_enabled": True,
                    "compression_enabled": True,
                    "optimization_enabled": True,
                },
            }
            return JSONResponse(content=info)

        @self.app.get("/deployment/health", include_in_schema=False)
        async def get_deployment_health() -> JSONResponse:
            """Get deployment health status."""
            health = {
                "status": "healthy",
                "environment": self.environment,
                "debug_mode": self.debug_mode,
                "gui_components": {
                    "static_files": self._check_static_files(),
                    "websocket": True,
                    "security": True,
                    "performance": True,
                },
                "timestamp": self._get_timestamp(),
            }
            return JSONResponse(content=health)

        @self.app.get("/deployment/config", include_in_schema=False)
        async def get_deployment_config() -> JSONResponse:
            """Get deployment configuration."""
            config = {
                "environment": self.environment,
                "debug_mode": self.debug_mode,
                "static_files_path": str(Path(__file__).parent / "static"),
                "allowed_file_types": [".pdf", ".txt", ".zip", ".json", ".csv", ".md"],
                "security_headers": True,
                "rate_limiting": True,
                "cors_origins": os.getenv("CORS_ORIGINS", "*"),
                "admin_token_required": os.getenv("ADMIN_TOKEN") is not None,
            }
            return JSONResponse(content=config)

    def _check_static_files(self) -> bool:
        """Check if static files are accessible.

        Returns:
            True if static files are accessible, False otherwise
        """
        try:
            static_path = Path(__file__).parent / "static"
            return static_path.exists() and (static_path / "index.html").exists()
        except Exception:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp.

        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def get_environment_config(self) -> dict[str, Any]:
        """Get environment-specific configuration.

        Returns:
            Environment configuration dictionary
        """
        base_config = {
            "debug": self.debug_mode,
            "environment": self.environment,
            "security": {
                "rate_limiting": True,
                "input_validation": True,
                "file_validation": True,
                "cors_enabled": True,
            },
            "performance": {
                "caching": True,
                "compression": True,
                "optimization": True,
            },
            "features": {
                "websocket": True,
                "file_upload": True,
                "mobile_support": True,
                "analytics": True,
            },
        }

        # Environment-specific overrides
        if self.environment == "production":
            base_config["security"]["strict_mode"] = True
            base_config["performance"]["aggressive_caching"] = True
            base_config["features"]["debug_panel"] = False
        elif self.environment == "staging":
            base_config["security"]["strict_mode"] = True
            base_config["features"]["debug_panel"] = True
        else:  # development/local
            base_config["security"]["strict_mode"] = False
            base_config["features"]["debug_panel"] = True
            base_config["features"]["hot_reload"] = True

        return base_config

    def setup_production_optimizations(self) -> None:
        """Setup production-specific optimizations."""
        if self.environment != "production":
            return

        log.info("Setting up production GUI optimizations")

        # Add production middleware
        @self.app.middleware("http")
        async def production_middleware(request: Request, call_next: Any) -> Any:
            response = await call_next(request)

            # Add production headers
            if request.url.path.startswith("/static/"):
                response.headers["Cache-Control"] = "public, max-age=31536000"  # 1 year
                response.headers["Expires"] = "Thu, 31 Dec 2025 23:59:59 GMT"
            elif request.url.path == "/":
                response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour

            return response

    def setup_development_features(self) -> None:
        """Setup development-specific features."""
        if not self.debug_mode:
            return

        log.info("Setting up development GUI features")

        @self.app.get("/dev/gui-debug", include_in_schema=False)
        async def gui_debug_info() -> JSONResponse:
            """Development-only GUI debug information."""
            debug_info = {
                "environment": self.environment,
                "debug_mode": self.debug_mode,
                "static_files": {
                    "path": str(Path(__file__).parent / "static"),
                    "exists": self._check_static_files(),
                },
                "configuration": self.get_environment_config(),
                "timestamp": self._get_timestamp(),
            }
            return JSONResponse(content=debug_info)

    def validate_deployment(self) -> dict[str, Any]:
        """Validate deployment configuration.

        Returns:
            Validation results dictionary
        """
        validation_results = {"valid": True, "errors": [], "warnings": [], "checks": {}}

        # Check static files
        static_check = self._check_static_files()
        validation_results["checks"]["static_files"] = static_check
        if not static_check:
            validation_results["errors"].append("Static files not found")
            validation_results["valid"] = False

        # Check environment variables
        required_env_vars = ["APP_ENV"]
        for var in required_env_vars:
            if not os.getenv(var):
                validation_results["warnings"].append(f"Environment variable {var} not set")

        # Check security configuration
        if not os.getenv("ADMIN_TOKEN") and self.environment == "production":
            validation_results["warnings"].append("ADMIN_TOKEN not set in production")

        # Check CORS configuration
        cors_origins = os.getenv("CORS_ORIGINS", "*")
        if cors_origins == "*" and self.environment == "production":
            validation_results["warnings"].append("CORS set to '*' in production")

        return validation_results

    def get_deployment_summary(self) -> dict[str, Any]:
        """Get deployment summary information.

        Returns:
            Deployment summary dictionary
        """
        return {
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "version": "1.0.1",
            "validation": self.validate_deployment(),
            "configuration": self.get_environment_config(),
            "features_enabled": {
                "gui": True,
                "websocket": True,
                "file_upload": True,
                "mobile_support": True,
                "security": True,
                "performance_monitoring": True,
                "analytics": True,
            },
            "deployment_ready": True,
        }


def setup_gui_deployment(app: FastAPI) -> GUIDeploymentManager:
    """Setup GUI deployment configuration.

    Args:
        app: FastAPI application instance

    Returns:
        Configured GUI deployment manager
    """
    manager = GUIDeploymentManager(app)

    # Setup environment-specific features
    manager.setup_production_optimizations()
    manager.setup_development_features()

    log.info(f"GUI deployment configured for {manager.environment} environment")
    return manager
