# Import necessary libraries
import streamlit as st
from pytube import YouTube, Playlist
from math import ceil
import threading
import time
import os
from pathlib import Path
import zipfile

# Function to download a single video
def Download(link):
    youtubeObject = YouTube(link)
    youtubeObject = youtubeObject.streams.get_highest_resolution()
    try:
        youtubeObject.download(output_path="downloads")
    except Exception as e:
        print(f"An error has occurred: {e}")
    print("Download is completed successfully")

# Define the main function to encapsulate the Streamlit app
def main():
    # Title of the Streamlit app
    st.title("YouTube Downloader")

    # Single video downloader
    st.subheader("Download a Single Video")
    video_url = st.text_input("Enter YouTube Video URL:")
    
    if st.button("Download Video"):
        if video_url:
            try:
                Download(video_url)
                st.success("Video downloaded successfully!")
                video_path = next(Path("downloads").iterdir())
                with open(video_path, "rb") as f:
                    st.download_button(
                        label="Download Video",
                        data=f,
                        file_name=video_path.name,
                        mime="video/mp4"
                    )
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            st.error("Please enter a valid URL.")

    st.write("---")

    # Playlist downloader
    st.subheader("Download a Playlist")
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

            # Create a directory to store downloaded videos
            download_dir = Path("downloads")
            download_dir.mkdir(exist_ok=True)

            # Function to download videos in a given list of links
            def downloader(link_chunk, thread_index):
                completed = 0
                for url in link_chunk:
                    try:
                        Download(url)
                        completed += 1
                    except Exception as e:
                        pass
                download_status["completed"][thread_index] = completed

            # Creating and starting threads
            threads = []
            for i in range(4):
                if i < len(link_chunks):
                    t = threading.Thread(target=downloader, args=(link_chunks[i], i), name=f'd{i+1}')
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

            st.write("Download complete!")

            # Zip the downloaded videos
            zip_path = download_dir / "videos.zip"
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for video_file in download_dir.iterdir():
                    if video_file.is_file():
                        zipf.write(video_file, video_file.name)
            
            # Provide download link for the zip file
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download Videos",
                    data=f,
                    file_name="videos.zip",
                    mime="application/zip"
                )

        except Exception as e:
            # Handle errors and display them
            st.error("An error occurred: " + str(e))

# Run the main function
if __name__ == "__main__":
    main()

