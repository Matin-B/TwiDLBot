# TwiDLBot

A high-performance, self-hosted Telegram bot for downloading media from X (formerly Twitter). 

TwiDLBot is built on top of the [TwiGram](https://github.com/Matin-B/TwiGram) library and leverages `aiogram` 3.x. To bypass standard Telegram file size restrictions (allowing video downloads up to 2,000 MB), this project is engineered to run alongside a **Local Telegram Bot API server** via Docker.

## Features

* **Complete Media Support**: Downloads standard text tweets, photos, GIFs, multi-media albums, and videos.
* **Large File Handling**: Utilizes a local Telegram API server to handle massive video files without hitting the public API's 20 MB restriction.
* **Intelligent Path Translation**: Implements a custom `DockerFilesPathWrapper` to seamlessly pass file paths between the host filesystem and the isolated Docker container.
* **Analytics Ready**: Automatically logs users and stores tweet metadata in MongoDB for tracking and analytics.
* **Graceful Fallbacks**: Automatically switches back to physical file downloads and standard multi-part uploads if remote URL submission fails.

## Architecture

* **Framework**: [aiogram 3.x](https://docs.aiogram.dev/en/latest/) (Asynchronous Telegram bot framework)
* **Database**: MongoDB (via `pymongo`)
* **Telegram Local API**: Official [Telegram Bot API Server](https://core.telegram.org/bots/api#using-a-local-bot-api-server) (Dockerized)
* **Deployment**: `systemd` for process management


---

## Installation & Deployment
- Copy the project folder in VPS (twidlbot folder)
- Install python virtual environment using command ```sudo apt install python3.14-venv```
- Create and activate virtualenv using the command below:
  ```shell
  python3.14 -m venv .venv && source .venv/bin/activate
  ```
- Upgrade pip version using command ```python -m pip install --upgrade pip```
- Install Python requirements using the command below:
  ```shell
  pip install -r requirements.txt
  ```
- Copy ```twidlbot.service``` to ```/etc/systemd/system/``` (```sudo cp twidlbot.service /etc/systemd/system/```)
- Reload the systemd daemon to load the new service:
  ```shell
  sudo systemctl daemon-reload
  ```
- Start the service:
  ```shell
  sudo systemctl start twidlbot.service
  ```
- Check the status of the service to make sure it's running:
  ```shell
  sudo systemctl status twidlbot.service
  ```
- Enable the service to start automatically at boot:
  ```shell
  sudo systemctl enable twidlbot.service
  ```

### Note: If you make changes to the twidlbot.service file, you need to reload the systemd daemon and restart the service for the changes to 