# coding: utf-8
import base64
import os
import time
import requests
from requests_futures.sessions import FuturesSession

# When the keys are not already stored in environment variables
# This is used when running locally (testing)
if "VT_KEY" not in list(os.environ.keys()) or "VT_SECRET" not in list(os.environ.keys()):
    with open("creds.txt") as f:
        key, secret, client_indent, client_version = f.readlines()
    os.environ["VT_KEY"] = key
    os.environ["VT_SECRET"] = secret


class Auth():
    def __init__(self, key, secret, scopes):
        if key == None or secret == None or scopes == None:
            raise TypeError("Usage: Auth(<key>, <secret>, [<scopes>])")

        if type(key) != str:
            raise TypeError("Expected str [key]")
        if type(secret) != str:
            raise TypeError("Expected str [secret]")
        if type(scopes) != list or len(scopes) == 0:
            raise TypeError("Expected list of ints [scopes]")

        self.__credentials = base64.b64encode(str.encode(f'{key}:{secret}')).decode("utf-8")
        self.scopes = scopes
        self.tokens = []
        self.last_token = 0


        # for scope in scopes:
        #     self.tokens.append(None)
        #     self.__renew_token(scope)
        self.__async_renew_token(scopes)

    # Renews one token
    def __renew_token(self, scope):
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.__credentials
        }
        url = f'https://api.vasttrafik.se/token?grant_type=client_credentials&scope=device_{scope}'
        response = requests.post(url, headers=header)
        response_dict = response.json()

        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f'{response.status_code} {response_dict.get("error_description")}')

        self.tokens[self.scopes.index(scope)] = ("Bearer " + response_dict.get("access_token"))
        return "Bearer " + response_dict.get("access_token")

    # Renews multiple tokens simultaneously
    def __async_renew_token(self, scopes):
        # Should only be used when starting the server and having to renew all tokens
        header = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": "Basic " + self.__credentials
        }
        url = "https://api.vasttrafik.se/token?grant_type=client_credentials&scope=device_"

        # Start a session for the async requests
        session = FuturesSession()
        reqs = []
        for scope in scopes:
            # Send the requests
            future = session.post(url + str(scope), headers=header)
            reqs.append(future)
            time.sleep(0.03) # Without this everything breaks

        responses = []
        for req in reqs:
            # Get the results
            r = req.result()
            if r.status_code != 200:
                raise requests.exceptions.HTTPError(f'{r.status_code} {r.get("error_description")}')

            self.tokens.append("Bearer " + r.json().get("access_token"))

    # Method called when a token is needed for a request
    # It cycles through them so Västtrafik does not complain about sending too many requests
    def get_token(self, scope_=None):
        if scope_:
            return self.tokens[self.tokens.index(scope_)], scope_
        else:
            self.last_token = (self.last_token + 1) % len(self.scopes)
            token = self.tokens[self.last_token]
            scope = self.scopes[self.last_token]

            return token, scope

    # Check normal synchronous responses
    def check_response(self, response, scope):
        if response.status_code == 401:
            print("Renewing token", scope)
            token = self.__renew_token(scope)
            # token, scope_ = self.get_token(scope)

            header = {"Authorization": token}
            response = requests.get(response.url, headers=header)

        response_dict = response.json()
        if response.status_code != 200:
            raise requests.exceptions.HTTPError(f'{response.status_code} {response_dict.get("error_description")}')

        return response

    # Check asynchronous responses where there are multiple ones
    def check_responses(self, response_list, scope):
        fine = True
        for resp in response_list:
            # Check for any errors
            if resp.status_code != 200:
                fine = False

        if fine:
            return response_list
        else:
            print("Renewing token " + str(scope))
            token = self.__renew_token(scope)
            header = {"Authorization": token}

            # Retry!
            session = FuturesSession()
            reqs = []
            for resp in response_list:
                # Send the new requests
                url = resp.url
                reqs.append(session.get(url, headers=header))
                time.sleep(0.01)

            # Get the results
            resps = []
            for req in reqs:
                resps.append(req.result())

            if resps[0].status_code != 200:
                raise requests.exceptions.HTTPError(f'{resps[0].status_code} {resps[0].reason}')

            return resps


class Reseplaneraren():
    def __init__(self, auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth

    # ----------- UNUSED METHODS BELOW -----------

    # def trip(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/trip"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def location_nearbyaddress(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.nearbyaddress"
    #     kwargs["format"] = "json"
 
    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def location_nearbystops(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.nearbystops"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def location_allstops(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.allstops"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def location_name(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/location.name"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def systeminfo(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/systeminfo"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def livemap(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/livemap"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def journeyDetail(self, ref):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/journeyDetail"

    #     response = requests.get(url, headers=header, params={"ref":ref})
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def geometry(self, ref):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/geometry"

    #     response = requests.get(url, headers=header, params={"ref":ref})
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # Sends one request at a time
    def departureBoard(self, **kwargs):
        token, scope = self.auth.get_token()
        header = {"Authorization": token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/departureBoard"
        kwargs["format"] = "json"

        response = requests.get(url, headers=header, params=kwargs)
        response = self.auth.check_response(response, scope)

        return response.json()
        
    # Sends multiple requests simultaneously
    def asyncDepartureBoards(self, stops, **kwargs):
        token, scope = self.auth.get_token()
        header = {"Authorization": token}
        url = "https://api.vasttrafik.se/bin/rest.exe/v2/departureBoard"
        kwargs["format"] = "json"

        # Start a session for the async requests
        session = FuturesSession()
        reqs = []
        for stop in stops:
            # Send the requests
            params = kwargs
            params["id"] = stop
            future = session.get(url, headers=header, params=params)
            reqs.append(future)
            time.sleep(0.02) # Without this everything breaks

        responses = []
        for req in reqs:
            # Get the results
            r = req.result()
            responses.append(r)

        # Check for errors
        resp = self.auth.check_responses(responses, scope)

        output = []
        for response in resp:
            output.append(response.json())

        return output


    # def arrivalBoard(self, **kwargs):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     url = "https://api.vasttrafik.se/bin/rest.exe/v2/arrivalBoard"
    #     kwargs["format"] = "json"

    #     response = requests.get(url, headers=header, params=kwargs)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


    # def request(self, url):
    #     token, scope = self.auth.get_token()
    #     header = {"Authorization": token}
    #     response = requests.get(url, headers=header)
    #     response = self.auth.check_response(response, scope)

    #     return response.json()


class TrafficSituations():
    def __init__(self, auth):
        if type(auth) != Auth:
            raise TypeError("Expected Auth object")
        self.auth = auth
        self.url = "https://api.vasttrafik.se/ts/v1/traffic-situations"

    
    def __get(self, url):
        token, scope = self.auth.get_token()
        header = {"Authorization": token}
        response = requests.get(url, headers=header)
        response = self.auth.check_response(response, scope)

        return response.json()

    # Get all the disruptions
    def trafficsituations(self):
        url = self.url
        return self.__get(url)


    # def stoppoint(self, gid):
    #     url = self.url + f'/stoppoint/{gid}'
    #     return self.__get(url)


    # def situation(self, gid):
    #     url = self.url + f'/{gid}'
    #     return self.__get(url)


    # def line(self, gid):
    #     url = self.url + f'/line/{gid}'
    #     return self.__get(url)


    # def journey(self, gid):
    #     url = self.url + f'/journey/{gid}'
    #     return self.__get(url)


    # def stoparea(self, gid):
    #     url = self.url + f'/stoparea/{gid}'
    #     return self.__get(url)


if __name__ == "__main__":
    with open("credentials.csv", "r") as f:
        key, secret = f.read().split(",")

    auth = Auth(key, secret, 0)
    ts = TrafficSituations(auth)
    # vt = Reseplaneraren(auth)

    s = ts.trafficsituations()[0]
    print(s)
    # stop1 = vt.location_name(input="Kungssten").get("LocationList").get("StopLocation")[0].get("id")
    # print(ts.stoppoint(9022014001040002))
    # stop2 = vt.location_name(input="Kampenhof").get("LocationList").get("StopLocation")[0].get("id")
    # print(vt.trip(originId=stop1, destId=stop2, date=20190215, time="15:24"))