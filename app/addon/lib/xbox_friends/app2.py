import sys
import json
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.common.exceptions import AuthenticationException
from xbox.webapi.api.provider.presence import PresenceLevel


"""
For doing authentication in code, see xbox/webapi/scripts/authenticate.py
or for OAUTH via web-brower, see xbox/webapi/scripts/browserauth.py



# Token save location: If tokenfile is not provided via cmdline, fallback
# of <appdirs.user_data_dir>/tokens.json is used as save-location
#
# Specifically:
# Windows: C:\\Users\\<username>\\AppData\\Local\\OpenXbox\\xbox
# Mac OSX: /Users/<username>/Library/Application Support/xbox/tokens.json
# Linux: /home/<username>/.local/share/xbox
#
# For more information, see: https://pypi.org/project/appdirs and module: xbox.webapi.scripts.constants

xbox-authenticate --tokens tokens.json --email no@live.com --password abc123

# NOTE: If no credentials are provided via cmdline, they are requested from stdin
xbox-authenticate --tokens tokens.json

# If you have a shell compatible with ncurses, you can use the Terminal UI app
xbox-auth-ui --tokens tokens.json
"""

try:
  auth_mgr = AuthenticationManager.from_file('tokens/tokens.json')
except FileNotFoundError as e:
  print(
    'Failed to load tokens from \'{}\'.\n'
    'ERROR: {}'.format(e.filename, e.strerror)
  )
  sys.exit(-1)

try:
  auth_mgr.authenticate(do_refresh=True)
except AuthenticationException as e:
  print('Authentication failed! Err: %s' % e)
  sys.exit(-1)

xbl_client = XboxLiveClient(auth_mgr.userinfo.userhash, auth_mgr.xsts_token.jwt, auth_mgr.userinfo.xuid)

# Some example API calls

# Get friendslist
friendslist = xbl_client.people.get_friends_own()
resp = friendslist.json()
print(resp)
people = [o["xuid"] for o in resp["people"]]
print(people)

# Get presence status (by list of XUID)
#presence = xbl_client.presence.get_presence_batch(people)
#presence = xbl_client.presence.get_presence_batch(people, presence_level=PresenceLevel.ALL)

for p in people:
  presence = xbl_client.presence.get_presence(p, presence_level=PresenceLevel.ALL)
  resp = presence.json()
  print("presence", resp)

profile = xbl_client.profile.get_profiles(people)
resp = profile.json()
print("profile", resp)

profiles = profile.json()["profileUsers"]
for profile in profiles:
  profile['presence'] = xbl_client.presence.get_presence(profile['id'], presence_level=PresenceLevel.ALL).json()

import ipdb
ipdb.set_trace()






# Get messages
#messages = xbl_client.message.get_message_inbox()

# Get profile by GT
#profile = xbl_client.profile.get_profile_by_gamertag('SomeGamertag')