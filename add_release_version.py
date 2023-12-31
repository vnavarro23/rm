import requests
from requests.auth import HTTPBasicAuth

##################################################################################
# This script assigns a release version to a list of tickets
##################################################################################
# Steps to use it:
# 1. Create a fix version for each project to which the tickets are associated
# 2. Add the name of the fix version to the variable fix_version
# 3. Add the list of tickets to the variable final_tickets
##################################################################################

fix_version = "EBH 2.0"

# Final list of tickets
final_tickets = "CSB-1319, CRET-809"

#Jira instance URL and API endpoint
jira_url = 'https://gan-tech.atlassian.net/'
api_endpoint = '/rest/api/2/search'

#Jira credentials
username = 'email@coolbet.com'
api_token = 'add_token_here'

jira_query = f"Key in ({final_tickets}) ORDER BY key DESC" 
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

        update_payload = { "update": { "fixVersions": [ {"add": {'name': fix_version}} ] } }
       # Construct the API request URL for updating issues
        update_api_url = f'{jira_url}/rest/api/2/issue/'

       # Send  API request to update the issue
        update_response = requests.put(
            f'{update_api_url}{key}',
            headers=headers,
            json=update_payload,
            auth=HTTPBasicAuth(username, api_token)
        )


    if update_response.status_code == 204:
        print(f'Fix version "{fix_version}" added to issue {key}')
    else:
        print(f'Failed to update issue {key}. Status code: {update_response.status_code}')

