import os
import re
import subprocess
import time
from typing import Callable, Dict, Optional, Tuple
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import requests
import yt_dlp
import base64
from loguru import logger
from selenium.webdriver.common.by import By

from config_wandb import ConfigWandb
from scrape_title import get_title_with_openai_vision
from utils import create_driver, login, parse_youtube_url

def get_domain_from_url(
    url: str,
) -> str:
    domain = urlparse(url).netloc
    if "www." in domain:
        domain = domain.replace("www.", "")

    return domain
def decode_url(url):
    # Parse the URL
    
    parsed_url = urlparse(url)
    file_extensions_to_strip_query = [".mp3", ".wav", ".mp4", ".avi"]

    # Special processing for specific file extensions with query parameters (Azure SAS Tokens)
    if any(parsed_url.path.endswith(ext) for ext in file_extensions_to_strip_query):
        # Parse query parameters
        query_params = parse_qs(parsed_url.query)

        # Reconstruct the full URL without the query parameters
        new_url_components = parsed_url._replace(query="")
        new_url = urlunparse(new_url_components)
        return new_url

    # Preserve the existing logic for other cases

    # Parse the query parameters
    query_params = parse_qs(parsed_url.query)

    # Decode the referrer if it exists
    if "referrer" in query_params:
        encoded_referrer = query_params["referrer"][0]
        decoded_referrer_bytes = base64.urlsafe_b64decode(encoded_referrer + "==")
        decoded_referrer = decoded_referrer_bytes.decode("utf-8")
        query_params["referrer"] = [decoded_referrer]

    # Reconstruct the query string
    encoded_query = urlencode(query_params, doseq=True)

    # Reconstruct the full URL
    new_url_components = parsed_url._replace(query=encoded_query)
    new_url = urlunparse(new_url_components)

    return new_url

def download_from_past_stream(
    openai_completion_with_backoff: Callable,
    *,
    config_wandb: ConfigWandb,
    url: str,
    user_login: Dict[str, str],
    dir_data: str,
    file_name: str,
) -> Tuple[Optional[str], Optional[str]]:
    try:
        # Extract domain
        domain = get_domain_from_url(url)

        # Create Google Chrome driver
        driver = create_driver(dir_data=dir_data)

        # Go to URL
        driver.get(url)
        time.sleep(10)

        # Get title from webpage with OpenAI Vision model
        title = get_title_with_openai_vision(
            openai_completion_with_backoff,
            config_wandb=config_wandb,
            base64_image=driver.get_screenshot_as_base64(),
        )
        logger.info(f"Title extracted with OpenAI Vision: {title}")

        # Login to website
        login(
            driver,
            openai_completion_with_backoff,
            config_wandb=config_wandb,
            domain=domain,
            user_login=user_login,
        )
        time.sleep(2)

        # Live audio scraping
        video_url = driver.current_url
        media_exts = [".mp3", ".wav", ".mp4", ".avi", ".mkv", ".webm", ".aspx"]
        media_ext = os.path.splitext(urlparse(video_url).path)[1]
        if media_ext in media_exts:
            _, file_name = download_stream(
                video_url,
                file_name,
                dir_data,
                media_ext,
            )
            return file_name, title

        else:
            logger.info(f"Not direct video url-{video_url}")
            try:
                video_tag = driver.find_element(By.TAG_NAME, "video")
                logger.info("Found video tag in this page")
                try:
                    video_src = video_tag.find_element(
                        By.TAG_NAME,
                        "source",
                    ).get_attribute("src")

                except Exception:
                    video_src = None

                if video_src is None or video_src == "":
                    video_src = video_tag.get_attribute("src")
                path_url = decode_url(video_src)

                if path_url.endswith(".m3u8"):  # type: ignore
                    logger.info(path_url)
                    _, file_name = download_stream(
                        str(path_url),
                        file_name,
                        dir_data,
                        media_ext,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name, title

                media_ext = os.path.splitext(str(video_src))[1]
                filename_without_ext = os.path.splitext(file_name)[0]
                filename = filename_without_ext + media_ext
                is_download_successful, file_name = download_stream(
                    str(video_src),
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name, title

            except Exception:
                pass

            try:
                audio_tag = driver.find_element(By.TAG_NAME, "audio")
                logger.info("Found audio tag in this page")
                try:
                    audio_src = audio_tag.find_element(
                        By.TAG_NAME, "source"
                    ).get_attribute("src")
                except Exception:
                    audio_src = None

                if audio_src is None or audio_src == "":
                    audio_src = audio_tag.get_attribute("src")

                path_url = decode_url(audio_src)
                media_ext = os.path.splitext(path_url)[1]

                if path_url.endswith(".m3u8"):  # type: ignore
                    logger.info(path_url)
                    is_download_successful, file_name = download_stream(
                        str(path_url),
                        file_name,
                        dir_data,
                        media_ext,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name, title

                youtube_domains = [
                    "youtube.com",
                    "m.youtube.com",
                    "youtu.be",
                    "bilibili.com",
                ]
                for domain in youtube_domains:
                    if domain in str(audio_src):
                        logger.info("Source identified as YouTube")
                        try:
                            result = download_from_youtube(
                                str(audio_src), file_name, dir_data
                            )
                        except Exception as e:
                            logger.info(e)

                        if result == 1:
                            logger.info("Successfully downloaded")
                            driver.quit()
                            logger.info(filename, title)
                            return filename, title

                is_download_successful, file_name = download_stream(
                    path_url,
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name, title

                is_download_successful, file_name = download_stream(
                    str(audio_src),
                    file_name,
                    dir_data,
                    media_ext,
                )
                if is_download_successful:
                    driver.quit()
                    return file_name, title

            except Exception:
                pass

            for request in driver.requests:
                if "kvgo" in domain:
                    mp4_url_pattern = re.compile(
                        r".*\.mp4\?.*Expires=.*", re.IGNORECASE
                    )
                    if mp4_url_pattern.match(request.url):
                        _, file_name = download_stream(
                            request.url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name, title

                    continue

                if (
                    ("enlivenstream" in domain)
                    or ("vimeo" in domain)
                    or ("sohu" in domain)
                    or ("tenmeetings" in domain)
                ):
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)
                    if mp4_url_pattern.match(request.url):
                        url = request.url.split(".mp4", 1)[0] + ".mp4"
                        _, file_name = download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name, title

                    continue

                if "omnigage" in domain:
                    if "www.omnigage.io/api/" in request.url:
                        res = requests.get(request.url).json()
                        url = (
                            res.get("data")
                            .get("attributes")
                            .get("voice-template-audio-url")
                        )
                        _, file_name = download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name, title

                if "webex" in domain:
                    if "api/v1/recordings" in request.url:
                        res = requests.get(request.url).json()
                        url = (
                            res.get("downloadRecordingInfo")
                            .get("downloadInfo")
                            .get("mp4URL")
                        )
                        _, file_name = download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                        )
                        return file_name, title

                    else:
                        continue

                if "zoom" in domain:
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)

                    if mp4_url_pattern.match(request.url):
                        headers = {key: request.headers[key] for key in request.headers}
                        _, file_name = download_stream(
                            request.url,
                            file_name,
                            dir_data,
                            media_ext,
                            headers,
                        )

                        return file_name, title
                    continue

                if "facebook" in domain or "fb.com" in domain:
                    mp4_url_pattern = re.compile(r".*\.mp4\?.*", re.IGNORECASE)
                    if mp4_url_pattern.match(request.url):
                        headers = {key: request.headers[key] for key in request.headers}
                        url = request.url[: request.url.find("&bytestart")]
                        is_download_successful, file_name = download_stream(
                            url,
                            file_name,
                            dir_data,
                            media_ext,
                            headers,
                        )
                        if is_download_successful:
                            return file_name, title

                # download streams
                if (
                    ".m3u8" in request.url
                    or ".mpd" in request.url
                    or ".ism" in request.url
                    or ".flv" in request.url
                ):
                    url = request.url
                    keys = ["user-agent", "origin", "referer"]
                    headers = {
                        key: request.headers[key]
                        for key in keys
                        if key in request.headers
                    }

                    # Create cookie header
                    if "icastpro" in domain:
                        cookies = driver.get_cookies()
                        cookie = "; ".join(
                            [f"{c.get('name')}={c.get('value')}" for c in cookies]
                        )
                        headers["cookie"] = cookie

                    is_download_successful, file_name = download_stream(
                        url,
                        file_name,
                        dir_data,
                        media_ext,
                        headers,
                    )
                    if is_download_successful:
                        driver.quit()
                        return file_name, title

        driver.quit()
        return file_name, title

    except Exception as e:
        logger.warning(f"Error in download_stream: {e}")
        return None, None
