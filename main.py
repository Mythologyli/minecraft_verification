from io import BytesIO

import requests
from PIL import Image


class Player:
    def __init__(self, minecraft_id: str, minecraft_name: str):
        self.minecraft_id = minecraft_id
        self.minecraft_name = minecraft_name

    def get_body(self):
        res = requests.get(f"https://mc-heads.net/body/{self.minecraft_id}/128.png")
        return Image.open(BytesIO(res.content))


def get_player_from_code(code: str) -> Player:
    res = requests.post(
        url="https://login.live.com/oauth20_token.srf",
        data={
            "client_id": "00000000402b5328",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "https://login.live.com/oauth20_desktop.srf",
            "scope": "service::user.auth.xboxlive.com::MBI_SSL"
        }
    )

    if res.status_code != 200:
        raise ValueError(f"Wrong code: {code}")

    access_token = res.json()["access_token"]

    res = requests.post(
        url="https://user.auth.xboxlive.com/user/authenticate",
        json={
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token
            },
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT"
        }
    )

    if res.status_code != 200:
        raise ValueError(f"Wrong code: {code}")

    xbl_token = res.json()["Token"]
    uhs = res.json()["DisplayClaims"]["xui"][0]["uhs"]

    res = requests.post(
        url="https://xsts.auth.xboxlive.com/xsts/authorize",
        json={
            "Properties": {
                "SandboxId": "RETAIL",
                "UserTokens": [xbl_token]
            },
            "RelyingParty": "rp://api.minecraftservices.com/",
            "TokenType": "JWT"
        }
    )

    if res.status_code != 200:
        raise ValueError(f"Wrong code: {code}")

    xsts_token = res.json()["Token"]

    res = requests.post(
        url="https://api.minecraftservices.com/authentication/login_with_xbox",
        json={
            "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
        }
    )

    if res.status_code != 200:
        raise ValueError(f"Wrong code: {code}")

    minecraft_access_token = res.json()["access_token"]

    res = requests.get(
        url="https://api.minecraftservices.com/minecraft/profile",
        headers={
            "Authorization": f"Bearer {minecraft_access_token}"
        }
    )

    if res.status_code != 200:
        raise ValueError(f"Wrong code: {code}")

    minecraft_id = res.json()["id"]
    minecraft_name = res.json()["name"]

    return Player(minecraft_id, minecraft_name)


def main():
    print("Open this link in your browser:")
    print(
        "https://login.live.com/oauth20_authorize.srf?client_id=00000000402b5328&response_type=code"
        "&scope=service%3A%3Auser.auth.xboxlive.com%3A%3AMBI_SSL&"
        "redirect_uri=https%3A%2F%2Flogin.live.com%2Foauth20_desktop.srf"
    )

    redirect_url = input("Enter the redirect URL: ")

    try:
        code = redirect_url.split("code=")[1].split("&")[0]
    except IndexError:
        print(f"Wrong redirect URL: {redirect_url}")
        return

    try:
        player = get_player_from_code(code)
    except ValueError as e:
        print(e)
        return

    print(player.minecraft_id)
    print(player.minecraft_name)

    player.get_body().show()


if __name__ == '__main__':
    main()
