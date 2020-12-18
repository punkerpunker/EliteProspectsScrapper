import requests
from stem import Signal
from stem.control import Controller


class Tor:
    password = "password"

    def __init__(self, session):
        self.session = session

    @classmethod
    def get_session(cls):
        session = requests.session()
        # Tor uses the 9050 port as the default socks port
        session.proxies = {'http':  'socks5://127.0.0.1:9050',
                           'https': 'socks5://127.0.0.1:9050'}
        return cls(session)

    @staticmethod
    def renew_connection():
        with Controller.from_port(port=9051) as controller:
            controller.authenticate(password="password")
            controller.signal(Signal.NEWNYM)

    @staticmethod
    def get_ip():
        session = Tor.get_session()
        return session.session.get("http://httpbin.org/ip").text
