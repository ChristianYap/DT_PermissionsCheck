# ReadME

Script to look through user, group, and policies
1. Get Access Token
2. User/Group: Get User's Groups & Permissions (Now Includes Permissions!)
3. User/Group: Get Users in Group (Enter Group ID)
4. Group: Get Policies for a Group
5. Group: Look up Group by ID or Name
6. Policy: Bind a Policy to a Group
7. Policy: Get Policy metadata by name
8. Policy: Get Policy metadata by ID
9. Exit

## Step 1: Create an OAuth Token with the following permissions:
account-idm-read, iam:users:read, iam:groups:read, account-env-read, account-idm-write, account-env-write, iam-policies-management, iam:policies:write, iam:policies:read, iam:bindings:write, iam:bindings:read, iam:effective-permissions:read, iam:service-users:use, iam:limits:read

## Step 2: Using the script
1. Update the following global variables:
  CLIENT_ID - Generated from OAuth
  CLIENT_SECRET - Generated from OAuth
  ACCOUNT_ID - Your DT Account
  ENVIRONMENT_ID - Your SaaS environment
  DEFAULT_GROUP_ID - You can leave this default ""

2. Run the script, generate a token
