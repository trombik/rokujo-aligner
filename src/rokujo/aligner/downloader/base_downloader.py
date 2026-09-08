from abc import ABC
import logging

import curl_cffi

logger = logging.getLogger(__name__)


class ResponseError(Exception):
    pass


class BaseDownloader(ABC):
    impersonate = None

    def __init__(self):
        pass

    def fetch(self, url: str) -> str:
        try:
            r = curl_cffi.get(url, impersonate=self.impersonate)
        except Exception as e:
            raise e

        logger.debug(f"Request URL: {r.url}")
        logger.debug(f"Response status: {r.status_code}")
        response_header_text = "\n".join(
            f"{k.decode('utf-8')}: {v.decode('utf-8')}"
            for k, v in r.headers.raw
        )
        logger.debug(f"Response headers:\n{response_header_text}")
        if r.status_code < 200 or r.status_code > 300:
            raise ResponseError(
                f"Request failed with status code: ({r.status_code})"
            )
        return r.content.decode("utf-8")


class ChromeDownloader(BaseDownloader):
    impersonate = "chrome150"


class FirefoxDownloader(BaseDownloader):
    impersonate = "firefox147"


class EdgeDownloader(BaseDownloader):
    impersonate = "edge101"
