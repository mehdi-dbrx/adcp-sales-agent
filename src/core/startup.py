"""Startup configuration and validation for AdCP Sales Agent."""

import logging
import os

from core.config import validate_configuration
from core.logging_config import setup_oauth_logging, setup_structured_logging

logger = logging.getLogger(__name__)


def initialize_application() -> None:
    """Initialize the application with configuration validation and setup.

    This should be called at the start of both the MCP server and Admin UI.

    Raises:
        SystemExit: If configuration validation fails
    """
    try:
        # Setup structured logging FIRST (before any logging calls)
        # This ensures production environments get JSON logs
        setup_structured_logging()

        logger.info("Initializing AdCP Sales Agent...")

        # Setup OAuth-specific logging
        setup_oauth_logging()
        logger.info("Structured logging initialized")

        # Validate all configuration
        validate_configuration()
        logger.info("Configuration validation passed")

        # Initialize Lakebase token refresh if using Lakebase
        if os.environ.get("LAKEBASE_HOST"):
            try:
                # Note: Import uses relative import since src. is patched in wheel
                from core.database.lakebase_token_refresh import start_token_refresh_thread
                start_token_refresh_thread()
                logger.info("Lakebase token refresh initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Lakebase token refresh: {e}")
                # Don't fail startup if token refresh fails - connection will fail later with clearer error

        logger.info("Application initialization completed successfully")

    except Exception as e:
        logger.error(f"Application initialization failed: {str(e)}")
        raise SystemExit(1) from e


def validate_startup_requirements() -> None:
    """Validate startup requirements without full initialization.

    This is useful for health checks and lightweight validation.
    """
    try:
        from core.config import get_config

        # Just check that config can be loaded
        get_config()

        # Note: SUPER_ADMIN_EMAILS is no longer required at startup.
        # Per-tenant OIDC with Setup Mode is the default authentication flow.
        # New tenants start with auth_setup_mode=true, allowing test credentials
        # to log in and configure SSO via the Admin UI.

        logger.info("Startup requirements validation passed")

    except Exception as e:
        logger.error(f"Startup requirements validation failed: {str(e)}")
        raise
