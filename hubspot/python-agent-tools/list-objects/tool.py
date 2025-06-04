from dataiku.llm.agent_tools import BaseAgentTool
import requests, json, logging


class HubspotListObjectsTool(BaseAgentTool):
    """List objects of any standard or custom schema in a HubSpot portal."""

    HUBSPOT_API_HOST = "https://api.hubspot.com"

    def set_config(self, config, plugin_config):
        self.access_token = config["hubspot_api_connection"]

        # Re-use one Session for every request (keeps TLS connection alive)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })

        # Pre-fetch object schemas so we can display valid choices
        self._object_types = None
        try:
            r = self.session.get(f"{self.HUBSPOT_API_HOST}/crm/v3/schemas", timeout=10)
            r.raise_for_status()
            self._object_types = sorted(s["name"] for s in r.json().get("results", []))
        except Exception as e:
            logging.debug(f"Could not fetch schemas list from HubSpot: {e}")


    def _allowed_object_types(self):
        if self._object_types:             # live list from tenant
            return self._object_types
        # fallback list of well-known CRM objects
        return [
            "contacts", "companies", "deals", "tickets",
            "line_items", "products", "quotes", "calls",
            "emails", "meetings", "tasks", "notes"
        ]

    
    def get_descriptor(self, tool):
        allowed_types = ", ".join(self._allowed_object_types())
        return {
            "description": """
            
            Purpose:
            • Lists CRM records of a chosen object type, page-by-page.  
            • ALSO acts as a lightweight “batch read” when you pass an ids array.

            Returns:
            • Array of objects with properties, metadata and optional associations.  
            • Paging block with ‘after’ cursor for the next page.

            Usage Guidance:
            • Use for broad exploration when you **don’t yet know** the filter criteria.  
            • To fetch specific records returned by list-associations, supply  
              ids=["123","456"] – this avoids the need for a separate batch-read tool.  
            • For targeted queries on property values, use search-objects instead.
            
            """,
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/list-objects/input",
                "title": "Input for HubSpot List Objects tool",
                "type": "object",
                "properties": {
                    "objectType": {
                        "type": "string",
                        "description": (
                            f"The HubSpot object type to list. "
                            f"Valid values include: {allowed_types}. "
                            "For custom objects, use the get-schemas tool."
                        )
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 500,
                        "default": 100,
                        "description": "Maximum number of results to return per page."
                    },
                    "after": {
                        "type": "string",
                        "description": "Paging cursor returned by a previous request."
                    },
                    "properties": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific properties to include for each record."
                    },
                    "associations": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Object types whose ID associations should be returned."
                    },
                    "archived": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether to include archived objects."
                    },
                    "ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Optional. If supplied, the call returns ONLY these records "
                            "(max 100 IDs) using HubSpot's batch/read endpoint."
                        )
                    }
                },
                "required": ["objectType"]
            }
        }

    def invoke(self, input, trace):
        args = input.get("input", {})
        object_type = args.get("objectType")

        if not object_type:
            return {
                "output": {"error": "Missing required parameter 'objectType'."},
                "isError": True
            }

        # Standard list parameters
        params = {}
        if "limit" in args:
            params["limit"] = args["limit"]
        if "after" in args:
            params["after"] = args["after"]
        if args.get("properties"):
            params["properties"] = ",".join(args["properties"])
        if args.get("associations"):
            params["associations"] = ",".join(args["associations"])
        if "archived" in args:
            params["archived"] = str(args["archived"]).lower()

        # Hubspot call
        try:
            ids = args.get("ids")

            if ids:
                if len(ids) > 100:
                    return {
                        "output": {"error": "ids array exceeds HubSpot limit of 100."},
                        "isError": True
                    }
                url = f"{self.HUBSPOT_API_HOST}/crm/v3/objects/{object_type}/batch/read"
                payload = {"inputs": [{"id": str(_id)} for _id in ids]}
                r = self.session.post(url, json=payload, timeout=30)
            else:
                url = f"{self.HUBSPOT_API_HOST}/crm/v3/objects/{object_type}"
                r = self.session.get(url, params=params, timeout=30)

            r.raise_for_status()
            data = r.json()

            # Flatten results
            results = [
                {
                    "id": item.get("id"),
                    "properties": item.get("properties", {}),
                    "createdAt": item.get("createdAt"),
                    "updatedAt": item.get("updatedAt"),
                    "archived": item.get("archived"),
                    "archivedAt": item.get("archivedAt"),
                    "associations": item.get("associations", {})
                }
                for item in data.get("results", [])
            ]

            formatted = {"results": results, "paging": data.get("paging", {})}

            return {
                "output": formatted,
                "sources": [{
                    "toolCallDescription": f"Listed HubSpot objects of type: {object_type}",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": f"HubSpot {object_type} objects",
                        "content": json.dumps(formatted, indent=2)
                    }]
                }]
            }

        except Exception as e:
            logging.error(f"Error listing HubSpot {object_type}: {e}")
            return {
                "output": {"error": f"Error listing HubSpot {object_type}: {e}"},
                "isError": True
            }