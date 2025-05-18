import json
from stitch import lambda_handler

event = {
    "body": json.dumps({
        "message": "hello world",
        "audios": "my-audio-bucket",
        "output": "output/hello_world.mp3"
    })
}
context = {}  # Lambda context object is not used

response = lambda_handler(event, context)
print(response)