import requests as req
import os 
from dotenv import load_dotenv
from datetime import date
import json

# Load environment variables from the local .env file
load_dotenv(dotenv_path="./.env")

# Global Configuration Constants
API_KEY = os.getenv("API_KEY")
CHANENEL_HANDLE = "ElMarianaJuega" 
maxResults = 50  # Maximum number of results allowed per request by the YouTube API

def get_playlistId():
    """
    Fetches the unique 'Uploads' playlist ID for a given YouTube channel handle.
    Every YouTube channel automatically stores all its uploaded videos in a hidden playlist.
    """
    try:
        # We query the 'channels' endpoint using the channel handle
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANENEL_HANDLE}&key={API_KEY}"
        response = req.get(url)
        response.raise_for_status()  # Automatically raises an exception for HTTP errors (4xx or 5xx)
        
        data = response.json()
        channel_items = data["items"][0]
        
        # Extract the specific playlist ID where all uploaded videos are stored
        channel_playlistId = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]
        return channel_playlistId
        
    except req.exceptions.RequestException as e:
        print(f"An error occurred in get_playlistId: {e}")
        raise e

def get_videosId(playlistId):
    """
    Retrieves all video IDs from the specified playlist using pagination.
    Loops through pages using 'nextPageToken' until no more pages are found.
    """
    videos_ids = []
    pageToken = None
    
    # FIXED: The playlistId parameter is now properly injected dynamically into the URL
    base_url = f"https://youtube.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlistId}&key={API_KEY}" 
    
    try:
        while True:
            url = base_url
            # If a pagination token exists from the previous loop, append it to fetch the next batch
            if pageToken:
                url += f"&pageToken={pageToken}"
                
            response = req.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Loop through each item in the current batch and collect the video ID
            for item in data.get('items', []):
                video_id = item['contentDetails']['videoId']
                videos_ids.append(video_id)
            
            # Check if there is another page of data; if not, break the loop
            pageToken = data.get('nextPageToken')
            if not pageToken:
                break
            
        return videos_ids
        
    except req.exceptions.RequestException as e:
        print(f"An error occurred in get_videosId: {e}")
        raise e
        
def batch_list(video_id_list, batch_size=50):
    """
    A generator function that splits a large list into smaller chunks (batches).
    This prevents hitting YouTube API URL length limitations when requesting multiple video details.
    """
    for video_id in range(0, len(video_id_list), batch_size):
        # Yields a slice of the list from the current index up to the batch size
        yield video_id_list[video_id:video_id + batch_size]

def extract_video_data(video_ids):
    """
    Takes a list of video IDs, groups them in batches of 50, and fetches
    detailed statistics and metadata for each video.
    """
    extracted_data = []

    try:
        # Loop through the video IDs in chunks of 50 using our global generator function
        for batch in batch_list(video_ids, maxResults):
            # Convert the list of IDs into a single comma-separated string (e.g., "id1,id2,id3")
            video_ids_str = ",".join(batch)
            
            # FIXED: Combined multiple 'part' arguments into a single comma-separated string as per API rules
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=contentDetails,snippet,statistics&id={video_ids_str}&key={API_KEY}"
            
            response = req.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Process each individual video returned in the current API response batch
            for item in data.get('items', []):
                video_id = item['id']
                snippet = item['snippet']
                contentDetails = item['contentDetails']
                statistics = item['statistics']
                
                # Structure the raw API response into a clean, normalized dictionary
                video_data = {
                    "video_id" : video_id,
                    "title" : snippet["title"],
                    "publishedAt" : snippet["publishedAt"],
                    "duration" : contentDetails['duration'],
                    # Using .get() ensures that if a count is missing (e.g., disabled comments), it defaults to None
                    "viewCount" : statistics.get('viewCount', None),
                    "likeCount" : statistics.get('likeCount', None),
                    "commentCount" : statistics.get('commentCount', None)
                }
                # FIXED: Corrected indentation so EVERY video in the loop gets saved, not just the last one
                extracted_data.append(video_data)
            
        return extracted_data
        
    except req.exceptions.RequestException as e:
        print(f"An error occurred in extract_video_data: {e}")
        raise e
    
def save_to_json(extracted_data):
    """
    Saves the completely extracted and structured dataset into a JSON file.
    The filename dynamically includes the current execution date.
    """
    # NOTE: Ensure that a directory named 'data' exists at the root of your project
    file_path = f'./data/YT_data_{date.today()}.json'
    
    # Open the file with UTF-8 encoding to perfectly handle emojis and special characters
    with open(file_path, "w", encoding="utf-8") as json_outfile:
        # indent=4 formats the JSON beautifully, ensure_ascii=False keeps special symbols intact
        json.dump(extracted_data, json_outfile, indent=4, ensure_ascii=False)

# Main Execution block (Orchestration Layer)
if __name__ == "__main__":
    print("Starting YouTube ELT Pipeline...")
    
    # Step 1: Get the upload playlist ID for the channel
    playlistId = get_playlistId()
    
    # Step 2: Extract all video IDs belonging to that playlist
    video_ids = get_videosId(playlistId)
    print(f"Found {len(video_ids)} video IDs. Fetching details...")
    
    # Step 3: Fetch detailed metrics for all collected video IDs
    video_data = extract_video_data(video_ids)
    
    # Step 4: Load/Save the transformed data locally into a JSON file
    save_to_json(video_data)
    
    print(f"Pipeline successfully completed! Extracted and saved {len(video_data)} videos into the data/ folder.")