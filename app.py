from os import environ
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Path, Query, Body
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()
es = Elasticsearch("http://elasticsearch:9200")

class Playlist(BaseModel):
    title: str
    description: Optional[str] = None
    video_ids: Optional[List[str]] = []

class Video(BaseModel):
    id: str # unique identifier for the video.
    original_playlist_url: Optional[str] = None # original playlist URL (e.g., YouTube playlist)
    original_owner_url: Optional[str] = None # origional owner URL (e.g., YouTube channel)
    comments: Optional[str] = None # comments added by users (e.g., YouTube)
    likes: Optional[int] = 0 # Number of likes the video has received.
    views: Optional[int] = 0 # Number of views for the video.
    url: str # URL where the video can be accessed.
    title: Optional[str] = None # Title of the video.
    description: Optional[str] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Search Endpoint
@app.get("/search")
def search(query: Optional[str] = Query(None, description="Search terms"), limit: int = 10):
    """
    Search for videos in the video manager index in ElasticSearch.
    This interface is a wrapper around the ElasticSearch search API.
    It is used to search for videos in the video manager index. We
    can search for videos by title, description, or custom comments
    added by the user. The search results are returned in the order
    of relevance. The search results are returned as a list of
    dictionaries. Each dictionary contains the metadata of a video

    Parameters
    ----------
    query : str (optional)
        Search terms to search for in the video manager index
    
    limit : int (optional)
        Maximum number of results to return

    Returns
    -------
    dict
        A dictionary containing the search results

    Raises
    ------
    HTTPException
        If there is an error executing the search query
    """
    try:
        # index name of the ElasticSearch index for videos is in the environment
        # variable `VIDEO_MANAGER_INDEX`. It is set in the `docker-compose.yml` file.
        response = es.search(
            index=environ["VIDEO_MANAGER_INDEX"],
            body= {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "description", "comments"],
                        "type": "best_fields"
                    }
                }
            }
        )
        return { "message": "Search results for query: {}".format(query),
                 "results": response['hits']['hits'] }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Managing Playlists

@app.post("/playlists")
def create_playlist(playlist: Playlist):
    # Implement playlist creation logic here
    return {"message": "Playlist created"}

@app.get("/playlists/{playlist_id}")
def get_playlist(playlist_id: Optional[str] = Path(None)):
    """
    Get the details of a playlist from the playlist manager index in ElasticSearch.
    This interface is a wrapper around the ElasticSearch search API.
    It is used to get the details of a playlist from the playlist manager index.
    The playlist details are returned as a list of dictionaries. Each dictionary
    contains the metadata of a playlist.

    Parameters
    ----------
    playlist_id : str (optional)
        ID of the playlist to fetch from the playlist manager index

    Returns
    -------
    dict
        A dictionary containing the playlist details

    Raises
    ------
    HTTPException
        If there is an error executing the search query
    """
    try:
        response = es.search(
            index=environ["PLAYLIST_MANAGER_INDEX"],
            body= {
                "query": {
                    "match": {
                        "id": playlist_id
                    }
                }
            }
        )
        return { "message": "Playlist details for ID: {}".format(playlist_id),
                 "results": response['hits']['hits'] }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/playlists/{playlist_id}")
def update_playlist(playlist_id: str, playlist: Playlist):
    # Implement playlist update logic here
    return {"message": "Playlist updated: {}".format(playlist_id)}

@app.delete("/playlists/{playlist_id}")
def delete_playlist(playlist_id: str):
    # Implement playlist deletion logic here
    return {"message": "Playlist deleted: {}".format(playlist_id)}

# Managing Videos

@app.post("/videos")
def add_video(video: Video):
    
    es.index(
        index=environ["VIDEO_MANAGER_INDEX"],
        body= {
            "title": video.title,
            "description": video.description,
            "comments": video.comments,
            "likes": video.likes,
            "views": video.views,
            "url": video.url,
            "original_playlist_url": video.original_playlist_url,
            "original_owner_url": video.original_owner_url
        }   )

    return {"message": "Video added"}

@app.get("/videos/{video_id}")
def get_video(video_id: Optional[str] = Path(None)):
    # Implement logic to fetch a specific video or all videos
    return {"message": "Video details for ID: {}".format(video_id)}

@app.put("/videos/{video_id}")
def update_video(video_id: str, video: Video):
    # Implement video update logic here
    return {"message": "Video updated: {}".format(video_id)}

@app.delete("/videos/{video_id}")
def delete_video(video_id: str):
    # Implement video deletion logic here
    return {"message": "Video deleted: {}".format(video_id)}

# Importing Data from YouTube

@app.post("/import/youtube-playlist")
def import_youtube_playlist(youtube_playlist_id: str = Body(...)):
    # Implement YouTube playlist import logic here
    return {"message": "Imported YouTube playlist: {}".format(youtube_playlist_id)}

@app.post("/import/youtube-channel")
def import_youtube_channel(youtube_channel_id: str = Body(...)):
    # Implement YouTube channel import logic here
    return {"message": "Imported YouTube channel: {}".format(youtube_channel_id)}

@app.post("/import/youtube-video")
def import_youtube_video(youtube_video_id: str = Body(...)):
    # Implement YouTube video import logic here
    return {"message": "Imported YouTube video: {}".format(youtube_video_id)}

@app.post("/import/video-link")
def import_video_link(video_url: str = Body(...)):
    # Implement logic for importing a video from a link
    return {"message": "Imported video from URL: {}".format(video_url)}
