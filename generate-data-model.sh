curl -X PUT "localhost:9200/playlist_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "title": { "type": "text" },
      "original_playlist_url": { "type": "text", "index": false },
      "original_owner_url": { "type": "text", "index": false },
      "description": { "type": "text" },
      "video_ids": { "type": "keyword" },  // Array of video IDs
      "comments": { "type": "text" },      // Array of comments
      "likes": { "type": "integer" },
      "views": { "type": "integer" }
    }
  }
}'


curl -X PUT "localhost:9200/video_index" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "original_playlist_url": { "type": "text", "index": false },
      "original_owner_url": { "type": "text", "index": false },
      "comments": { "type": "text" },      // Array of comments
      "likes": { "type": "integer" },
      "views": { "type": "integer" },
      "url": { "type": "text", "index": false },
      "title": { "type": "text" },
      "description": { "type": "text" }
    }
  }
}'
