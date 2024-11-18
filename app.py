from os import environ
from datetime import datetime
from elasticsearch.exceptions import NotFoundError, ElasticsearchException
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Path, Query, Body
from typing import List, Optional
from pydantic import BaseModel
from fastapi.responses import RedirectResponse
from data_model import index, initialize_playlist_index

app = FastAPI()
es = Elasticsearch("http://elasticsearch:9200")
initialize_playlist_index(es)

class Video(BaseModel):
    date_added: Optional[datetime] = None # Date the video was added to the index.
    date_published: Optional[datetime] = None # Date the video was published.
    date_updated: Optional[datetime] = None # Date the video was last updated.
    likes: int = 0 # Number of likes the video has received.
    views: int = 0 # Number of views for the video.
    url: str # URL where the video can be accessed.
    title: Optional[str] = None # Title of the video.
    description: Optional[str] = None

class Playlist(BaseModel):
    title: str # title of the playlist
    date_added: Optional[datetime] = None # date the playlist was added to the index
    date_updated: Optional[datetime] = None # date the playlist was last updated
    original_playlist_published: Optional[datetime] = None # date the original playlist was published
    original_playlist_url: Optional[str] = None # original playlist URL (e.g., YouTube playlist)
    original_owner_url: Optional[str] = None # original owner URL (e.g., YouTube channel)
    description: Optional[str] = None # description of the playlist
    videos: Optional[Video] = None # list of videos in the playlist
    likes: int = 0
    views: int = 0

class VideoResponse(Video):
    id: str # Elasticsearch _id
    score: Optional[float] = None # Elasticsearch score

class PlaylistResponse(Playlist):
    id: str  # Elasticsearch _id
    score: Optional[float] = None # Elasticsearch score

class MutationResponse(BaseModel):
    message: str
    id: str

def search_pl(query: Optional[str] = None,
              start: int = 0,
              size: int = 10,
              fields: Optional[List[str]] = None):
    try:
        body = {
            "from": start,
            "size": size,
            "query": {
                "match_all": {}
            } if not query else {
                "multi_match": {
                    "query": query,
                    "fields": fields,
                    "type": "best_fields"
                }
            }
        }
        return es.search(index=index, body=body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def search_pl_vid(playlist_id: str,
                  query: Optional[str] = None,
                  start: int = 0,
                  size: int = 10,
                  fields: Optional[List[str]] = None):
    try:
        if query is None:
            return es.get(index=index, id=playlist_id)["videos"]
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "playlist_id": playlist_id
                            }
                        },
                        {
                            "nested": {
                                "path": "videos",
                                "query": {
                                    "match": {
                                        "videos.title": query
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
        return es.search(index=index, body=body)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
######################
# REST API Endpoints #
######################

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/redoc")

#############
# Playlists #
#############

@app.get("/playlists/",
         response_model=List[PlaylistResponse],
         summary="Search playlists")
def get_playlists(query: Optional[str] = Query(None, description="Keywords"),
                  start: int = Query(0, alias="start"),
                  size: int = Query(10, alias="size"),
                  fields: Optional[List[str]] = Query(["title", "description"], alias="fields")):

    resp = search_pl(query, start, size, fields)
    return [PlaylistResponse(id=hit["_id"], score=hit["_score"],
                             **hit["_source"]) for hit in resp['hits']['hits']]

@app.post("/playlists/",
          summary="Create a playlist")
def create_playlist(playlist: Playlist):
    try:
        return es.index(index=index, body=playlist.dict())
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))

# response_model=PlaylistResponse
@app.get("/playlists/{id}/",
         summary="Get a playlist")
def get_playlist(id: str = Path(..., description="The ID of the playlist to get")):
    try:
        return es.get(index=index, id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"playlist {id=} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@app.put("/playlists/{id}",
         summary="Update a playlist")
def update_playlist(playlist: Playlist,
                    id: str = Path(..., description="The ID of the playlist to update")):
    try:
        return es.update(index=index, id=id, body=playlist.dict())
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"playlist {id=} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/playlists/{id}",
            summary="Delete a playlist")
def delete_playlist(id: str = Path(..., description="The ID of the playlist to delete")):
    try:
        return es.delete(index=index, id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"playlist {id=} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))
    

########################
# Videos in a Playlist #
########################
    
@app.get("/playlists/{id}/videos/",
         response_model=List[VideoResponse],
         summary="Search videos in a playlist")
def get_videos(query: Optional[str] = Query(None, description="Keywords"),
               start: int = Query(0, alias="start"),
               size: int = Query(10, alias="size"),
               fields: Optional[List[str]] = Query(["title", "description"], alias="fields")):
    resp = search_pl_vid(query, start, size, fields)
    return [VideoResponse(id=hit["_id"], score=hit["_score"],
                          **hit["_source"]) for hit in resp['hits']['hits']]

@app.post("/playlist/{id}/videos/",
          summary="Add a video to a playlist")
def add_video(video: Video):
    try:
        return es.index(index=index, body=video.dict())
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/playlist/{playlist_id}/videos/{video_id}",
         summary="Get details of a video in a playlist",
         response_model=VideoResponse)
def get_video(playlist_id: str = Path(..., description="The ID of the video to get"),
              video_id: str = Path(..., description="The ID of the video to get")):
    try:
        # must look at the nested videos field
        playlist = es.get(index=index, id=playlist_id)
        for video in playlist["_source"]["videos"]:
            if video["_id"] == video_id:
                return VideoResponse(id=video_id, **video)
        raise HTTPException(status_code=404, detail=f"video {video_id=} not found")
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"playlist {playlist_id=} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/playlists/{playlist_id}/videos/{video_id}",
         summary="Update a video in a playlist")
def update_video(video: Video,
                 playlist_id: str = Path(..., description="The ID of the playlist to update"),
                 video_id: str = Path(..., description="The ID of the video to update")):
    try:
        # must look at the nested 'videos' field for the given playlist
        playlist = es.get(index=index, id=playlist_id)
        for i, v in enumerate(playlist["_source"]["videos"]):
            if v["_id"] == video_id:
                playlist["_source"]["videos"][i] = video.dict()
                return es.update(index=index, id=playlist_id, body=playlist["_source"])
        raise HTTPException(status_code=404, detail=f"video {video_id=} not found")
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"video {id=} not found")
    except ElasticsearchException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/playlists/{playlist_id}/videos/{id}",
            summary="Delete a video in a playlist")
def delete_video(id: str):
    try:
        return es.delete(index=index, id=id)
    except NotFoundError:
        raise HTTPException(status_code=404, detail=f"video {id=} not found")
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
