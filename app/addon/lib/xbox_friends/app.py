import sys

from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.common.exceptions import AuthenticationException
from aiohttp import ClientResponseError, ClientSession
#import xbox
import asyncio


"""
For doing authentication, see xbox/webapi/scripts/authenticate.py
"""
tokens = "tokens.json"

async def test():
    async with ClientSession() as session:
        auth_mgr = AuthenticationManager(
          session, args.client_id, args.client_secret, ""
        )

        with open(args.tokens, mode="r") as f:
            tokens = f.read()
        auth_mgr.oauth = OAuth2TokenResponse.parse_raw(tokens)
        try:
            auth_mgr.refresh_tokens()
        except ClientResponseError:
          print("Could not refresh tokens")
          sys.exit(-1)

        with open(args.tokens, mode="w") as f:
            f.write(auth_mgr.oauth.json())

        xbl_client = XboxLiveClient(auth_mgr)

        # Some example API calls

        # Get friendslist
        friendslist = await xbl_client.people.get_friends_own()

        # Get presence status (by list of XUID)
        presence = await xbl_client.presence.get_presence_batch(["12344567687845", "453486346235151"])

        # Get messages
        messages = await xbl_client.message.get_inbox()

        # Get profile by GT
        profile = await xbl_client.profile.get_profile_by_gamertag("SomeGamertag")


asyncio.run(test())