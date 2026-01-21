"""Lakebase token refresh mechanism for service principal authentication.

Lakebase requires Databricks identity authentication (tokens) rather than
native PostgreSQL password authentication. This module handles token
generation and refresh for service principals.
"""

import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Token cache with expiration tracking
_token_cache: Optional[str] = None
_token_expires_at: Optional[datetime] = None
_token_lock = threading.Lock()

# Service principal configuration
SERVICE_PRINCIPAL_CLIENT_ID = os.environ.get("LAKEBASE_SERVICE_PRINCIPAL_CLIENT_ID", "1ae64aaa-98b3-435b-9d2d-df62f4460d24")
LAKEBASE_INSTANCE_NAME = os.environ.get("LAKEBASE_INSTANCE_NAME", "sales-agent-db")
LAKEBASE_HOST = os.environ.get("LAKEBASE_HOST")
LAKEBASE_DATABASE = os.environ.get("LAKEBASE_DATABASE", "databricks_postgres")


def generate_database_credential_token() -> tuple[str, datetime]:
    """Generate a new database credential token for the service principal.
    
    Uses Databricks REST API via the Python SDK or HTTP requests.
    
    Returns:
        Tuple of (token, expiration_time)
    """
    try:
        # Use REST API directly (SDK may use incorrect endpoint)
        import requests
        
        host = os.environ.get("DATABRICKS_HOST")
        token_pat = os.environ.get("DATABRICKS_TOKEN")  # Service principal token or PAT
        
        if not host or not token_pat:
            raise ValueError(
                "DATABRICKS_HOST and DATABRICKS_TOKEN environment variables required. "
                "Use service principal token or PAT for authentication."
            )
        
        # Correct endpoint: /api/2.0/database/credentials (not /api/2.0/sql/database-credentials/generate)
        url = f"{host}/api/2.0/database/credentials"
        headers = {"Authorization": f"Bearer {token_pat}"}
        payload = {
            "request_id": f"sales-agent-mcp-{int(time.time())}",
            "instance_names": [LAKEBASE_INSTANCE_NAME],
        }
        
        logger.info(f"Generating database credential token via REST API: {url}")
        logger.info(f"Payload: request_id={payload['request_id']}, instance_names={payload['instance_names']}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            token = data["token"]
            expiration_str = data["expiration_time"]
        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else 'N/A'
            response_text = http_err.response.text[:500] if http_err.response else 'N/A'  # Limit response text length
            logger.error(f"HTTP error calling {url}: Status {status_code}")
            logger.error(f"Response body: {response_text}")
            # Don't include the original exception message as it may contain old URLs
            raise RuntimeError(f"Failed to generate database credential token: HTTP {status_code} for {url}. Response: {response_text}")
        except Exception as req_err:
            logger.error(f"Request error calling {url}: {req_err}")
            # Don't include the original exception message as it may contain old URLs
            raise RuntimeError(f"Failed to generate database credential token for {url}: {type(req_err).__name__}")
        
        # Parse expiration time (ISO 8601 format)
        # Handle both timezone-aware and timezone-naive formats
        expiration_str_clean = expiration_str.replace("Z", "+00:00")
        expiration_time = datetime.fromisoformat(expiration_str_clean)
        
        # Always convert to timezone-naive UTC for consistent comparison
        # If timezone-aware, convert to UTC first, then remove timezone info
        if expiration_time.tzinfo is not None:
            # Convert to UTC, then remove timezone info
            expiration_time = expiration_time.astimezone(timezone.utc).replace(tzinfo=None)
        
        logger.info(f"Generated new database credential token, expires at {expiration_time} (timezone-naive UTC)")
        return token, expiration_time
        
    except RuntimeError:
        # Re-raise RuntimeError as-is (already has proper error message)
        raise
    except Exception as e:
        logger.error(f"Error generating database credential token: {e}", exc_info=True)
        raise RuntimeError(f"Failed to generate database credential token: {e}")


def get_database_token() -> str:
    """Get a valid database credential token, refreshing if necessary.
    
    Tokens are cached and automatically refreshed when they expire.
    
    Returns:
        Valid database credential token
    """
    global _token_cache, _token_expires_at
    
    # Print to stdout for immediate visibility (not just logs)
    print(f"[DEBUG PRINT] get_database_token called")
    
    with _token_lock:
        # Use timezone-naive UTC datetime for consistent comparison
        now = datetime.utcnow()
        print(f"[DEBUG PRINT] now={now}, now.tzinfo={now.tzinfo}")
        logger.info(f"[DEBUG] get_database_token START: now={now} (tzinfo={now.tzinfo}), _token_cache={_token_cache is not None}, _token_expires_at={_token_expires_at}")
        print(f"[DEBUG PRINT] _token_expires_at={_token_expires_at}, type={type(_token_expires_at)}")
        
        # Normalize expiration time to timezone-naive if needed
        expires_at_normalized = None
        if _token_expires_at is not None:
            logger.info(f"[DEBUG] _token_expires_at exists: {_token_expires_at}, tzinfo={_token_expires_at.tzinfo}, type={type(_token_expires_at)}")
            if _token_expires_at.tzinfo is not None:
                # Convert timezone-aware to timezone-naive UTC
                logger.info(f"[DEBUG] Converting timezone-aware datetime to naive")
                expires_at_normalized = _token_expires_at.astimezone(timezone.utc).replace(tzinfo=None)
                _token_expires_at = expires_at_normalized
                logger.info(f"[DEBUG] Normalized to: {expires_at_normalized}, tzinfo={expires_at_normalized.tzinfo}")
            else:
                expires_at_normalized = _token_expires_at
                logger.info(f"[DEBUG] Already timezone-naive: {expires_at_normalized}, tzinfo={expires_at_normalized.tzinfo}")
        else:
            logger.info(f"[DEBUG] _token_expires_at is None")
        
        # Check if we need to refresh the token
        # Refresh 5 minutes before expiration to avoid race conditions
        should_refresh = _token_cache is None or expires_at_normalized is None
        logger.info(f"[DEBUG] Initial should_refresh check: {should_refresh} (_token_cache={_token_cache is not None}, expires_at_normalized={expires_at_normalized is not None})")
        
        if not should_refresh:
            # Safe comparison - both are timezone-naive
            logger.info(f"[DEBUG] Preparing comparison: now={now} (tzinfo={now.tzinfo}), expires_at_normalized={expires_at_normalized} (tzinfo={expires_at_normalized.tzinfo})")
            print(f"[DEBUG PRINT] About to compare: now={now} (tzinfo={now.tzinfo}), expires_at_normalized={expires_at_normalized} (tzinfo={expires_at_normalized.tzinfo})")
            
            # CRITICAL SAFETY CHECK: Ensure both are timezone-naive before comparison
            if now.tzinfo is not None:
                logger.error(f"[DEBUG] now has timezone info! Converting to naive: {now}")
                now = now.replace(tzinfo=None)
                print(f"[DEBUG PRINT] Converted now to naive: {now}")
            if expires_at_normalized.tzinfo is not None:
                logger.error(f"[DEBUG] expires_at_normalized has timezone info! Converting to naive: {expires_at_normalized}")
                expires_at_normalized = expires_at_normalized.astimezone(timezone.utc).replace(tzinfo=None)
                print(f"[DEBUG PRINT] Converted expires_at_normalized to naive: {expires_at_normalized}")
            
            refresh_threshold = expires_at_normalized - timedelta(minutes=5)
            logger.info(f"[DEBUG] refresh_threshold={refresh_threshold} (tzinfo={refresh_threshold.tzinfo})")
            print(f"[DEBUG PRINT] refresh_threshold={refresh_threshold} (tzinfo={refresh_threshold.tzinfo})")
            logger.info(f"[DEBUG] About to compare: now >= refresh_threshold")
            print(f"[DEBUG PRINT] About to compare: now >= refresh_threshold")
            logger.info(f"[DEBUG] now type: {type(now)}, refresh_threshold type: {type(refresh_threshold)}")
            print(f"[DEBUG PRINT] now type: {type(now)}, refresh_threshold type: {type(refresh_threshold)}")
            logger.info(f"[DEBUG] now.tzinfo: {now.tzinfo}, refresh_threshold.tzinfo: {refresh_threshold.tzinfo}")
            print(f"[DEBUG PRINT] now.tzinfo: {now.tzinfo}, refresh_threshold.tzinfo: {refresh_threshold.tzinfo}")
            should_refresh = now >= refresh_threshold
            logger.info(f"[DEBUG] Comparison result: {should_refresh}")
            print(f"[DEBUG PRINT] Comparison result: {should_refresh}")
        
        if should_refresh:
            logger.info("Refreshing database credential token...")
            _token_cache, new_expires_at = generate_database_credential_token()
            logger.info(f"[DEBUG] Generated new token: new_expires_at={new_expires_at}, tzinfo={new_expires_at.tzinfo if new_expires_at else None}, type={type(new_expires_at)}")
            # CRITICAL: Ensure the returned datetime is timezone-naive
            # Even though generate_database_credential_token should return naive, double-check
            if new_expires_at is not None:
                if new_expires_at.tzinfo is not None:
                    logger.warning(f"[DEBUG] Token expiration has timezone info! Normalizing: {new_expires_at}")
                    _token_expires_at = new_expires_at.astimezone(timezone.utc).replace(tzinfo=None)
                    logger.info(f"[DEBUG] After normalization: {_token_expires_at}, tzinfo={_token_expires_at.tzinfo}")
                else:
                    _token_expires_at = new_expires_at
                    logger.info(f"[DEBUG] Token expiration already timezone-naive: {_token_expires_at}")
            else:
                logger.error("[DEBUG] generate_database_credential_token returned None expiration!")
                _token_expires_at = None
        
        logger.info(f"[DEBUG] get_database_token END: returning token, _token_expires_at={_token_expires_at}")
        return _token_cache


def get_lakebase_connection_string() -> str:
    """Get the Lakebase connection string with current token.
    
    Returns:
        PostgreSQL connection string with service principal and token
    """
    token = get_database_token()
    
    if not LAKEBASE_HOST:
        raise ValueError("LAKEBASE_HOST environment variable is required")
    
    # Use service principal client ID as username
    # URL-encode the token (it's a JWT, so it may contain special characters)
    from urllib.parse import quote_plus
    encoded_token = quote_plus(token)
    
    return f"postgresql://{SERVICE_PRINCIPAL_CLIENT_ID}:{encoded_token}@{LAKEBASE_HOST}:5432/{LAKEBASE_DATABASE}?sslmode=require"


def refresh_token_in_background():
    """Background thread to refresh tokens before expiration."""
    while True:
        try:
            # Sleep until 5 minutes before expiration
            with _token_lock:
                if _token_expires_at:
                    # Ensure expiration time is timezone-naive
                    expires_at = _token_expires_at
                    if expires_at.tzinfo is not None:
                        expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
                    sleep_until = expires_at - timedelta(minutes=5)
                    sleep_seconds = (sleep_until - datetime.utcnow()).total_seconds()
                    
                    if sleep_seconds > 0:
                        time.sleep(sleep_seconds)
            
            # Refresh token
            get_database_token()
            
        except Exception as e:
            logger.error(f"Error in token refresh background thread: {e}")
            # Wait 1 minute before retrying on error
            time.sleep(60)


def start_token_refresh_thread():
    """Start background thread for token refresh."""
    thread = threading.Thread(target=refresh_token_in_background, daemon=True)
    thread.start()
    logger.info("Started background token refresh thread")
