Here’s the content of the Hubspot Plugin Documentation PDF converted into clean, GitHub-friendly Markdown format for your README:

⸻

Hubspot Plugin Documentation

Prerequisites
	1.	Create a private app in HubSpot
Go to: Settings → Integrations → Private Apps → Create private app
	2.	Name the app and assign scopes
	•	Tip: Start with read-only scopes if you’re just testing.
	3.	Create the app and copy the access token
	•	Store it securely.

⸻

Tools

Category	Tool Name	Description
OAuth	get-user-details	Authenticate a private-app token and return user, hub, and scope details.
Objects	list-objects	List CRM records (paged) for a chosen object type.
Objects	search-objects	Filter/search CRM records with complex criteria.
Objects	get-schemas	List custom-object schemas.
Properties	list-properties	List all properties for any object type.
Associations	list-associations	List relationships for a record.


⸻

Testing and Scopes

get-user-details

Scopes: oauth, settings.user.read, etc.
Test Query:

{
  "input": {},
  "context": {}
}


⸻

list-objects

Scopes: crm.objects.{object}.read
Test Query:

{
  "input": {
    "objectType": "contacts",
    "limit": 10,
    "properties": ["email", "firstname", "lastname"]
  },
  "context": {}
}


⸻

search-objects

Scopes: crm.objects.{object}.read
Test Query:

{
  "input": {
    "objectType": "contacts",
    "query": "test",
    "limit": 10,
    "properties": ["email", "firstname", "lastname"],
    "filterGroups": [
      {
        "filters": [
          {
            "propertyName": "email",
            "operator": "CONTAINS_TOKEN",
            "value": "example.com"
          }
        ]
      }
    ]
  },
  "context": {}
}


⸻

get-schemas

Scopes: crm.schemas.{object}.read
Test Query:

{
  "input": {},
  "context": {}
}


⸻

list-properties

Scopes: crm.schemas.{object}.read
Test Query:

{
  "input": {
    "objectType": "contacts",
    "includeHidden": true
  },
  "context": {}
}


⸻

list-associations

Scopes: crm.objects.{object}.read
Test Query:

{
  "input": {
    "objectType": "contacts",
    "objectId": "12345",
    "toObjectType": "companies"
  },
  "context": {}
}

Replace {object} with specific CRM objects such as contacts, companies, deals, tickets, notes, or tasks when configuring scopes.

⸻

Example Prompts

Tool	Prompt Examples
get-user-details	“Which HubSpot account am I connected to and what can my token do?”“Remind me who I am in HubSpot and which APIs I’m allowed to use.”
list-objects	“Show me our contacts list.”“Give me the latest deals in the pipeline.”
search-objects	“Find open deals worth more than $10,000.”“Pull contacts who have ‘@example.com’ in their email.”
list-associations	“Which contacts belong to the company ‘Acme Corp’?”“Which deals are linked to contact john@example.com?”
list-properties	“What fields do we track on company records?”“What data points exist on a support ticket in HubSpot?”
get-schemas	“Do we have any custom objects in our portal?”“What does the ‘Subscriptions’ custom object look like?”


⸻

Let me know if you want this saved as a .md file or if you’d like any parts expanded or stylized further.
