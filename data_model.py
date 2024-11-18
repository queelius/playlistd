from os import environ

playlist_mapping = {
  "mappings": {
    "properties": {
      "title": {
        "type": "text"
      },
      "date_added": {
        "type": "date"
      },
      "date_updated": {
        "type": "date"
      },
      "original_playlist_published": {
        "type": "date"
      },
      "original_playlist_url": {
        "type": "text"
      },
      "original_owner_url": {
        "type": "text"
      },
      "description": {
        "type": "text"
      },
      "videos": {
        "type": "nested",
        "properties": {
          "comments": {
            "type": "text"
          },
          "date_added": {
            "type": "date"
          },
          "date_published": {
            "type": "date"
          },
          "date_updated": {
            "type": "date"
          },
          "likes": {
            "type": "integer"
          },
          "views": {
            "type": "integer"
          },
          "url": {
            "type": "text"
          },
          "title": {
            "type": "text"
          },
          "description": {
            "type": "text"
          }
        }
      },
      "comments": {
        "type": "text"
      },
      "likes": {
        "type": "integer"
      },
      "views": {
        "type": "integer"
      }
    }
  }
}

index = environ['PLAYLIST_INDEX']

def initialize_playlist_index(es):
    if not es.indices.exists(index=index):
        es.indices.create(index=index, body=playlist_mapping)
        print(f"Created playlist index: {index}")
    else:
        print(f"Index {index} already exists")
