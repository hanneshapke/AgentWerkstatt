#!/usr/bin/env python3
"""
Test script to check if 3rd party services (mem0 and langfuse) are operational

This script verifies:
1. Package availability
2. Configuration requirements
3. Service connectivity
4. Basic functionality

Usage: python test_services.py
"""

import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv("../.env")


def print_header(service_name: str) -> None:
    """Print a formatted header for each service test"""
    print(f"\n{'=' * 60}")
    print(f"🔍 Testing {service_name} Service")
    print(f"{'=' * 60}")


def print_status(check_name: str, success: bool, message: str = "") -> None:
    """Print a formatted status line"""
    status = "✅" if success else "❌"
    print(f"{status} {check_name:<30} {message}")


def test_mem0_service() -> dict[str, Any]:
    """Test mem0 memory service functionality"""
    print_header("mem0 Memory")

    results = {
        "package_available": False,
        "config_valid": False,
        "connection_successful": False,
        "basic_operations": False,
        "overall_status": False,
        "error_messages": [],
        "recommendations": [],
    }

    # Test 1: Package availability
    try:
        from mem0 import Memory

        results["package_available"] = True
        print_status("Package installed", True, "mem0ai package found")
    except ImportError as e:
        results["package_available"] = False
        results["error_messages"].append(f"mem0ai package not installed: {e}")
        results["recommendations"].append("Install with: pip install mem0ai")
        print_status("Package installed", False, "mem0ai not found")
        return results

    # Test 2: Configuration
    server_url = os.getenv("MEM0_SERVER_URL", "http://localhost:8000")
    print_status("Configuration", True, f"Server URL: {server_url}")
    results["config_valid"] = True

    # Test 3: Connection test
    try:
        memory = Memory()
        results["connection_successful"] = True
        print_status("Service connection", True, f"Connected to {server_url}")
    except Exception as e:
        results["connection_successful"] = False
        results["error_messages"].append(f"Connection failed: {e}")
        results["recommendations"].extend(
            [
                "Start mem0 service with: docker compose -f third_party/docker-compose.yaml up -d mem0",
                "Or check if mem0 server is running on the configured URL",
            ]
        )
        print_status("Service connection", False, f"Failed to connect: {str(e)[:50]}...")
        return results

    # Test 4: Basic operations
    try:
        # Test basic memory operations
        test_user_id = "test_user_001"
        test_messages = [
            {"role": "user", "content": "Hello, this is a test message"},
            {"role": "assistant", "content": "Hello! This is a test response from the assistant."},
        ]

        # Add a memory
        memory.add(test_messages, user_id=test_user_id)

        # Search for memories
        search_results = memory.search(query="test message", user_id=test_user_id, limit=1)

        if search_results and "results" in search_results:
            results["basic_operations"] = True
            print_status("Basic operations", True, "Add/search operations working")
        else:
            results["basic_operations"] = False
            results["error_messages"].append("Search operation returned no results")
            print_status("Basic operations", False, "Search returned no results")

    except Exception as e:
        results["basic_operations"] = False
        results["error_messages"].append(f"Operations failed: {e}")
        print_status("Basic operations", False, f"Failed: {str(e)[:50]}...")

    # Overall status
    results["overall_status"] = all(
        [
            results["package_available"],
            results["config_valid"],
            results["connection_successful"],
            results["basic_operations"],
        ]
    )

    status_msg = "Fully operational" if results["overall_status"] else "Issues detected"
    print_status("Overall Status", results["overall_status"], status_msg)

    return results


def test_langfuse_service() -> dict[str, Any]:
    """Test Langfuse observability service functionality"""
    print_header("Langfuse Observability")

    results = {
        "package_available": False,
        "config_valid": False,
        "connection_successful": False,
        "basic_operations": False,
        "overall_status": False,
        "error_messages": [],
        "recommendations": [],
    }

    # Test 1: Package availability
    try:
        from langfuse import Langfuse, get_client

        results["package_available"] = True
        print_status("Package installed", True, "langfuse package found")
    except ImportError as e:
        results["package_available"] = False
        results["error_messages"].append(f"langfuse package not installed: {e}")
        results["recommendations"].append("Install with: pip install langfuse")
        print_status("Package installed", False, "langfuse not found")
        return results

    # Test 2: Configuration
    required_env_vars = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        results["config_valid"] = False
        results["error_messages"].append(f"Missing environment variables: {missing_vars}")
        results["recommendations"].extend(
            [
                "Set LANGFUSE_PUBLIC_KEY environment variable",
                "Set LANGFUSE_SECRET_KEY environment variable",
                "Get keys from: https://cloud.langfuse.com (or your self-hosted instance)",
            ]
        )
        print_status("Configuration", False, f"Missing: {missing_vars}")
        return results
    else:
        results["config_valid"] = True
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        print_status("Configuration", True, f"Host: {host}")

    # Test 3: Authentication and connection
    try:
        # Initialize Langfuse client
        langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=langfuse_host,
        )

        # Test authentication
        client = get_client()
        auth_result = client.auth_check()

        if auth_result:
            results["connection_successful"] = True
            print_status("Authentication", True, f"Connected to {langfuse_host}")
        else:
            results["connection_successful"] = False
            results["error_messages"].append("Authentication failed")
            results["recommendations"].append(
                "Check your LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY"
            )
            print_status("Authentication", False, "Auth check failed")
            return results

    except Exception as e:
        results["connection_successful"] = False
        results["error_messages"].append(f"Connection failed: {e}")
        results["recommendations"].extend(
            [
                "Verify your Langfuse credentials",
                "Check if LANGFUSE_HOST is correct",
                "Ensure internet connectivity to Langfuse service",
            ]
        )
        print_status("Authentication", False, f"Failed: {str(e)[:50]}...")
        return results

    # Test 4: Basic operations
    try:
        # Test basic trace creation using the correct v3.2.1 API
        from langfuse import Langfuse

        langfuse_client = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            host=langfuse_host,
        )

        # Create a test span using the correct API
        span = langfuse_client.start_span(name="test_span")

        # Update the span
        span.update(output="Test span completed successfully")

        # End the span
        span.end()

        # Create a test generation
        generation = langfuse_client.start_generation(name="test_generation", model="test-model")

        # Update the generation
        generation.update(input="Test input", output="Test generation output")

        # End the generation
        generation.end()

        # Flush to ensure data is sent
        langfuse_client.flush()

        results["basic_operations"] = True
        print_status("Basic operations", True, "Span and generation creation working")

    except Exception as e:
        results["basic_operations"] = False
        results["error_messages"].append(f"Operations failed: {e}")

    # Overall status
    results["overall_status"] = all(
        [
            results["package_available"],
            results["config_valid"],
            results["connection_successful"],
            results["basic_operations"],
        ]
    )

    status_msg = "Fully operational" if results["overall_status"] else "Issues detected"
    print_status("Overall Status", results["overall_status"], status_msg)

    return results


def print_summary(mem0_results: dict[str, Any], langfuse_results: dict[str, Any]) -> None:
    """Print a summary of all test results"""
    print(f"\n{'=' * 60}")
    print("📋 SUMMARY")
    print(f"{'=' * 60}")

    # Service status overview
    mem0_status = "✅ OPERATIONAL" if mem0_results["overall_status"] else "❌ ISSUES"
    langfuse_status = "✅ OPERATIONAL" if langfuse_results["overall_status"] else "❌ ISSUES"

    print(f"mem0 Memory Service:      {mem0_status}")
    print(f"Langfuse Observability:  {langfuse_status}")

    # Recommendations
    all_recommendations = mem0_results["recommendations"] + langfuse_results["recommendations"]
    if all_recommendations:
        print("\n🔧 RECOMMENDATIONS:")
        for i, rec in enumerate(all_recommendations, 1):
            print(f"  {i}. {rec}")

    # Error summary
    all_errors = mem0_results["error_messages"] + langfuse_results["error_messages"]
    if all_errors:
        print("\n❌ ERRORS ENCOUNTERED:")
        for i, error in enumerate(all_errors, 1):
            print(f"  {i}. {error}")

    # Overall system status
    both_operational = mem0_results["overall_status"] and langfuse_results["overall_status"]
    if both_operational:
        print("\n🎉 All services are operational!")
    else:
        print("\n⚠️  Some services need attention. See recommendations above.")


def main():
    """Main function to run all service tests"""
    print("🔍 AgentWerkstatt Third-Party Services Test")
    print("Testing mem0 and Langfuse operational status...\n")

    # Test services
    mem0_results = test_mem0_service()
    langfuse_results = test_langfuse_service()

    # Print summary
    print_summary(mem0_results, langfuse_results)

    # Exit with appropriate code
    both_operational = mem0_results["overall_status"] and langfuse_results["overall_status"]
    sys.exit(0 if both_operational else 1)


if __name__ == "__main__":
    main()
