import requests as req
import os 
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")

API_KEY = os.getenv("API_KEY")
CHANENEL_HANDLE = "ElMarianaJuega" 

def get_playlistId():
    
    try:
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=contentDetails&forHandle={CHANENEL_HANDLE}&key={API_KEY}"

        response = req.get(url)
        
        response.raise_for_status()

        data = response.json()

        #print(json.dumps(data, indent=4))
        
        channel_items = data["items"][0]
        
        channel_playlistId =  channel_items["contentDetails"]["relatedPlaylists"]["uploads"]
        
        # print(channel_playlistId)
        
        return channel_playlistId
    
    except req.exceptions.RequestException as e:
        print(f"Un error ha ocurrido: {e}")
        

if __name__ == "__main__":
    get_playlistId()