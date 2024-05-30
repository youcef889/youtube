# Import necessary libraries
import streamlit as st
from pytube import YouTube, Playlist
from math import ceil
import threading
import time
import os
import shutil
from zipfile import ZipFile

# Define the main function to encapsulate the Streamlit app
def main():
    # Title of the Streamlit app
    st.title("YouTube Downloader")

    # Radio button to select between downloading a playlist or a single video
    option = st.radio("Select option:", ("Download Playlist", "Download Single Video"))

    if option == "Download Playlist":
        download_playlist()
    elif option == "Download Single Video":
        download_single_video()

# Function to download a YouTube playlist
def download_playlist():
    # Input field to enter the Playlist URL
    playlist_url = st.text_input("Enter Playlist URL:")

    # Button to start processing the playlist
    if st.button("Download Playlist"):
        # Attempt to create a Playlist object from the provided URL
        try:
            p = Playlist(playlist_url)
            # Display playlist information
            st.write(f"**Playlist Name**: {p.title}")
            st.write(f"**Channel Name**: {p.owner}")
            st.write(f"**Total Videos**: {p.length}")
            st.write(f"**Total Views**: {p.views}")

            # Extract all video URLs from the playlist
            links = p.video_urls
            size = ceil(len(links) / 4)  # Determine chunk size for threads

            # Function to split the links into chunks for multithreading
            def split_link(links, size):
                for i in range(0, len(links), size):
                    yield links[i:i+size]

            link_chunks = list(split_link(links, size))
            st.write("Starting download...")

            # Track download progress
            progress_bars = [st.progress(0) for _ in range(len(link_chunks))]
            status_texts = [st.empty() for _ in range(len(link_chunks))]

            # Shared dictionary to store download status
            download_status = {"completed": [0] * len(link_chunks), "total": len(link_chunks)}

            # Function to download videos in a given list of links
            def downloader(link_chunk, thread_index, download_dir):
                completed = 0
                for url in link_chunk:
                    try:
                        yt = YouTube(url)
                        ys = yt.streams.get_highest_resolution()
                        ys.download(download_dir)
                        completed += 1
                    except Exception as e:
                        pass
                download_status["completed"][thread_index] = completed

            # Create a temporary directory for downloads
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)

            # Creating and starting threads
            threads = []
            for i in range(4):
                if i < len(link_chunks):
                    t = threading.Thread(target=downloader, args=(link_chunks[i], i, download_dir), name=f'd{i+1}')
                    threads.append(t)
                    t.start()

            # Monitoring thread progress
            while any(t.is_alive() for t in threads):
                for i in range(len(link_chunks)):
                    if download_status["total"] > 0:
                        progress = download_status["completed"][i] / len(link_chunks[i])
                        progress_bars[i].progress(progress)
                        status_texts[i].write(f"Thread {i+1}: {int(progress * 100)}%")
                time.sleep(1)  # Polling interval

            # Wait for all threads to complete
            for t in threads:
                t.join()

            # Zip the downloaded files
            zip_filename = "playlist_download.zip"
            with ZipFile(zip_filename, 'w') as zipf:
                for foldername, subfolders, filenames in os.walk(download_dir):
                    for filename in filenames:
                        filepath = os.path.join(foldername, filename)
                        zipf.write(filepath, os.path.relpath(filepath, download_dir))

            # Provide a download link for the zip file
            st.write("Download complete! Click below to download the zip file.")
            with open(zip_filename, "rb") as f:
                st.download_button(label="Download ZIP", data=f, file_name=zip_filename)

            # Clean up temporary files
            shutil.rmtree(download_dir)
            os.remove(zip_filename)

        except Exception as e:
            # Handle errors and display them
            st.error("An error occurred: " + str(e))

# Function to download a single YouTube video
def download_single_video():
    # Input field to enter the video URL
    video_url = st.text_input("Enter Video URL:")

    # Button to start downloading the video
    if st.button("Download Video"):
        try:
            # Create a YouTube object from the provided URL
            yt = YouTube(video_url)
            # Get the highest resolution stream
            ys = yt.streams.get_highest_resolution()
            # Download the video
            download_dir = "downloads"
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            ys.download(download_dir)
            st.write("Download complete! Click below to download the video.")
            with open(os.path.join(download_dir, ys.default_filename), "rb") as f:
                st.download_button(label="Download Video", data=f, file_name=ys.default_filename)
        except Exception as e:
            # Handle errors and display them
            st.error("An error occurred: " + str(e))

# Run the main function
if __name__ == "__main__":
    main()
