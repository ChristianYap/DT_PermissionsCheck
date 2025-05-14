# Readme

Script to look through user, group, and policies
1. Get Access Token
2. User/Group: Get User's Groups & Permissions
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
   - To get started, you must get an access (Option #1). Token will automatically refresh before expiring as long as the script is running.
  

## Options


  2. User/Group: Get User's Groups & Permissions (Now Includes Permissions!) - This will pull permissions on a global, account, and environment level.

  Input: User Email
     
  ![Image](https://github.com/user-attachments/assets/701b36ca-f764-4957-b276-86d73fc6619f)

  Sample Output:
  
  ![image](https://github.com/user-attachments/assets/72e64de9-75c6-4aea-831f-face58c804d7)

  3. User/Group: Get Users in Group (Enter Group ID)

  Input: Group ID

  ![image](https://github.com/user-attachments/assets/9f9d2bbf-d6b3-42cf-a134-287f179fd27f)


  4. Group: Get Policies for a Group

  Input: Group ID

  Output:

  ![image](https://github.com/user-attachments/assets/45f0a273-b0a8-48fc-977b-d3c9f1a28451)


  5. Group: Look up Group by ID or Name

  Input: Group ID or Group Name

  Output:Returns group ID if you look by group name, and vice versa. 

  6. Policy: Bind a Policy to a Group

  Input: Group ID & Policy ID, as well as parameters/metadata/boundaries.

  ![image](https://github.com/user-attachments/assets/8fe7b874-dbb2-4983-8897-be049b81534a)

  7. Policy: Get Policy metadata by name

  Input: Policy Name, followed by if you want to pull in global/account/environment-level policy rules.
  
  ![image](https://github.com/user-attachments/assets/cf7ca1ea-f68d-4232-9c71-de967e4c27aa)
  
  Output:
  ![image](https://github.com/user-attachments/assets/62417be4-4663-4a84-9a08-327c4dd74a9e)

  8. Policy: Get Policy metadata by ID

  Input: Policy ID, followed by if you want to pull in global/account/environment-level policy rules.

  Output: same as option #7.

  9. Exit
      Exits the script
   
