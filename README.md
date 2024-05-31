# YouTube Playlist Downloader

This is a Streamlit application that allows users to download YouTube playlists. The app downloads all videos from a given YouTube playlist URL and provides a link to download the videos as a zip file.

## Features

- Download all videos from a YouTube playlist.
- Multithreading support for faster downloads.
- Progress bars to monitor the download process.
- Download videos as a zip file.
## New Features Added:
  -Audio Only Option.
  -Improved Error Handling.
  -Download Statistics.

## Getting Started

### Clone the Repository

```sh
git clone https://github.com/youcef889/youtube.git
cd youtube
docker build -t youtube-playlist-downloader .
docker run  --publish 8501:8501 --detach --name  youtube-playlist-downloader youtube-playlist-downloader

