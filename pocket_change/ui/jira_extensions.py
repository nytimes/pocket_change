from pocket_change.auth import PocketChangeUser
from flask import g


@PocketChangeUser.authenticator
def jira_auth(user):
    
    if g.jira.verify_credentials(user.name, user.password):
        # If the user already exists in the database,
        # update their password to match what authenticated
        # in Jira to keep password in Pocket Change in sync
        # with password in Jira.
        if (hasattr(user, 'user') and user.user
            and hasattr(user.user, 'password_crypt')):
            user.user.password = user.password
        return True
    return False