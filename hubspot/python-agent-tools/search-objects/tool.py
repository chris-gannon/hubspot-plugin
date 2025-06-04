from dataiku.llm.agent_tools import BaseAgentTool
import requests
import json
import logging

# Constants from the original JS tool
HUBSPOT_OBJECT_TYPES = [
    "contacts", "companies", "deals", "tickets",
    "line_items", "products", "quotes", "calls",
    "emails", "meetings", "tasks", "notes"
]

class HubspotSearchObjectsTool(BaseAgentTool):
    """Performs advanced filtered searches across HubSpot object types using complex criteria."""

    HUBSPOT_API_HOST = "https://api.hubspot.com"

    def set_config(self, config, plugin_config):
        # Get access token from config
        self.access_token = config["hubspot_api_connection"]
        
        # Re-use one Session for every request (keeps TLS connection alive)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

    def get_descriptor(self, tool):
        object_types = ", ".join(HUBSPOT_OBJECT_TYPES)
        return {
            "description": """
            
            Purpose:
            • Performs precision searches on a CRM object type using filterGroups, filters and/or a free-text query.

            Returns:
            • Matching records plus paging information.

            Usage Guidance:
            • Preferred when you know EXACTLY what you’re looking for (e.g. “deals with amount > 10 000 closed this month”).  
            • Use list-objects first to discover property names, then search-objects for the precise pull.  
            • If search returns IDs you need to inspect in full, pass those IDs to list-objects (ids=…).
            
            """,
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/search-objects/input",
                "title": "Input for HubSpot Search Objects tool",
                "type": "object",
                "properties": {
                    "objectType": {
                        "type": "string",
                        "description": f"The type of HubSpot object to search. Valid values include: {object_types}. For custom objects, use the get-schemas tool to get the objectType."
                    },
                    "query": {
                        "type": "string",
                        "description": "Text to search across default searchable properties of the specified object type. Each object type has different searchable properties. For example: contacts (firstname, lastname, email, phone, company), companies (name, website, domain, phone), deals (dealname, pipeline, dealstage, description, dealtype), etc"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                        "description": "The maximum number of results to display per page (max: 100)."
                    },
                    "after": {
                        "type": "string",
                        "description": "The paging cursor token of the last successfully read resource."
                    },
                    "properties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of the properties to be returned in the response."
                    },
                    "sorts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "propertyName": {
                                    "type": "string",
                                    "description": "The name of the property to sort by"
                                },
                                "direction": {
                                    "type": "string",
                                    "enum": ["ASCENDING", "DESCENDING"],
                                    "description": "The sort direction"
                                }
                            },
                            "required": ["propertyName", "direction"]
                        },
                        "description": "A list of sort criteria to apply to the results."
                    },
                    "filterGroups": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "filters": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "propertyName": {
                                                "type": "string",
                                                "description": "The name of the property to filter by"
                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": [
                                                    "EQ", "NEQ", "LT", "LTE", "GT", "GTE", 
                                                    "BETWEEN", "IN", "NOT_IN", "HAS_PROPERTY", 
                                                    "NOT_HAS_PROPERTY", "CONTAINS_TOKEN", 
                                                    "NOT_CONTAINS_TOKEN"
                                                ],
                                                "description": "The operator to use for comparison"
                                            },
                                            "value": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {"type": "number"},
                                                    {"type": "boolean"}
                                                ],
                                                "description": "The value to compare against. Must be a string, number, or boolean"
                                            },
                                            "values": {
                                                "type": "array",
                                                "items": {
                                                    "oneOf": [
                                                        {"type": "string"},
                                                        {"type": "number"},
                                                        {"type": "boolean"}
                                                    ]
                                                },
                                                "description": "Set of values for multi-value operators like IN and NOT_IN."
                                            },
                                            "highValue": {
                                                "oneOf": [
                                                    {"type": "string"},
                                                    {"type": "number"},
                                                    {"type": "boolean"}
                                                ],
                                                "description": "The upper bound value for range operators like BETWEEN. The lower bound is specified by the value attribute"
                                            }
                                        },
                                        "required": ["propertyName", "operator"]
                                    },
                                    "description": "Array of filters to apply (combined with AND)."
                                }
                            },
                            "required": ["filters"]
                        },
                        "description": "Groups of filters to apply (combined with OR)."
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

        try:
            # Prepare request body
            request_body = {}
            
            # Add optional parameters
            if "query" in args:
                request_body["query"] = args["query"]
            
            if "limit" in args:
                request_body["limit"] = args["limit"]
            
            if "after" in args:
                request_body["after"] = args["after"]
            
            if "properties" in args and args["properties"]:
                request_body["properties"] = args["properties"]
            
            if "sorts" in args and args["sorts"]:
                request_body["sorts"] = args["sorts"]
            
            if "filterGroups" in args and args["filterGroups"]:
                request_body["filterGroups"] = args["filterGroups"]

            # Call HubSpot API
            url = f"{self.HUBSPOT_API_HOST}/crm/v3/objects/{object_type}/search"
            response = self.session.post(url, json=request_body, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Format the results
            results = [
                {
                    "id": item.get("id"),
                    "properties": item.get("properties", {}),
                    "createdAt": item.get("createdAt"),
                    "updatedAt": item.get("updatedAt"),
                    "archived": item.get("archived", False),
                    "archivedAt": item.get("archivedAt")
                }
                for item in data.get("results", [])
            ]

            formatted = {"results": results, "paging": data.get("paging", {})}

            return {
                "output": formatted,
                "sources": [{
                    "toolCallDescription": f"Searched HubSpot {object_type} with criteria",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": f"HubSpot {object_type} search results",
                        "content": json.dumps(formatted, indent=2)
                    }]
                }]
            }

        except Exception as e:
            logging.error(f"Error searching HubSpot {object_type}: {str(e)}")
            return {
                "output": {"error": f"Error searching HubSpot {object_type}: {str(e)}"},
                "isError": True
            }
