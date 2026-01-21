"""Startup script for Databricks Apps deployment."""
import logging
import os
import sys
import traceback

# Force unbuffered output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(line_buffering=True)

logger = logging.getLogger(__name__)


def main():
    """Main startup function for the app."""
    try:
        print("=" * 80)
        print("Starting Sales Agent Application...")
        print("=" * 80)
        
        # Step 1: Initialize application
        print("\n[1/4] Initializing application...")
        from core.startup import initialize_application
        initialize_application()
        print("✅ Application initialized")
        
        # Step 2: Initialize database (skip if SKIP_MIGRATIONS is set)
        skip_migrations = os.environ.get("SKIP_MIGRATIONS", "").lower() == "true"
        if skip_migrations:
            print("\n[2/4] Skipping database migrations (SKIP_MIGRATIONS=true)")
        else:
            print("\n[2/4] Running database migrations...")
            from core.database.database import init_db
            init_db(exit_on_error=True)
            print("✅ Database migrations complete")
        
        # Step 3: Import MCP server
        print("\n[3/4] Importing MCP server...", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        
        try:
            import time
            
            # Start import in background - it may hang but module will be in sys.modules when done
            print("  Starting import of core.main...", flush=True)
            sys.stdout.flush()
            
            # Use threading to import without blocking
            import threading
            import_result = {'done': False, 'error': None}
            
            def do_import():
                try:
                    import core.main
                    import_result['done'] = True
                except Exception as e:
                    import_result['error'] = e
                    import_result['done'] = True
            
            thread = threading.Thread(target=do_import, daemon=False)
            thread.start()
            
            # Wait for import with timeout
            thread.join(timeout=15)
            
            # Check if module is in sys.modules (even if thread didn't finish)
            if 'core.main' in sys.modules:
                core_main_module = sys.modules['core.main']
                print("  ✅ Module found in sys.modules", flush=True)
                sys.stdout.flush()
            elif import_result['error']:
                raise import_result['error']
            elif import_result['done']:
                import core.main
                core_main_module = core.main
                print("  ✅ Import completed", flush=True)
                sys.stdout.flush()
            else:
                raise ImportError("core.main import timed out and not in sys.modules")
            
            # Access mcp object
            print("  Accessing mcp object...", flush=True)
            sys.stdout.flush()
            
            if not hasattr(core_main_module, 'mcp'):
                error_msg = "core.main module does not have 'mcp' attribute!"
                print(f"  ❌ ERROR: {error_msg}", flush=True)
                print(f"  Available attributes: {[a for a in dir(core_main_module) if not a.startswith('_')][:20]}", flush=True)
                sys.stdout.flush()
                raise AttributeError(error_msg)
            
            mcp = core_main_module.mcp
            print(f"  ✅ Got mcp object: {type(mcp).__name__}", flush=True)
            sys.stdout.flush()
            
            print("✅ MCP server imported", flush=True)
            sys.stdout.flush()
            sys.stderr.flush()
            
        except ImportError as e:
            print(f"❌ Import Error: {e}", flush=True, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        except AttributeError as e:
            print(f"❌ Attribute Error (mcp not found): {e}", flush=True, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected Error importing MCP server: {type(e).__name__}: {e}", flush=True, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        
        # Step 4: Start MCP server
        print("\n[4/4] Starting MCP server...")
        host = os.environ.get('ADCP_SALES_HOST', '0.0.0.0')
        port = int(os.environ.get('ADCP_SALES_PORT', '8000'))
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print("=" * 80)
        print("🚀 MCP Server starting...")
        print("=" * 80)
        
        # MATCH WORKING APP PATTERN: Use import path like working app
        # Instead of mcp.run(), we use uvicorn.run() with import path string
        print("=" * 80, flush=True)
        print("🔍 Using working app pattern: uvicorn.run() with import path", flush=True)
        print("=" * 80, flush=True)
        sys.stdout.flush()
        
        # Set mcp settings before starting uvicorn
        mcp.settings.host = host
        mcp.settings.port = port
        mcp.settings.streamable_http_path = "/"
        
        print(f"  MCP settings: host={mcp.settings.host}, port={mcp.settings.port}, streamable_http_path={mcp.settings.streamable_http_path}", flush=True)
        print(f"  Using import path: core.main:combined_app", flush=True)
        sys.stdout.flush()
        
        # Run with uvicorn directly using import path (like working app)
        import uvicorn
        print("=" * 80, flush=True)
        print(f"🚀 Starting uvicorn server on {host}:{port} using import path", flush=True)
        print("=" * 80, flush=True)
        sys.stdout.flush()
        
        try:
            # Skip the import test - we know core.main imports successfully (we already imported it)
            # Just call uvicorn.run() directly with the import path string
            # Uvicorn will handle the import internally
            print("=" * 80, flush=True)
            print("🚀 Starting uvicorn.run() with import path: core.main:combined_app", flush=True)
            print("=" * 80, flush=True)
            sys.stdout.flush()
            
            # Run uvicorn with import path string (like working app)
            # This matches the working app pattern exactly
            # Uvicorn will import "core.main:combined_app" and access the combined_app attribute
            uvicorn.run(
                "core.main:combined_app",  # Import path to the combined app
                host=host,
                port=port,
                # Don't specify log_level - let uvicorn use defaults (like working app)
            )
            
            # This should NEVER execute if uvicorn.run() blocks correctly
            print("=" * 80, flush=True)
            print("❌❌❌ CRITICAL: uvicorn.run() RETURNED - THIS SHOULD NEVER HAPPEN!", flush=True)
            print("=" * 80, flush=True)
            sys.stdout.flush()
            sys.exit(1)
            
        except Exception as e:
            print("=" * 80, flush=True)
            print(f"❌❌❌ CRITICAL: uvicorn.run() THREW EXCEPTION: {type(e).__name__}: {e}", flush=True)
            print("=" * 80, flush=True)
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
            sys.exit(1)
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print(f"   Module: {e.name if hasattr(e, 'name') else 'unknown'}")
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Startup Error: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
