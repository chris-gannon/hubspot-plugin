from dataiku.llm.agent_tools import BaseAgentTool
import requests
import json
import logging

class HubspotGetSchemasTool(BaseAgentTool):
    """Retrieves all custom object schemas defined in the HubSpot account."""
    
    HUBSPOT_API_HOST = "https://api.hubspot.com"
    
    def set_config(self, config, plugin_config):
        self.access_token = config["hubspot_api_connection"]
        
        # Re-use one Session for every request
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        })
        
    def get_descriptor(self, tool):
        return {
            "description": """
            
            Purpose:
            • Lists all custom-object schemas in the portal so you know their objectType IDs and structure.

            Returns:
            • For each custom object: objectTypeId, fully-qualified objectType, primary display property and other metadata.

            Usage Guidance:
            • Call once at the start if you plan to work with custom objects; cache the objectTypeId for subsequent list-objects or search-objects calls.  
            • Standard CRM objects (contacts, companies, etc.) are NOT returned—those are known a-priori.
            
            """,
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/get-schemas/input",
                "title": "Input for HubSpot Get Schemas tool",
                "type": "object",
                "properties": {}  # No input properties needed
            }
        }
        
    def invoke(self, input, trace):
        try:
            url = f"{self.HUBSPOT_API_HOST}/crm-object-schemas/v3/schemas"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            schemas = response.json()
            
            # Simplify the results to match the JavaScript implementation
            simplified_results = []
            for schema in schemas.get("results", []):
                # Extract objectType from fullyQualifiedName
                object_type = schema.get("fullyQualifiedName", "").split('_')[1] if '_' in schema.get("fullyQualifiedName", "") else ""
                
                simplified_results.append({
                    "objectTypeId": schema.get("objectTypeId"),
                    "objectType": object_type,
                    "name": schema.get("name"),
                    "labels": schema.get("labels")
                })
            
            formatted_result = {"results": simplified_results}
            
            return {
                "output": formatted_result,
                "sources": [{
                    "toolCallDescription": "Retrieved HubSpot custom object schemas",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": "HubSpot Schema Information",
                        "content": json.dumps(formatted_result, indent=2)
                    }]
                }]
            }
            
        except Exception as e:
            logging.error(f"Error retrieving HubSpot schemas: {str(e)}")
            return {
                "output": {"error": f"Error retrieving HubSpot schemas: {str(e)}"},
                "isError": True
            }