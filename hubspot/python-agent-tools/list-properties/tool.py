from dataiku.llm.agent_tools import BaseAgentTool
import requests, json, logging

class HubspotListPropertiesTool(BaseAgentTool):
    """List properties for any standard or custom schema in a HubSpot portal."""

    HUBSPOT_API_HOST = "https://api.hubspot.com"
    
    # Standard HubSpot object types for reference in the description
    HUBSPOT_OBJECT_TYPES = [
        "contacts", "companies", "deals", "tickets", 
        "products", "line_items", "quotes", "calls", 
        "emails", "meetings", "notes", "tasks"
    ]

    def set_config(self, config, plugin_config):
        self.access_token = config["hubspot_api_connection"]
        
        # Re-use one Session for every request (keeps TLS connection alive)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

    def get_descriptor(self, tool):
        object_types = ", ".join(self.HUBSPOT_OBJECT_TYPES)
        return {
            "description": """
            
            Purpose:
            • Lists every property definition (name, label, type, etc.) for a given object type.

            Returns:
            • Array of property definitions.

            Usage Guidance:
            • Response can be large; request only when you genuinely need the full catalogue.  
            • For a quick sense of common fields, sample a handful of records with list-objects first.  
            • Set includeHidden=true if you need internal or deprecated fields.
            
            """,
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/list-properties/input",
                "title": "Input for HubSpot List Properties tool",
                "type": "object",
                "properties": {
                    "objectType": {
                        "type": "string",
                        "description": f"The type of HubSpot object to get properties for. Valid values include: {object_types}. For custom objects, use the get-schemas tool to get the objectType."
                    },
                    "archived": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to return only properties that have been archived."
                    },
                    "includeHidden": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to include hidden properties in the response."
                    }
                },
                "required": ["objectType"]
            }
        }

    def invoke(self, input, trace):
        args = input.get("input", {})
        object_type = args.get("objectType")
        
        # Defensive check
        if not object_type:
            return {
                "output": {"error": "Missing required parameter 'objectType'."},
                "isError": True
            }
        
        # Build query parameters
        params = {
            "archived": str(args.get("archived", False)).lower(),
            "includeHidden": str(args.get("includeHidden", False)).lower()
        }
        
        # Call HubSpot
        try:
            url = f"{self.HUBSPOT_API_HOST}/crm/v3/properties/{object_type}"
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            
            # Filter each result to include only specific fields
            filtered_results = [
                {
                    "name": prop.get("name"),
                    "label": prop.get("label"),
                    "type": prop.get("type"),
                    "description": prop.get("description"),
                    "groupName": prop.get("groupName")
                }
                for prop in data.get("results", [])
            ]
            
            formatted = {
                "results": filtered_results,
                "paging": data.get("paging", {})
            }
            
            return {
                "output": formatted,
                "sources": [{
                    "toolCallDescription": f"Listed HubSpot properties for object type: {object_type}",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": f"HubSpot {object_type} properties",
                        "content": json.dumps(formatted, indent=2)
                    }]
                }]
            }
            
        except Exception as e:
            logging.error(f"Error listing HubSpot properties for {object_type}: {e}")
            return {
                "output": {"error": f"Error listing HubSpot properties for {object_type}: {e}"},
                "isError": True
            }