import requests
from requests.auth import HTTPBasicAuth

key_DEP_ticket = "V2DEP-1109"

# Final jira query with excluded tickets
jira_query = "Key in (V2DEP-1130,V2DEP-1122)"


#Jira instance URL and API endpoint
jira_url = 'https://gan-tech.atlassian.net/'
api_endpoint = '/rest/api/2/search'

#Jira credentials
username = 'email@coolbet.com'
api_token = ''



# Construct the API request URL
api_url = f'{jira_url}{api_endpoint}'
headers = {
    'Content-Type': 'application/json'
}

# Set the Jira query payload
payload = {
    'jql': jira_query,
    'startAt': 0,
    'maxResults': 1000  # Set the desired maximum number of results
}


# Send the API request with HTTP Basic Authentication
response = requests.post(api_url, headers=headers, json=payload, auth=HTTPBasicAuth(username, api_token))

# Check the response status code
if response.status_code == 200:
    response_data = response.json()
    issues = response_data['issues']
    issue_data = []
    # Extract the relevant data from each issue
    for issue in issues:
        key = issue['key']

        update_payload = {
        "type": {
            "name": "Relates"
        },
        "inwardIssue": {
            "key": key_DEP_ticket
        },
        "outwardIssue": {
            "key": key
        }
    }

       # Construct the API request URL for updating issues
        update_api_url = f'{jira_url}/rest/api/3/issueLink'

       # Send  API request to update the issue
        update_response = requests.post(
            update_api_url,
            headers=headers,
            json=update_payload,
            auth=HTTPBasicAuth(username, api_token)
        )


    if update_response.status_code == 204:
        print(f'DEP summary ticket "{key_DEP_ticket}" added to issues {key}')
    else:
        print(f'Failed to update issue {key}. Status code: {update_response}')

