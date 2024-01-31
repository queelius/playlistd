#!/bin/bash

# Elasticsearch URL
ELASTICSEARCH_URL="http://localhost:9200"

# Function to generate a comma-separated list of video IDs
generate_video_id_list() {
    local num_videos=$1
    local start_id=$2
    local video_ids=()

    for ((i=0; i<num_videos; i++)); do
        video_ids+=("\"video$((start_id + i))\"")
    done

    echo $(IFS=, ; echo "${video_ids[*]}")
}

# Function to generate fake playlist data
generate_playlist_data() {
    local id=$1
    local video_ids=$2
    echo '{
        "title": "Fake Playlist '$id'",
        "description": "Description for Fake Playlist '$id'",
        "video_ids": ['$video_ids'],
        "likes": 10,
        "views": 100
    }'
}

# Function to generate fake video data
generate_video_data() {
    local id=$1
    echo '{
        "url": "http://example.com/video/'$id'",
        "title": "Fake Video '$id'",
        "description": "Description for Fake Video '$id'",
        "likes": 5,
        "views": 50
    }'
}

# Number of documents to generate
NUM_PLAYLISTS=5
NUM_VIDEOS_PER_PLAYLIST=5
NUM_TOTAL_VIDEOS=$((NUM_PLAYLISTS * NUM_VIDEOS_PER_PLAYLIST))

# Generate and post fake video data
for i in $(seq 1 $NUM_TOTAL_VIDEOS); do
    video_data=$(generate_video_data "$i")
    curl -X POST "$ELASTICSEARCH_URL/video_index/_doc/$i" -H 'Content-Type: application/json' -d "$video_data"
    echo " - Uploaded video $i"
done

# Generate and post fake playlist data
for i in $(seq 1 $NUM_PLAYLISTS); do
    start_id=$(( (i - 1) * NUM_VIDEOS_PER_PLAYLIST + 1 ))
    video_id_list=$(generate_video_id_list $NUM_VIDEOS_PER_PLAYLIST $start_id)
    playlist_data=$(generate_playlist_data "$i" "$video_id_list")
    curl -X POST "$ELASTICSEARCH_URL/playlist_index/_doc/$i" -H 'Content-Type: application/json' -d "$playlist_data"
    echo " - Uploaded playlist $i"
done

echo "Fake data generation complete."
