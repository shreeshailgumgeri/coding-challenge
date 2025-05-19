from bucket_repo import BucketRepo
from pydub import AudioSegment
import json
import hashlib

def generate_cache_key(audio_keys):
    """
    Generate a unique cache key based on the list of audio file keys.
    Sort them to ensure consistent ordering for the same input.
    """
    key_string = json.dumps(sorted(audio_keys))
    return hashlib.sha256(key_string.encode("utf-8")).hexdigest()

def lambda_handler(event, context):
    # 1. Get bucket name and output key (can also get from event)
    bucket_name = 'pxd-audios'  
    bucket_output_name = 'pxd-output' 
    output_file = 'stitched.mp3'  

    # 2. Create the repo object
    repo = BucketRepo(bucket_name=bucket_name, bucket_output_name=bucket_output_name, output_file=output_file)

    # 3. List audio files in the S3 bucket
    audio_keys = repo.list_files()
    print("Audio files found:", audio_keys)

    if not audio_keys:
        print("No audio files to stitch.")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "message": "No audio files to stitch.",
            })
        }

    # 4. Generate a cache key and check for cached output in S3
    cache_key = generate_cache_key(audio_keys)
    cache_output_file = f'cache/{cache_key}.mp3'
    repo.output_file = cache_output_file  # set output file to cache path

    if repo.exists(cache_output_file):
        # Cache hit: return existing file's public URL
        public_url = repo.get_public_url()
        print(f"Cache hit! Returning cached stitched file at {cache_output_file}")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "message": "Stitched audio retrieved from cache!",
                "audio_files": audio_keys,
                "output_file": cache_output_file,
                "public_url": public_url,
                "cached": True
            })
        }

    # 5. Read audio files from S3 and load them with pydub
    audio_segments = []
    for key in audio_keys:
        audio_bytes = repo.read(key)
        audio_segment = AudioSegment.from_file(audio_bytes)
        audio_segments.append(audio_segment)

    # 6. Stitch audio segments together and write to S3 cache
    stitched_audio = sum(audio_segments)
    repo.write(stitched_audio)
    public_url = repo.get_public_url()
    print("Stitched audio uploaded to S3 cache!")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "success": True,
            "message": "Stitched audio uploaded to S3!",
            "audio_files": audio_keys,
            "output_file": cache_output_file,
            "public_url": public_url,
            "cached": False
        })
    }
