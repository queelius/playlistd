playlist_mapping = {
    "mappings": {
        "properties": {
            "title": { "type": "text" },
            "original_playlist_url": { "type": "text", "index": False },
            "original_owner_url": { "type": "text", "index": False },
            "description": { "type": "text" },
            "video_ids": { "type": "keyword" },
            "comments": { "type": "text" },
            "likes": { "type": "integer" },
            "views": { "type": "integer" }
        }
    }
}

video_mapping = {
    "mappings": {
        "properties": {
            "original_playlist_url": { "type": "text", "index": False },
            "original_owner_url": { "type": "text", "index": False },
            "comments": { "type": "text" },
            "likes": { "type": "integer" },
            "views": { "type": "integer" },
            "url": { "type": "text", "index": False },
            "title": { "type": "text" },
            "description": { "type": "text" }
        }
    }
}


#def initialize_indexes(es: Elasticsearch):
#    def initialize_mapping(index_name, mapping):
#        try:
#            if not es.indices.exists(index=index_name):
#                es.indices.create(index=index_name, body=mapping)
#                print(f"Created index: {index_name}")
#            else:
#                print(f"Index {index_name} already exists")
#        except exceptions.ElasticsearchException as e:
#            print(f"Error creating index {index_name}: {str(e)}")##

#    initialize_mapping(environ['VIDEO_INDEX'], video_mapping)
#    initialize_mapping(environ['PLAYLIST_INDEX'], playlist_mapping)
