import requests
import re

BASE_URL = "https://cdn.syndication.twimg.com/tweet"

headers = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/98.0.4758.80 Safari/537.36",
}


def human_readable_filesize(num, suffix="B"):
    """
    Return a human readable filesize from bytes
    Note: from StackOverflow(https://stackoverflow.com/a/1094933/11491901)
    
    :param num: The number to format
    :param suffix: The suffix to use for the units, defaults to B (optional)
    :return: the size of the file in a human readable format.
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def check_content_size(url):
    response = requests.head(url, allow_redirects=True)
    content_size = int(response.headers['Content-Length'])
    if content_size < 20971520:
        return {
            "status": True,
            "size": human_readable_filesize(content_size)
        }
    return {
        "status": False,
        "size": human_readable_filesize(content_size)
    }


def edit_tweet_text(tweet_text: str, entities: dict) -> str:
    """
    Replace expended urls with their short version
    
    :param tweet_text: The text of the tweet
    :type tweet_text: str

    :param entities: A dictionary of entities that are present in the tweet
    :type entities: dict

    :return: The tweet text with the media url removed.
    """
    urls = entities.get("urls")
    for url in urls:
        expanded_url = url.get("expanded_url")
        shorted_url = url.get("url")
        tweet_text = tweet_text.replace(shorted_url, expanded_url)
    try:
        media_url = entities.get("media")[0].get("url")
        return tweet_text.replace(f" {media_url}", "")
    except TypeError:
        return tweet_text


def text_tweet_handler(data: dict) -> dict:
    """
    Handle text tweet
    
    :param data: The data that you want to extract the photo from
    :type data: dict

    :return: A dictionary with the following keys:
        - status: True or False, depending on whether the tweet was successfully extracted
        - type_name: "text"
        - data: a dictionary with the following keys:
            - tweet_text: the text of the tweet
            - created_at: the date of tweet created (UTC time)
            - tweet_url: the url of the tweet
            - owner_username: the username of the user who posted the tweet
            - owner_name: the name of the user who posted the tweet
    """
    tweet_id_str = data.get("id_str")
    created_at = data.get("created_at")
    owner_username = data.get("user").get("screen_name")
    owner_name = data.get("user").get("name")

    tweet_text = data.get("text")
    entities = data.get("entities")
    tweet_text = edit_tweet_text(tweet_text, entities)

    tweet_url = f"https://twitter.com/{owner_username}/status/{tweet_id_str}"
    return {
        "status": True,
        "type_name": "text",
        "data": {
            "tweet_text": tweet_text,
            "tweet_url": tweet_url,
            "created_at": created_at,
            "owner_username": owner_username,
            "owner_name": owner_name,
        }
    }


def gif_tweet_handler(data: dict) -> dict:
    """
    Handle tweets that contain a gif
    
    :param data: The data that you want to extract the photo from
    :type data: dict

    :return: A dictionary with the following keys:
        - status: True or False, depending on whether the tweet was successfully extracted
        - type_name: "gif"
        - data: a dictionary with the following keys:
            - tweet_text: the text of the tweet
            - created_at: the date of tweet created (UTC time)
            - tweet_url: the url of the tweet
            - gif_url: the url of the gif
            - owner_username: the username of the user who posted the tweet
            - owner_name: the name of the user who posted the tweet
    """
    video = data.get("video")
    video_variants = video.get("variants")
    gif_url = video_variants[0].get("src")
    
    tweet_id_str = data.get("id_str")
    created_at = data.get("created_at")
    owner_username = data.get("user").get("screen_name")
    owner_name = data.get("user").get("name")

    tweet_text = data.get("text")
    entities = data.get("entities")
    tweet_text = edit_tweet_text(tweet_text, entities)

    tweet_url = f"https://twitter.com/{owner_username}/status/{tweet_id_str}"
    return {
        "status": True,
        "type_name": "gif",
        "data": {
            "tweet_text": tweet_text,
            "created_at": created_at,
            "tweet_url": tweet_url,
            "gif_url": gif_url,
            "owner_username": owner_username,
            "owner_name": owner_name,
        }
    }


def video_tweet_handler(data: dict) -> dict:
    """
    Handle tweets that contain a video
    
    :param data: The data that you want to extract the photo from
    :type data: dict

    :return: A dictionary with the following keys:
        - status: True or False, depending on whether the tweet was successfully extracted
        - type_name: "video"
        - data: a dictionary with the following keys:
            - tweet_text: the text of the tweet
            - created_at: the date of tweet created (UTC time)
            - tweet_url: the url of the tweet
            - video_poster_url: the url of the video poster
            - video_urls: a list of urls of the videos in the tweet (sorted by size)
            - owner_username: the username of the user who posted the tweet
            - owner_name: the name of the user who posted the tweet
    """
    video = data.get("video")
    content_type = video["contentType"]
    if content_type == "gif":
        return gif_tweet_handler(data)
    video_poster_url = video.get("poster") + "?name=large"
    video_variants = video.get("variants")
    count = 0
    for item in video_variants:
        if item['type'] == 'application/x-mpegURL':
            video_variants.pop(count)
        count += 1
    
    video_urls = {}
    for item in video_variants:
        video_url = item.get("src")
        video_quality = video_url.split("/vid/")[-1].split("/")[0]
        video_urls[video_quality] = video_url
    
    # Sort the video urls by highest quality
    video_urls = dict(
        sorted(
            video_urls.items(),
            key=lambda x: int(x[0].split("x")[0]),
            reverse=True,
        )
    )
    
    tweet_id_str = data.get("id_str")
    created_at = data.get("created_at")
    owner_username = data.get("user").get("screen_name")
    owner_name = data.get("user").get("name")

    tweet_text = data.get("text")
    entities = data.get("entities")
    tweet_text = edit_tweet_text(tweet_text, entities)

    tweet_url = f"https://twitter.com/{owner_username}/status/{tweet_id_str}"
    return {
        "status": True,
        "type_name": "video",
        "data": {
            "tweet_text": tweet_text,
            "created_at": created_at,
            "tweet_url": tweet_url,
            "video_poster_url": video_poster_url,
            "video_urls": video_urls,
            "owner_username": owner_username,
            "owner_name": owner_name,
        }
    }


def album_tweet_handler(data: dict) -> dict:
    """
    Handle tweets that contain multiple photos
    
    :param data: The data that you want to extract the photo from
    :type data: dict

    :return: A dictionary with the following keys:
        - status: True or False, depending on whether the tweet was successfully extracted
        - type_name: "album"
        - data: a dictionary with the following keys:
            - tweet_text: the text of the tweet
            - created_at: the date of tweet created (UTC time)
            - tweet_url: the url of the tweet
            - photo_count: the number of photos in the album
            - photo_urls: a list of urls of the photos in the album
            - owner_username: the username of the user who posted the tweet
            - owner_name: the name of the user who posted the tweet
    """
    photos = data.get("photos")
    photo_count = len(photos)
    photo_urls = []
    for photo in photos:
        photo_urls.append(
            photo.get("url") + "?name=large"
        )

    tweet_id_str = data.get("id_str")
    created_at = data.get("created_at")
    owner_username = data.get("user").get("screen_name")
    owner_name = data.get("user").get("name")

    tweet_text = data.get("text")
    entities = data.get("entities")
    tweet_text = edit_tweet_text(tweet_text, entities)

    tweet_url = f"https://twitter.com/{owner_username}/status/{tweet_id_str}"
    return {
        "status": True,
        "type_name": "album",
        "data": {
            "tweet_text": tweet_text,
            "created_at": created_at,
            "tweet_url": tweet_url,
            "photo_count": photo_count,
            "photo_urls": photo_urls,
            "owner_username": owner_username,
            "owner_name": owner_name,
        }
    }


def photo_tweet_handler(data: dict) -> dict:
    """
    Handle tweets that contain a single photo
    
    :param data: The data that you want to extract the photo from
    :type data: dict

    :return: A dictionary with the following keys:
        - status: True or False, depending on whether the tweet was successfully extracted
        - type_name: "photo"
        - data: a dictionary with the following keys:
            - tweet_text: the text of the tweet
            - created_at: the date of tweet created (UTC time)
            - tweet_url: the url of the tweet
            - photo_url: the url of the photo
            - owner_username: the username of the user who posted the tweet
            - owner_name: the name of the user who posted the tweet
    """
    photos = data.get("photos")
    if len(photos) >= 1:
        return album_tweet_handler(data)
    photo_url = photos[0].get("url") + "?name=large"

    tweet_id_str = data.get("id_str")
    created_at = data.get("created_at")
    owner_username = data.get("user").get("screen_name")
    owner_name = data.get("user").get("name")

    tweet_text = data.get("text")
    entities = data.get("entities")
    tweet_text = edit_tweet_text(tweet_text, entities)

    tweet_url = f"https://twitter.com/{owner_username}/status/{tweet_id_str}"
    return {
        "status": True,
        "type_name": "photo",
        "data": {
            "tweet_text": tweet_text,
            "created_at": created_at,
            "tweet_url": tweet_url,
            "photo_url": photo_url,
            "owner_username": owner_username,
            "owner_name": owner_name,
        }
    }


def download(url: str) -> dict:
    if len(url) == 0:
        raise ValueError("URL cannot be empty.")
    url = url.replace("www.", "")
    if "t.co/" in url:
        response = requests.get(url)
        url = response.url
    regex_pattern = r"twitter.com\/.*\/status\/([0-9]*)"
    tweet_id = re.search(regex_pattern, url)
    if tweet_id is None:
        return {
            "status": False,
            "status_code": 400,
            "message": "The url is not a tweet url",
        }
    tweet_id = tweet_id.group(1)
    parameters = (
        ("id", tweet_id),
        ("lang", "en"),
    )
    response = requests.get(BASE_URL, headers=headers, params=parameters)
    if response.status_code == 200:
        data = response.json()
        if "video" in data:
            return video_tweet_handler(data)
        else:
            if "photos" in data:
                return photo_tweet_handler(data)
            return text_tweet_handler(data)
    elif response.status_code == 404:
        return {
            "status": False,
            "status_code": response.status_code,
            "message": "Tweet is not found. It may have been deleted or made private.",
        }
    return {
        "status": False,
        "status_code": response.status_code,
        "message": response.reason,
    }