############################################################################################
# Last updated: 5/10/2025
# Script to look through user, group, and policies
# 1. Get Access Token
# 2. User/Group: Get User's Groups & Permissions
# 3. User/Group: Get Users in Group (Enter Group ID)
# 4. Group: Get Policies for a Group
# 5. Group: Look up Group by ID or Name
# 6. Policy: Bind a Policy to a Group
# 7. Policy: Get Policy metadata by name
# 8. Policy: Get Policy metadata by ID
# 9. Exit
# Owner: Christian.Yap@dynatrace.com
############################################################################################
import requests
import threading
import time
from tabulate import tabulate
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Constants
CLIENT_ID = "CHANGEME" # Generated from your OAuth
CLIENT_SECRET = "CHANGEME" # Generated from your OAuth
ACCOUNT_ID = "CHANGEME"  # Dynatrace account ID
ENVIRONMENT_ID = "CHANGEME"  # Hardcoded environment ID
DEFAULT_GROUP_ID = "CHANGEME"  # Default example group ID

# Global variable to store the access token
access_token = None
token_refresh_thread = None
stop_token_refresh = False


############################################################################################
## Menu Option 1: Generate New SSO
############################################################################################
def get_token(client_id, client_secret):
    """Retrieve an access token from Dynatrace SSO."""
    url = "https://sso.dynatrace.com/sso/oauth2/token"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "account-idm-read account-idm-write iam-policies-management iam:bindings:read iam:effective-permissions:read",
        "urn": f"dtaccount:{ACCOUNT_ID}"
    }

    response = requests.post(url, headers=headers, data=data, verify=False)
    
    if response.status_code == 200:
        global access_token
        access_token = response.json().get("access_token")
        print(f"\nAccess Token Retrieved: \n{access_token}\n")
        return access_token
    else:
        print(f"\nFailed to get token. Status Code: {response.status_code}, Response: {response.text}\n")
        return None

############################################################################################
## Automatically refresh token once a token is generated
############################################################################################
def auto_refresh_token():
    """Automatically refreshes the access token every 4 minutes."""
    global access_token, stop_token_refresh
    while not stop_token_refresh:
        time.sleep(240)  # Wait 4 minutes
        if access_token:  # Only refresh if we already have a token
            print("\nRefreshing Access Token...\n")
            get_token(CLIENT_ID, CLIENT_SECRET)

def start_token_refresh_thread():
    """Starts the background thread to refresh the token."""
    global token_refresh_thread, stop_token_refresh
    if token_refresh_thread is None or not token_refresh_thread.is_alive():
        stop_token_refresh = False
        token_refresh_thread = threading.Thread(target=auto_refresh_token, daemon=True)
        token_refresh_thread.start()

############################################################################################
## Menu Option 2: Get User's group and permissions
############################################################################################
def get_user_groups_and_permissions(access_token, account_id, environment_id):
    """Retrieve a user's groups and list all their associated permissions."""
    
    email = input("\nEnter the User's Email: ").strip()
    encoded_email = email.replace("@", "%40")  # Encoding '@' for API URL

    url = f"https://api.dynatrace.com/iam/v1/accounts/{account_id}/users/{encoded_email}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        user_data = response.json()
        groups = user_data.get("groups", [])

        if not groups:
            print(f"\n User '{email}' is not assigned to any groups.")
            return

        print(f"\n User '{email}' is a member of the following groups:\n")
        table_data = [[group["uuid"], group["groupName"]] for group in groups]
        print(tabulate(table_data, headers=["Group UUID", "Group Name"], tablefmt="grid"))

        # Store permissions in a list
        all_permissions = []

        print("\n🔎 Fetching policies and permissions for each group...\n")

        # Loop through each group to get policies
        for group in groups:
            group_id = group["uuid"]
            group_name = group["groupName"]

            print(f"\n🔹 Checking Policies for Group: {group_name} ({group_id})\n")
            policies = get_policies_for_group(access_token, account_id, environment_id, group_id, return_policies=True)

            if policies:
                for policy in policies:
                    policy_uuid = policy["policyUuid"]
                    level_type = policy["levelType"]
                    level_id = policy["levelId"]

                    # Fetch permissions for this policy
                    permissions = get_permissions_for_policy(access_token, policy_uuid, level_type, level_id, account_id, environment_id)

                    # Store results
                    all_permissions.extend(permissions)

        # Print the final permissions table
        if all_permissions:
            print("\n Final List of User Permissions:\n")
            print(tabulate(all_permissions, headers=["Policy UUID", "Level Type", "Level ID", "Effect", "Permission", "Conditions"], tablefmt="grid"))
        else:
            print("\n No permissions found for this user.")

    else:
        print(f"\n Failed to retrieve user groups. Status Code: {response.status_code}, Response: {response.text}\n")

############################################################################################
## Menu Option 3: Get Users in Group
############################################################################################
def get_users_in_group(access_token, account_id):
    """Retrieve users in a specific group."""
    group_id = input("\nEnter the Group ID: ").strip() or DEFAULT_GROUP_ID

    url = f"https://api.dynatrace.com/iam/v1/accounts/{account_id}/groups/{group_id}/users"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        users_data = response.json()
        if "items" in users_data and users_data["items"]:
            print("\n Users in Group:")
            user_table = [[user["uid"], user["email"], user["name"], user["surname"]] for user in users_data["items"]]
            print(tabulate(user_table, headers=["User ID", "Email", "First Name", "Last Name"], tablefmt="grid"))
        else:
            print("\n No users found in this group.")
    else:
        print(f"\n Failed to get users. Status Code: {response.status_code}, Response: {response.text}\n")

############################################################################################
## Menu Option 4: Geta group's policies
############################################################################################
def get_policies_for_group(access_token, account_id, environment_id, group_id=None, return_policies=False, is_from_menu=False):
    """Retrieve and display policies for a user group from all three levels (Global, Account, Environment).
    
    - If called from the menu (Option #4), prompt the user for a Group ID and display the results.
    - Otherwise, use the provided `group_id` (e.g., when calling from `get_user_groups_and_permissions`).
    """
    
    if is_from_menu:  # Only prompt for Group ID if coming from the menu
        group_id = input("\nEnter the Group ID: ").strip()
        if not group_id:
            print("\n No Group ID provided. Exiting...")
            return None

    if not group_id:
        print("\n No valid Group ID found. Exiting...")
        return None

    scopes = ["global", f"account/{account_id}", f"environment/{environment_id}"]
    policies = []

    for scope in scopes:
        scope_display = "Global" if scope == "global" else "Account" if "account" in scope else "Environment"
        print(f"\n🔍 Checking {scope_display} policies for Group {group_id}...\n")

        url = f"https://api.dynatrace.com/iam/v1/repo/{scope}/bindings/groups/{group_id}?details=true"
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers, verify=False)

        if response.status_code == 200:
            policies_data = response.json()
            policy_details = policies_data.get("bindingsDetails", [])

            if policy_details:
                policies.extend(policy_details)  # Store policies for later use
            else:
                print(f"\n No {scope_display} policies found for Group {group_id}.")

        else:
            print(f"\n Failed to get {scope_display} policies. Status Code: {response.status_code}, Response: {response.text}\n")

    # If called from the menu, print the policies in a structured format
    if is_from_menu and policies:
        print("\n Retrieved Policies for the Group:\n")

        table_data = []
        for policy in policies:
            policy_uuid = policy.get("policyUuid", "N/A")
            level_type = policy.get("levelType", "N/A")
            level_id = policy.get("levelId", "N/A")
            groups = ", ".join(policy.get("groups", [])) if policy.get("groups") else "None"

            # Extract parameters, metadata, and boundaries
            parameters = policy.get("parameters", {})
            param_str = ", ".join([f"{key}: {value}" for key, value in parameters.items()]) if parameters else "None"

            metadata = policy.get("metadata", {})
            metadata_str = ", ".join([f"{key}: {value}" for key, value in metadata.items()]) if metadata else "None"

            boundaries = policy.get("boundaries", [])
            boundary_str = ", ".join(boundaries) if boundaries else "None"

            table_data.append([policy_uuid, level_type, level_id, groups, param_str, metadata_str, boundary_str])

        print(tabulate(table_data, headers=["Policy UUID", "Level Type", "Level ID", "Groups", "Parameters", "Metadata", "Boundaries"], tablefmt="grid"))

    return policies if return_policies else None
        

############################################################################################
## Menu Option 5: Lookup group by ID or Name
############################################################################################
def lookup_group_by_id_or_name(access_token, account_id):
    """Look up a group by its UUID or name."""
    url = f"https://api.dynatrace.com/iam/v1/accounts/{account_id}/groups"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        groups_data = response.json().get("items", [])
        if not groups_data:
            print("\n No groups found.")
            return

        print("\nChoose search method:")
        print("1. Search by Group UUID")
        print("2. Search by Group Name")
        search_choice = input("Enter your choice: ").strip()

        if search_choice == "1":
            group_uuid = input("\nEnter Group UUID: ").strip()
            matching_groups = [g for g in groups_data if g.get("uuid") == group_uuid]

            if matching_groups:
                print(f"\n Group UUID '{group_uuid}' matches Group Name: {matching_groups[0].get('name', 'Unknown')}")
            else:
                print(f"\n No group found with UUID '{group_uuid}'.")

        elif search_choice == "2":
            group_name = input("\nEnter Group Name: ").strip()
            matching_groups = [g for g in groups_data if g.get("name", "").lower() == group_name.lower()]

            if matching_groups:
                print(f"\n Group Name '{group_name}' matches Group UUID: {matching_groups[0].get('uuid', 'Unknown')}")
            else:
                print(f"\n No group found with Name '{group_name}'.")

        else:
            print("\n Invalid choice. Please enter '1' or '2'.")
    
    else:
        print(f"\n Failed to retrieve groups. Status Code: {response.status_code}, Response: {response.text}\n")

############################################################################################
## Menu Option 6: Bind a policy to a group
############################################################################################      
def bind_policy_to_group(access_token, environment_id, account_id):
    """Bind a policy to a group."""
    print("\n🔗 Bind a Policy to a Group")

    group_id = input("Enter Group ID: ").strip()
    policy_id = input("Enter Policy ID: ").strip()

    # Collect parameters
    parameters = {}
    while True:
        key = input("Enter parameter key (or press Enter to skip): ").strip()
        if not key:
            break
        value = input(f"Enter value for '{key}': ").strip()
        parameters[key] = value
        add_more = input("Add another parameter? (yes/no): ").strip().lower()
        if add_more != "yes":
            break

    # Collect metadata
    metadata = {}
    while True:
        key = input("Enter metadata key (or press Enter to skip): ").strip()
        if not key:
            break
        value = input(f"Enter value for '{key}': ").strip()
        metadata[key] = value
        add_more = input("Add another metadata entry? (yes/no): ").strip().lower()
        if add_more != "yes":
            break

    # Collect multiple boundaries
    boundaries = []
    while True:
        boundary = input("Enter a Boundary ID (or press Enter to skip): ").strip()
        if not boundary:
            break
        boundaries.append(boundary)
        add_more = input("Add another boundary? (yes/no): ").strip().lower()
        if add_more != "yes":
            break

    url = f"https://api.dynatrace.com/iam/v1/repo/environment/{environment_id}/bindings/{policy_id}/{group_id}"
    headers = {
        "accept": "*/*",
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "parameters": parameters,
        "metadata": metadata,
        "boundaries": boundaries  # Now supports multiple boundary IDs
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)

    if response.status_code in [200, 201, 204]:  # Accepting 204 as a success
        print("\n Policy successfully bound to group!")

        # Call "Get Policies for a Group" to validate binding
        print("\n Validating binding by retrieving updated group policies...\n")
        get_policies_for_group(access_token, account_id, environment_id, group_id)
    else:
        print(f"\n Failed to bind policy. Status Code: {response.status_code}, Response: {response.text}\n")

############################################################################################
## Menu Option 7: Get Policy permissions by name
############################################################################################ 
def get_all_policies(access_token, environment_id,account_id):
    print("\nSelect policy scope to retrieve from:")
    print("1. Global")
    print("2. Account")
    print("3. Environment")
    choice = input("Enter your choice (1/2/3): ").strip()

    print("\nOptional: Enter policy name to filter by (or press Enter to list all):")
    policy_name = input("Policy name: ").strip()

    if choice == "1":
        scope_label = "global"
        url = "https://api.dynatrace.com/iam/v1/repo/global/global/policies"
    elif choice == "2":
        scope_label = f"account/{account_id}"
        url = f"https://api.dynatrace.com/iam/v1/repo/account/{account_id}/policies"
    elif choice == "3":
        scope_label = f"environment/{environment_id}"
        url = f"https://api.dynatrace.com/iam/v1/repo/environment/{environment_id}/policies"
    else:
        print("\n Invalid choice.")
        return

    if policy_name:
        url += f"?name={policy_name}"

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        policies = response.json().get("policies", [])

        if not policies:
            print(f"\n No policies found at {scope_label} level.")
            return

        print(f"\n Policies at {scope_label} level:\n")
        table_data = [
            [p.get("uuid", "N/A"), p.get("name", "N/A"), p.get("description", "N/A"), p.get("category", "N/A")]
            for p in policies
        ]
        print(tabulate(table_data, headers=["Policy UUID", "Name", "Description", "Category"], tablefmt="grid"))
    else:
        print(f"\n Failed to retrieve policies. Status Code: {response.status_code}, Response: {response.text}")

############################################################################################
## Menu Option 8: Get Policy metadata by ID
############################################################################################  
def get_policy_metadata(access_token, account_id):
    policy_id = input("\nEnter the Policy ID: ").strip()
    if not policy_id:
        print("\n No policy ID provided.")
        return

    url = f"https://api.dynatrace.com/iam/v1/repo/account/{account_id}/policies/{policy_id}"
    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        data = response.json()
        print("\nPolicy Metadata:\n")
        print(f"UUID:        {data.get('uuid')}")
        print(f"Name:        {data.get('name')}")
        print(f"Description: {data.get('description')}")
        print(f"Category:    {data.get('category')}")
        print("\nStatement Query:\n----------------")
        print(data.get("statementQuery", "N/A"))

        print("\nStatements:")
        for stmt in data.get("statements", []):
            print(f"  - Effect: {stmt.get('effect')}")
            for perm in stmt.get("permissions", []):
                print(f"    • Permission: {perm}")
            for cond in stmt.get("conditions", []):
                print(f"    • Condition: {cond.get('name')} {cond.get('operator')} {', '.join(cond.get('values', []))}")
    else:
        print(f"\n Failed to retrieve policy metadata. Status Code: {response.status_code}, Response: {response.text}")

############################################################################################
## Menu Option 7: Helper for 7/8
############################################################################################  
def get_permissions_for_policy(access_token, policy_uuid, level_type, level_id, account_id, environment_id):
    """Retrieve detailed permissions for a policy based on its scope (global, account, environment)."""
    
    if level_type == "global":
        url = f"https://api.dynatrace.com/iam/v1/repo/global/global/policies/{policy_uuid}"
    elif level_type == "account":
        url = f"https://api.dynatrace.com/iam/v1/repo/account/{account_id}/policies/{policy_uuid}"
    elif level_type == "environment":
        url = f"https://api.dynatrace.com/iam/v1/repo/environment/{environment_id}/policies/{policy_uuid}"
    else:
        return None

    headers = {
        "accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        policy_data = response.json()
        statements = policy_data.get("statements", [])
        
        permissions = []
        for statement in statements:
            effect = statement.get("effect", "N/A")
            permission_list = statement.get("permissions", [])
            conditions = statement.get("conditions", [])

            for permission in permission_list:
                condition_str = "None"
                if conditions:
                    condition_str = "; ".join([
                        f"{cond['name']} {cond['operator']} {', '.join(cond['values'])}"
                        for cond in conditions
                    ])

                permissions.append([policy_uuid, level_type, level_id, effect, permission, condition_str])

        return permissions
    else:
        print(f"\n Failed to get permissions for policy {policy_uuid} ({level_type}). Response: {response.text}\n")
        return []

############################################################################################
## Main Function
############################################################################################        
def main():
    global access_token, stop_token_refresh

    while True:
        print("\n--- Dynatrace API Menu ---")
        print("1. Get Access Token")
        print("2. User/Group: Get User's Groups & Permissions") 
        print("3. User/Group: Get Users in Group (Enter Group ID)")
        print("4. Group: Get Policies for a Group")
        print("5. Group: Look up Group by ID or Name")
        print("6. Policy: Bind a Policy to a Group")
        print("7. Policy: Get Policy metadata by name")
        print("8. Policy: Get Policy metadata by ID")           
        print("9. Exit")

        user_input = input("Enter your choice: ").strip()

        if user_input == "1":
            access_token = get_token(CLIENT_ID, CLIENT_SECRET)
            if access_token:
                start_token_refresh_thread()
        elif user_input == "2":
            if access_token:
                get_user_groups_and_permissions(access_token, ACCOUNT_ID, ENVIRONMENT_ID)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "3":
            if access_token:
                get_users_in_group(access_token, ACCOUNT_ID)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "4":
            if access_token:
                get_policies_for_group(access_token, ACCOUNT_ID, ENVIRONMENT_ID, is_from_menu=True)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "5":
            if access_token:
                lookup_group_by_id_or_name(access_token, ACCOUNT_ID)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "6":
            if access_token:
                bind_policy_to_group(access_token, ENVIRONMENT_ID, ACCOUNT_ID)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "7":
            if access_token:
                get_all_policies(access_token, ENVIRONMENT_ID, ACCOUNT_ID)
            else:
                print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "8":
                if access_token:
                    get_policy_metadata(access_token, ACCOUNT_ID)
                else:
                    print("\n You need to get an access token first. Choose option 1.")
        elif user_input == "9":
            stop_token_refresh = True
            print("\nExiting program. Goodbye!\n")
            break
        else:
            print("\nInvalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()
