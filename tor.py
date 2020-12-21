import requests
from stem import Signal
from stem.control import Controller

tor_ip = 'localhost'
tor_port = 9050
tor_password = 'tttBBB777'
tor_controller_port = 9051


class Tor:
    proxies = {'http':  f'socks5://{tor_ip}:{tor_port}',
               'https': f'socks5://{tor_ip}:{tor_port}'}

    def __init__(self, session):
        self.session = session

    @classmethod
    def get_session(cls):
        session = requests.session()
        # Tor uses the 9050 port as the default socks port
        session.proxies = cls.proxies
        return cls(session)

    @staticmethod
    def renew_connection():
        with Controller.from_port(port=tor_controller_port) as controller:
            controller.authenticate(password=tor_password)
            controller.signal(Signal.NEWNYM)

    @staticmethod
    def get_ip():
        session = Tor.get_session()
        return session.session.get("http://httpbin.org/ip").text
