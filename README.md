# HubSpot Plugin with Agent Tools

## Prerequisites

1. **Create a private app in HubSpot**  
   `Settings → Integrations → Private Apps → Create private app`
2. **Name the app and assign scopes** (tip: start with read-only scopes if you’re just testing).
3. **Click “Create app”** and copy the generated **access-token**—store it securely.

---

## Tools Overview

| Category    | Tool                | Description                                                                                   |
|-------------|---------------------|-----------------------------------------------------------------------------------------------|
| OAuth       | `get-user-details`  | Authenticate a private-app token and return user, hub, and scope details.                     |
| Objects     | `list-objects`      | List CRM records (paged) for a chosen object type.                                            |
| Objects     | `search-objects`    | Filter/search CRM records with complex criteria.                                              |
| Objects     | `get-schemas`       | List custom-object schemas.                                                                   |
| Properties  | `list-properties`   | List all properties for any object type.                                                      |
| Associations| `list-associations` | List relationships for a record.                                                              |

---

## Testing & Scopes

> **Tip:** Replace `{object}` with a specific CRM object such as `contacts`, `companies`, `deals`, `tickets`, `notes`, or `tasks` when configuring scopes.

### Scope Matrix

| Tool                | Required Scopes                       |
|---------------------|---------------------------------------|
| `get-user-details`  | `oauth`, `settings.user.read`         |
| `list-objects`      | `crm.objects.{object}.read`           |
| `search-objects`    | `crm.objects.{object}.read`           |
| `get-schemas`       | `crm.schemas.{object}.read`           |
| `list-properties`   | `crm.schemas.{object}.read`           |
| `list-associations` | `crm.objects.{object}.read`           |

### Example Request Bodies

<details>
<summary><code>get-user-details</code></summary>

```json
{
  "input": {},
  "context": {}
}
```
</details>

<details>
<summary><code>list-objects</code></summary>

```json
{
  "input": {
    "objectType": "contacts",
    "limit": 10,
    "properties": ["email", "firstname", "lastname"]
  },
  "context": {}
}
```
</details>

<details>
<summary><code>search-objects</code></summary>

```json
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
```
</details>

<details>
<summary><code>get-schemas</code></summary>

```json
{
  "input": {},
  "context": {}
}
```
</details>

<details>
<summary><code>list-properties</code></summary>

```json
{
  "input": {
    "objectType": "contacts",
    "includeHidden": true
  },
  "context": {}
}
```
</details>

<details>
<summary><code>list-associations</code></summary>

```json
{
  "input": {
    "objectType": "contacts",
    "objectId": "12345",
    "toObjectType": "companies"
  },
  "context": {}
}
```
</details>

### Example Prompts

| Tool                | Sample Prompt                         |
|---------------------|---------------------------------------|
| `get-user-details`  | `Which HubSpot account am I connected to and what can my token do?`<br><br>`Remind me who I am in HubSpot and which APIs I can use.`|
| `list-objects`      | `Show me our contacts list.`<br><br>`Give me the latest deals in the pipeline.`|
| `search-objects`    | `Find open deals worth more than $10,000.`<br><br>`Pull contacts who have ‘@example.com’ in their email.`|
| `get-schemas`       | `Which contacts belong to the company ‘Acme Corp’?`<br><br>`Which deals are linked to contact john@example.com?`|
| `list-properties`   | `What fields do we track on company records?`<br><br>`What data points exist on a support ticket in HubSpot?`|
| `list-associations` | `Do we have any custom objects in our portal?`<br><br>`What does the ‘Subscriptions’ custom object look like?`|
