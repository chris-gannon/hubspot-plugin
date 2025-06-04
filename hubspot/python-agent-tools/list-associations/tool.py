from dataiku.llm.agent_tools import BaseAgentTool
import requests
import json
import logging

class HubspotListAssociationsTool(BaseAgentTool):
    """Lists associations between a specific HubSpot object and other objects of a particular type."""

    HUBSPOT_API_HOST = "https://api.hubspot.com"

    def set_config(self, config, plugin_config):
        self.access_token = config["hubspot_api_connection"]
        
        # Re-use one Session for every request (keeps TLS connection alive)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
        
        # List of common HubSpot object types for reference
        self.hubspot_object_types = [
            "contacts", "companies", "deals", "tickets",
            "line_items", "products", "quotes", "calls",
            "emails", "meetings", "tasks", "notes"
        ]

    def get_descriptor(self, tool):
        object_types = ", ".join(self.hubspot_object_types)
        return {
            "description": """
            
            Purpose:
            • Retrieves the relationships (associations) between one record (objectId) and another object type.

            Returns:
            • toObjectIds + relationship metadata; paging cursor if more results.

            Usage Guidance:
            • Typical pattern:  
                1  Call list-associations to get the IDs of related records.  
                2  Call list-objects with ids=[…] to pull full details of those related records.  
            • Use when you already have the source objectId and want to map its connections.
            
            """,
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/list-associations/input",
                "title": "Input for HubSpot List Associations tool",
                "type": "object",
                "properties": {
                    "objectType": {
                        "type": "string",
                        "description": f"The type of HubSpot object to get associations from. Valid values include: {object_types}. For custom objects, use the get-schemas tool to get the objectType."
                    },
                    "objectId": {
                        "type": "string",
                        "description": "The ID of the HubSpot object to get associations from"
                    },
                    "toObjectType": {
                        "type": "string",
                        "description": f"The type of HubSpot object to get associations to. Valid values include: {object_types}. For custom objects, use the get-schemas tool to get the objectType."
                    },
                    "after": {
                        "type": "string",
                        "description": "Paging cursor token for retrieving the next page of results"
                    }
                },
                "required": ["objectType", "objectId", "toObjectType"]
            }
        }

    def invoke(self, input, trace):
        args = input.get("input", {})
        
        # Validate required parameters
        required_params = ["objectType", "objectId", "toObjectType"]
        for param in required_params:
            if param not in args:
                return {
                    "output": {"error": f"Missing required parameter '{param}'"},
                    "isError": True
                }
        
        try:
            # Build the API path
            endpoint = f"/crm/v4/objects/{args['objectType']}/{args['objectId']}/associations/{args['toObjectType']}?limit=500"
            
            # Add pagination parameter if provided
            if args.get("after"):
                endpoint += f"&after={args['after']}"
            
            # Make API request
            url = f"{self.HUBSPOT_API_HOST}{endpoint}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                "output": data,
                "sources": [{
                    "toolCallDescription": f"Listed associations from {args['objectType']} to {args['toObjectType']}",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": f"HubSpot associations: {args['objectType']} -> {args['toObjectType']}",
                        "content": json.dumps(data, indent=2)
                    }]
                }]
            }
            
        except Exception as e:
            logging.error(f"Error retrieving HubSpot associations: {str(e)}")
            return {
                "output": {"error": f"Error retrieving HubSpot associations: {str(e)}"},
                "isError": True
            }