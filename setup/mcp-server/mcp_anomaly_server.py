"""MCP Server for Anomaly Detection.

Provides tools for detecting and querying network anomalies.
"""

import os
import json
import boto3
from boto3.dynamodb.conditions import Key
from mcp.server.fastmcp import FastMCP
from datetime import datetime

mcp = FastMCP(host="0.0.0.0", port=8000, stateless_http=True)

# Initialize DynamoDB resource
dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-west-2"))

# Get the anomalies table
table = dynamodb.Table(os.environ.get("ANOMALIES_TABLE", "telco-anomalies-synthetic-data"))


@mcp.tool()
def detect_anomaly(market: str) -> str:
    """Detect network anomalies for a specific telecom market.

    This tool queries the anomalies database for active issues in a given market.

    Args:
        market: The geographic market to check (e.g., 'Denver', 'Phoenix')

    Returns:
        JSON string containing anomaly details or error message
    """
    try:
        print ("ddb table :: ", table)
        # Query DynamoDB using the market-index GSI
        response = table.query(
            IndexName="market-index",
            KeyConditionExpression=Key("market").eq(market),
            ScanIndexForward=False,  # Most recent first
            Limit=10  # Limit to 10 most recent anomalies
        )

        items = response.get("Items", [])
        print ("ddb table items for detect_anomaly :: ", items)
        if not items:
            return json.dumps({
                "status": "success",
                "market": market,
                "message": f"No anomalies detected in {market}",
                "anomalies": []
            })

        # Format anomalies for the agent
        formatted_anomalies = []
        for item in items:
            formatted_anomaly = {
                "anomaly_id": item.get("anomaly_id"),
                "severity": item.get("severity"),
                "type": item.get("type"),
                "component": item.get("component"),
                "description": item.get("description"),
                "status": item.get("status"),
                "affected_customers": item.get("affected_customers"),
                "timestamp": item.get("timestamp"),
                "cell_sites": item.get("cell_sites", []),
                "kpi_impact": item.get("kpi_impact", {})
            }
            formatted_anomalies.append(formatted_anomaly)

        print ("formatted_anomalies :: ", formatted_anomalies)
        # Sort by severity (P1 first)
        severity_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
        formatted_anomalies.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return json.dumps({
            "status": "success",
            "market": market,
            "anomaly_count": len(formatted_anomalies),
            "anomalies": formatted_anomalies,
            "summary": f"Found {len(formatted_anomalies)} anomalies in {market}. "
                      f"Highest severity: {formatted_anomalies[0]['severity']}"
        }, default=str)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to query anomalies: {str(e)}"
        })


@mcp.tool()
def get_anomaly_details(anomaly_id: str) -> str:
    """Get detailed information about a specific anomaly.

    Args:
        anomaly_id: The unique identifier of the anomaly

    Returns:
        JSON string with detailed anomaly information
    """
    try:
        print ("ddb table :: ", table)
        # Get item from DynamoDB
        response = table.get_item(Key={"anomaly_id": anomaly_id})
        print ("get_anomaly_details - ddb get_item response :: ", response)
        if "Item" not in response:
            return json.dumps({
                "status": "error",
                "message": f"Anomaly {anomaly_id} not found"
            })

        item = response["Item"]
        print ("get_anomaly_details - ddb get_item response record :: ", item)
        # Calculate duration if still active
        duration = "Ongoing"
        if item.get("status") == "RESOLVED" and item.get("resolved_at"):
            start_time = datetime.fromisoformat(item["timestamp"])
            end_time = datetime.fromisoformat(item["resolved_at"])
            duration = str(end_time - start_time)

        return json.dumps({
            "status": "success",
            "anomaly": {
                "anomaly_id": item.get("anomaly_id"),
                "market": item.get("market"),
                "severity": item.get("severity"),
                "type": item.get("type"),
                "component": item.get("component"),
                "description": item.get("description"),
                "status": item.get("status"),
                "affected_customers": item.get("affected_customers"),
                "timestamp": item.get("timestamp"),
                "duration": duration,
                "cell_sites": item.get("cell_sites", []),
                "kpi_impact": item.get("kpi_impact", {}),
                "notes": item.get("notes", [])
            }
        }, default=str)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to get anomaly details: {str(e)}"
        })


@mcp.tool()
def list_active_markets() -> str:
    """List all markets with active anomalies.

    Returns:
        JSON string with list of markets and anomaly counts
    """
    try:
        print ("ddb table :: ", table)
        # Scan table for all active anomalies
        response = table.scan(
            FilterExpression=Key("status").eq("ACTIVE")
        )
        print ("list_active_markets - ddb get_item response :: ", response)
        items = response.get("Items", [])
        print ("list_active_markets - ddb get_item response items :: ", items)
        # Count anomalies by market
        market_counts = {}
        for item in items:
            market = item.get("market", "Unknown")
            market_counts[market] = market_counts.get(market, 0) + 1

        # Sort markets by anomaly count
        sorted_markets = sorted(market_counts.items(), key=lambda x: x[1], reverse=True)

        return json.dumps({
            "status": "success",
            "total_active_anomalies": len(items),
            "affected_markets": len(market_counts),
            "markets": [
                {"market": market, "anomaly_count": count}
                for market, count in sorted_markets
            ]
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to list active markets: {str(e)}"
        })


if __name__ == "__main__":
    print("🚀 Starting Anomaly Detection MCP Server on port 8000...")
    print("📊 Available tools:")
    print("   - detect_anomaly(market: str)")
    print("   - get_anomaly_details(anomaly_id: str)")
    print("   - list_active_markets()")
    print("")
    print("Server ready for connections...")

    # Run the MCP server
    mcp.run(transport="streamable-http")