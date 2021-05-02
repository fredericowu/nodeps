from django.db import models
from xbox.webapi.api.client import XboxLiveClient
from xbox.webapi.authentication.manager import AuthenticationManager
from xbox.webapi.common.exceptions import AuthenticationException
from xbox.webapi.api.provider.presence import PresenceLevel
import datetime
from django.utils import timezone
import os


TOKEN_FILE = os.path.dirname(__file__) + "/lib/xbox_friends/tokens/tokens.json"


class XboxFriends(models.Model):
    xuid = models.CharField(null=True, default=None, max_length=255)
    state = models.CharField(null=True, default=None, max_length=255)
    lastseen_titlename = models.CharField(null=True, default=None, max_length=255)
    lastseen_timestamp = models.DateTimeField(default=None, null=True)
    gamertag = models.CharField(null=True, default=None, max_length=255)
    realname = models.CharField(null=True, default=None, max_length=255)
    gamedisplayname = models.CharField(null=True, default=None, max_length=255)
    last_check = models.DateTimeField(auto_now=True)
    


    @classmethod
    def _get_settings(self, settings, name):
        return next(filter(lambda a: a["id"] == name, settings), {'value': None})["value"]

    @classmethod
    def generate_token(cls):
        user = os.getenv("XBOX_USER")
        password = os.getenv("XBOX_PASSWORD")
        os.system(f"echo xbox-authenticate --tokens  {TOKEN_FILE} --email {user} --password {password}")


    @classmethod
    def check_status(cls):
        auth_mgr = AuthenticationManager.from_file(TOKEN_FILE)
        try:
            auth_mgr.authenticate(do_refresh=True)
        except AuthenticationException:
            cls.generate_token()


        xbl_client = XboxLiveClient(auth_mgr.userinfo.userhash, auth_mgr.xsts_token.jwt, auth_mgr.userinfo.xuid)
        friendslist = xbl_client.people.get_friends_own().json()
        people = [o["xuid"] for o in friendslist["people"]]
        profiles = xbl_client.profile.get_profiles(people).json()["profileUsers"]

        status = {}
        for profile in profiles:
            profile['presence'] = xbl_client.presence.get_presence(profile['id'], presence_level=PresenceLevel.ALL).json()
            print(profile['presence'])

            xf, created = XboxFriends.objects.get_or_create(xuid=profile["id"])
            changed = created

            xf.gamertag = cls._get_settings(profile["settings"], "Gamertag")
            xf.realname = cls._get_settings(profile["settings"], "RealName")
            xf.gamedisplayname = cls._get_settings(profile["settings"], "GameDisplayName")

            new_state = profile["presence"]["state"]
            #new_state = "Online"
            if new_state != xf.state:
                changed = True
            xf.state = new_state

            if "lastSeen" in profile["presence"]:
                xf.lastseen_titlename = profile["presence"]["lastSeen"]["titleName"]
                xf.lastseen_timestamp = datetime.datetime.strptime(profile["presence"]["lastSeen"]["timestamp"].split(".")[0], '%Y-%m-%dT%H:%M:%S')
            else:
                xf.lastseen_timestamp = timezone.now()

            xf.save()

            print("{} is {}".format(xf.gamertag, xf.state))
            status[xf] = {
                'state': xf.state,
                'changed': changed,
                'gamertag': xf.gamertag,
                'title': xf.lastseen_titlename,
            }

        return status





