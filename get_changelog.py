import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import csv
import re

##################################################################################


import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import csv
import re

##################################################################################
builds = """
sportsbook-silo	185	185	Latest
debezium-heartbeater	54	47	-7
"""
# Notes for snapshot
# sports	2423	2372	-42 is the correct version
# Tickes added manually→ debezium-heartbeater	54	47	-7 : build 47 doesnt have ticket https://www.coolbet.com/p/jenkins/job/debezium-heartbeater/changes
# debezium-heartbeater	54	47	-7

#fix_version = "Wynnbet web 2.2.0"


PRODUCT_TYPE_WEB = "web"
PRODUCT_TYPE_RETAIL = "retail"

PRODUCT_TYPE = PRODUCT_TYPE_WEB  #Options are: PRODUCT_TYPE_WEB or PRODUCT_TYPE_RETAIL

#Jira credentials
username = 'email@coolbet.com'
api_token = 'kjhakj'

#Jira instance URL and API endpoint
jira_url = 'https://gan-tech.atlassian.net/'
api_endpoint = '/rest/api/2/search'

# Jenkins instance and credentials
jenkins_url = 'https://www.coolbet.com/p/jenkins/'
jenkins_user = 'email@coolbet.com'
jenkins_token = 'hjsga'

#Parte 1 Parse the builds

lines = builds.strip().split("\n")
data = {}
for line in lines:
    row = line.strip().split("\t")
    # if not "Latest" in line:
        #line example: warehouse	2810	2809	-1
    data[row[0]] = [int(row[1]), int(row[2])]

#Replace service names to match with jenkins names
replacements = {
    'auth-cb': 'auth_cb',
    'auth-bo': 'auth_bo',
    'sb-odds': 'sb_odds',
    'users-cb': 'users_cb',
    'core-proxy':'client-proxy',
    'sportsbook-reports':'sportsbook_reports'
}

for key, value in data.copy().items():
    modified_key = replacements.get(key)
    # delete old key and update with new value if replacement is found
    if modified_key:
      del data[key]
      data[modified_key] = value

modified_dict = data
##################################################################################
#Parte 2 Extract Jenkins information to get ticket_id and Create Jira query

def get_build_info(job_name, build_number):
    # API endpoint for retrieving build information
    api_endpoint = f'{jenkins_url}/job/{job_name}/{build_number}/api/json'

    # Create a session with authentication credentials
    session = requests.Session()
    session.auth = HTTPBasicAuth(jenkins_user, jenkins_token)

    try:
        response = session.get(api_endpoint)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve build information: {str(e)}")
        return None

def clean_comment(comment):
   try:
    #x = re.search("(\w*-\d*)",comment)
    x = re.search(r'([A-Za-z]+-\d+)',comment)
    clean_comment = x.groups(1)[0]
   except Exception as e:
    #  print(f"!Error while parsing: {comment}")
    #  print(response.json())
    #  print(e)
     return ""
   return clean_comment

def extract_commit_comment(build_info):
    # Extract commit comment from build_info JSON
    change_set = build_info.get('changeSet', {})
    items = change_set.get('items', [])
    commit_comments = []
    for item in items:
        comment = item.get('comment', '')
        parsed_comment = clean_comment(comment)
        if comment:
          commit_comments.append(parsed_comment)
    return commit_comments

def remove_duplicated_tickets(s):
    parts = s.split('-')
    if len(parts) >= 2 and parts[1].isdigit():
        return '-'.join(parts[:2])
    return s


# Iterate over job names and builds
job_builds = modified_dict
commit_comments = set()
for job_name, builds in job_builds.items():
    for build_number in range(builds[1] + 1, builds[0] + 1):
        build_info = get_build_info(job_name, build_number)

        tickets_in_build = extract_commit_comment(build_info)
        tickets_in_build = set(tickets_in_build)
        tickets_in_build = [remove_duplicated_tickets(item) for item in tickets_in_build]

        if build_info:
            commit_comments = commit_comments.union(set(extract_commit_comment(build_info)))


commit_comments_str = ", ".join(commit_comments)

jira_tickets = commit_comments_str
#Exclude tickets from certain projects
def remove_tickets(jira_tickets, tickets_to_remove):
    print("blue")
    print(jira_tickets)
    #remove first character if it's a comma
    if jira_tickets and jira_tickets[0] == ",":
      jira_tickets = jira_tickets[1:]
    print(type(jira_tickets))
    tickets = jira_tickets.split(", ")
    filtered_tickets = [element for element in tickets if not any(element.startswith(ticket) for ticket in tickets_to_remove)]
    result = ", ".join(filtered_tickets)
    return result

if PRODUCT_TYPE == PRODUCT_TYPE_WEB:
  #Exclude tickets from projects: CRET, CCASPLAT, CCASFEAT, CTOOL, CFEND, CCORE
  tickets_to_remove = ["CRET","CTOOL", "CCASPLAT", "CCASFEAT", "CDWH" ]
  filtered_jira_tickets = remove_tickets(jira_tickets, tickets_to_remove)
  # Removed this to the below query AND labels in ('$Wynn', '$Platform', '$Universal', '$Wynnbet-MA')
  filtered_jira_tickets = f"Key in ({filtered_jira_tickets}) AND cf[12354] in (WYNNBET-MA, WYNNBET-AZ, WYNNBET-NY, Platform) and cf[12214] in('GAN Sports Online') ORDER BY key DESC"
elif PRODUCT_TYPE == PRODUCT_TYPE_RETAIL:
  #Exclude tickets from projects: CPAYM, CCASPLAT, CCASFEAT, CTOOL, CMKTG, CFEND, CSERV, CCORE
  tickets_to_remove = ["CCASPLAT", "CCASFEAT", "CTOOL", "CDWH"]
  filtered_jira_tickets = remove_tickets(jira_tickets, tickets_to_remove)
  filtered_jira_tickets = f"Key in ({filtered_jira_tickets}) ORDER BY key DESC"
  #filtered_jira_tickets = f"Key in ({filtered_jira_tickets}) and cf[12214] in ('GAN Sports Retail') AND cf[12354] in ('WYNNBET-MA', 'Platform') ORDER BY key DESC"
else:
  print("Error: Unknown product type!! :()")


##################################################################################
#Parte 3 Get results from Jira query (Get the Jenkins information to extract the ticket id)

jira_query = filtered_jira_tickets
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
response_data = response.json()
print(response_data)
# Check the response status code
if response.status_code == 200:
    # Extract the response JSON data
    response_data = response.json()
    # Process the retrieved issues
    issues = response_data['issues']
    # Create a list to store the issue data
    issue_data = []
    # Extract the relevant data from each issue
    for issue in issues:
        key = issue['key']
        summary = issue['fields']['summary']
        description = issue['fields']['description']
        url = f"{jira_url}browse/{key}"

        #update_payload = { "update": { "fixVersions": [ {"add": {'name': fix_version}} ] } }
        # Construct the API request URL for updating issues
       # update_api_url = f'{jira_url}/rest/api/2/issue/'

        # Send the API request to update the issue
        # update_response = requests.put(
        #     f'{update_api_url}{key}',
        #     headers=headers,
        #     json=update_payload,
        #     auth=HTTPBasicAuth(username, api_token)
        # )

    # Check the response status code for the update request
    # if update_response.status_code == 204:
    #     print(f'Fix version "{fix_version}" added to issue {key}')
    # else:
    #     print(f'Failed to update issue {key}. Status code: {update_response.status_code}')



        # Append the issue data to the list
        issue_data.append([key, summary, description, url])

    # Define the Excel file path
    excel_file = 'jira_results.xlsx'

    # Define the column headers
    column_headers = ['Key', 'Summary', 'Description', 'URL']

    # Create a DataFrame from the issue data
    df = pd.DataFrame(issue_data, columns=column_headers)

    # Save the DataFrame to Excel
    df.to_excel(excel_file, index=False)

    print(f"Jira issues saved in '{excel_file}'.")
else:
    print(f"Failed to retrieve Jira issues. Status code: {response.status_code}")

