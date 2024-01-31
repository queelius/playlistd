from os import environ
from elasticsearch.exceptions import NotFoundError
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Path, Query, Body, status
from typing import List, Optional
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from typing import Union, List

app = FastAPI()
es = Elasticsearch("http://elasticsearch:9200")

class Playlist(BaseModel):
    title: str # title of the playlist
    original_playlist_url: Optional[str] = None # original playlist URL (e.g., YouTube playlist)
    original_owner_url: Optional[str] = None # original owner URL (e.g., YouTube channel)
    description: Optional[str] = None # description of the playlist
    video_ids: Optional[List[str]] = None # list of video IDs in the playlist
    comments: Optional[str] = None # additional comments added
    likes: int = 0
    views: int = 0

class Video(BaseModel):
    original_playlist_url: Optional[str] = None # original playlist URL (e.g., YouTube playlist)
    original_owner_url: Optional[str] = None # original owner URL (e.g., YouTube channel)
    comments: Optional[str] = None # additional comments added
    likes: int = 0 # Number of likes the video has received.
    views: int = 0 # Number of views for the video.
    url: str # URL where the video can be accessed.
    title: Optional[str] = None # Title of the video.
    description: Optional[str] = None

class VideoResponse(Video):
    id: str  # Elasticsearch _id
    score: Optional[float] = None # Elasticsearch score

class PlaylistResponse(Playlist):
    id: str  # Elasticsearch _id
    score: Optional[float] = None # Elasticsearch score

class DetailedPlaylistResponse(PlaylistResponse):
    videos: List[Video] = []

class MutationResponse(BaseModel):
    message: str
    id: str

def find(index: str, id: str):
    try:
        return es.get(index=index, id=id)['_source']
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"id={id} in {index} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))


def search_util(index: str, q: Optional[str] = None, start: int = 0, size: int = 10, fields: Optional[List[str]] = None):
    try:
        body = {
            "from": start,
            "size": size,
            "query": {
                "match_all": {}
            } if not q else {
                "multi_match": {
                    "query": q,
                    "fields": fields,
                    "type": "best_fields"
                }
            }
        }
        return es.search(index=index, body=body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/redoc")

# Managing Playlists

@app.get("/playlists/",
         response_model=List[PlaylistResponse],
         summary="Search playlists",
         description="List all playlists or search for playlists")
def get_playlists(q: Optional[str] = Query(None, description="Search terms"),
                  start: int = Query(0, alias="start"),
                  size: int = Query(10, alias="size"),
                  fields: Optional[List[str]] = Query(["title", "description", "comments"], alias="fields")):

    resp = search_util(environ["PLAYLIST_INDEX"], q, start, size, fields)
    return [PlaylistResponse(id=hit["_id"],
                             score=hit["_score"],
                             **hit["_source"]) for hit in resp['hits']['hits']]

@app.post("/playlists",
          summary="Create a playlist",
          description="Create a playlist")
def create_playlist(playlist: Playlist):
    return process(es.index(
        index=environ["PLAYLIST_INDEX"],
        body=playlist.dict()))

@app.get("/playlists/{id}",
         summary="Get a playlist",
         description="Get the details of a playlist")
def get_playlist(id: str):
    return find(environ["PLAYLIST_INDEX"], id)
  
@app.put("/playlists/{id}",
         summary="Update a playlist",
         description="Update the details of a playlist")
def update_playlist(id: str, playlist: Playlist):
    return process(es.update(index=environ["PLAYLIST_INDEX"],
        id=id, body=playlist.dict()))

@app.delete("/playlists/{id}",
            summary="Delete a playlist",
            description="Delete a playlist from the playlist index")
def delete_playlist(id: str):
    try:
        return es.delete(index=environ["PLAYLIST_INDEX"], id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"id={id} in {environ['PLAYLIST_INDEX']} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Managing Videos
@app.get("/videos/",
         response_model=List[VideoResponse],
         summary="Search videos",
         description="List all videos or search for videos")
def get_videos(q: Optional[str] = Query(None, description="Search terms"),
               start: int = Query(0, alias="start"),
               size: int = Query(10, alias="size"),
               fields: Optional[List[str]] = Query(["title", "description", "comments"], alias="fields")):
    resp = search_util(environ["VIDEO_INDEX"], q, start, size, fields)
    return [VideoResponse(id=hit["_id"],
                          score=hit["_score"],
                          **hit["_source"]) for hit in resp['hits']['hits']]
@app.post("/videos/",
          summary="Add a video",
          description="Add a video to the video index")
def add_video(video: Video):
    resp = es.index(index=environ["VIDEO_INDEX"], body=video.dict())
    return MutationResponse(message="Added video", id=resp['_id'])

@app.get("/videos/{id}",
         summary="Get a video",
         description="Get the details of a video",
         response_model=VideoResponse)
def get_video(id: str = Path(..., description="The ID of the video to get")):
    return VideoResponse(id=id, **find(environ["VIDEO_INDEX"], id))

@app.put("/videos/{id}",
         summary="Update a video",
         description="Update the details of a video")
def update_video(id: str, video: Video):
    return es.update(index=environ["VIDEO_INDEX"], id=id, body=video.dict())

@app.delete("/videos/{id}", summary="Delete a video", description="Delete a video from the video index")
def delete_video(id: str):
    try:
        resp = es.delete(index=environ["VIDEO_INDEX"], id=id)
        return MutationResponse(result=resp['result'], id=resp['_id'])
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"id={id} in {environ['VIDEO_INDEX']} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))

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


# Advanced Search that exposes the Elasticsearch DSL

@app.post("/search",
          summary="Advanced search",
          description="Advanced search using the Elasticsearch DSL",
          response_model=Union[List[PlaylistResponse], List[VideoResponse]])
def search(body: dict = Body(...), videos: bool = Body(False)):
    try:
        index = environ["VIDEO_INDEX"] if videos else environ["PLAYLIST_INDEX"]
        resp = es.search(index=index, body=body)
        return [PlaylistResponse(id=hit["_id"],
                                 score=hit["_score"],
                                 **hit["_source"]) if not videos else
                VideoResponse(id=hit["_id"],
                              score=hit["_score"],
                              **hit["_source"]) for hit in resp['hits']['hits']]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))