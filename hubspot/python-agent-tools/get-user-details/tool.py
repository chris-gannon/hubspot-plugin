from dataiku.llm.agent_tools import BaseAgentTool
import requests
import json
import logging

class HubspotGetUserDetailsTool(BaseAgentTool):
    def set_config(self, config, plugin_config):
        self.access_token = config["hubspot_api_connection"]
        self.base_url = "https://api.hubspot.com"
        
    def get_descriptor(self, tool):
        return {
            "description": """
            
            Purpose:
            • Validates the current HubSpot private-app token and identifies the authenticated user and portal.  

            Returns:
            • User-level: userId, ownerId (if the user is an owner)  
            • Portal-level: hubId, uiDomain, portal name  
            • Token-level: token type, appId, list of authorised scopes  

            Usage Guidance:
            • ALWAYS call this first in a session so the agent knows which scopes are available.  
            • The hubId + uiDomain can be combined to build deep links into HubSpot.  
            • Subsequent tool calls may rely on ownerId to filter “my” records.  
            
            """,            
            "inputSchema": {
                "$id": "https://dataiku.com/agents/tools/get-user-details/input",
                "title": "Input for HubSpot Get User Details tool",
                "type": "object",
                "properties": {}  # No input properties needed
            }
        }

    def invoke(self, input, trace):
        try:
            # Get token info
            token_info_url = f"{self.base_url}/oauth/v2/private-apps/get/access-token-info"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            token_info_response = requests.post(
                token_info_url, 
                headers=headers, 
                json={"tokenKey": self.access_token}
            )
            token_info_response.raise_for_status()
            token_info = token_info_response.json()
            
            # Get account info
            account_info_url = f"{self.base_url}/account-info/v3/details"
            account_info_response = requests.get(account_info_url, headers=headers)
            
            if account_info_response.status_code == 200:
                account_info = account_info_response.json()
            else:
                account_info = None
            
            # Get owner info if token info has userId
            owner_info = None
            if token_info and "userId" in token_info:
                owner_info_url = f"{self.base_url}/crm/v3/owners/{token_info['userId']}?idProperty=userId&archived=false"
                owner_info_response = requests.get(owner_info_url, headers=headers)
                
                if owner_info_response.status_code == 200:
                    owner_info = owner_info_response.json()
            
            # Format the response
            formatted_response = {
                "tokenInfo": token_info,
                "ownerInfo": owner_info,
                "accountInfo": account_info
            }
            
            # Generate human-readable content for sources
            readable_content = (
                f"- Token Info: {json.dumps(token_info, indent=2)}\n"
                f"- Owner Info: {json.dumps(owner_info, indent=2)}\n"
                f"- Account Info: {json.dumps(account_info, indent=2)}"
            )
            
            return {
                "output": formatted_response,
                "sources": [{
                    "toolCallDescription": "Retrieved HubSpot user details",
                    "items": [{
                        "type": "SIMPLE_DOCUMENT",
                        "title": "HubSpot User Details",
                        "content": readable_content
                    }]
                }]
            }
            
        except Exception as e:
            logging.error(f"Error retrieving HubSpot user details: {str(e)}")
            return {
                "output": {"error": f"Error retrieving HubSpot user details: {str(e)}"},
                "isError": True
            }
