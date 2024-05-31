# Import necessary libraries
import streamlit as st
from pytube import YouTube, Playlist
from math import ceil
import threading
import time
import os
from io import BytesIO
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

    # Dropdown to select resolution
    resolution = st.selectbox("Select resolution:", ("Highest", "720p", "480p", "360p", "Audio Only"))

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

            total_size = 0
            start_time = time.time()

            # Function to download videos in a given list of links
            def downloader(link_chunk, thread_index):
                nonlocal total_size
                completed = 0
                video_files = []
                for url in link_chunk:
                    try:
                        yt = YouTube(url)
                        if resolution == "Highest":
                            ys = yt.streams.get_highest_resolution()
                        elif resolution == "Audio Only":
                            ys = yt.streams.get_audio_only()
                        else:
                            ys = yt.streams.filter(res=resolution).first()

                        video_bytes = BytesIO()
                        ys.stream_to_buffer(video_bytes)
                        video_bytes.seek(0)
                        video_files.append((ys.default_filename, video_bytes))
                        total_size += len(video_bytes.getvalue())
                        completed += 1
                    except Exception as e:
                        st.error(f"Error downloading {url}: {e}")
                download_status["completed"][thread_index] = completed
                return video_files

            # Create and start threads for downloading
            threads = []
            video_files_list = []
            for i in range(4):
                if i < len(link_chunks):
                    t = threading.Thread(target=lambda q, arg1: q.append(downloader(*arg1)), args=(video_files_list, (link_chunks[i], i)))
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

            end_time = time.time()
            total_time = end_time - start_time

            # Create zip file in memory
            zip_buffer = BytesIO()
            with ZipFile(zip_buffer, 'w') as zipf:
                for video_files in video_files_list:
                    for filename, video_bytes in video_files:
                        zipf.writestr(filename, video_bytes.getvalue())
            zip_buffer.seek(0)

            # Provide a download link for the zip file
            st.write("Download complete! Click below to download the zip file.")
            st.download_button(label="Download ZIP", data=zip_buffer, file_name="playlist_download.zip", mime="application/zip")

            # Display download statistics
            download_statistics(total_size, total_time)

        except Exception as e:
            # Handle errors and display them
            st.error("An error occurred: " + str(e))

# Function to download a single YouTube video
def download_single_video():
    # Input field to enter the video URL
    video_url = st.text_input("Enter Video URL:")

    # Dropdown to select resolution
    resolution = st.selectbox("Select resolution:", ("Highest", "720p", "480p", "360p", "Audio Only"))

    # Button to start downloading the video
    if st.button("Download Video"):
        try:
            start_time = time.time()

            # Create a YouTube object from the provided URL
            yt = YouTube(video_url)
            # Get the highest resolution stream
            if resolution == "Highest":
                ys = yt.streams.get_highest_resolution()
            elif resolution == "Audio Only":
                ys = yt.streams.get_audio_only()
            else:
                ys = yt.streams.filter(res=resolution).first()

            # Download the video to a BytesIO buffer
            video_bytes = BytesIO()
            ys.stream_to_buffer(video_bytes)
            video_bytes.seek(0)

            end_time = time.time()
            total_size = len(video_bytes.getvalue())
            total_time = end_time - start_time

            # Provide the video file as a download link
            st.write("Download complete! Click below to download the video.")
            st.download_button(label="Download Video", data=video_bytes, file_name=ys.default_filename)

            # Display download statistics
            download_statistics(total_size, total_time)

        except Exception as e:
            # Handle errors and display them
            st.error("An error occurred: " + str(e))

# Function to display download statistics
def download_statistics(total_size, total_time):
    st.write("### Download Statistics")
    st.write(f"**Total Download Size**: {total_size / (1024 * 1024):.2f} MB")
    st.write(f"**Total Download Time**: {total_time:.2f} seconds")
    if total_time > 0:
        st.write(f"**Average Download Speed**: {total_size / (1024 * 1024) / total_time:.2f} MB/s")

# Run the main function
if __name__ == "__main__":
    main()

