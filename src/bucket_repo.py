import boto3
import io
from botocore.exceptions import ClientError

class BucketRepo:
    def __init__(self, bucket_name, bucket_output_name, output_file, log=None):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name
        self.bucket_output = bucket_output_name
        self.output_file = output_file
        self.log = log

    def list_files(self, prefix=''):
        """List all audio files in the bucket (optionally filter by prefix)."""
        paginator = self.s3.get_paginator('list_objects_v2')
        files = []
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix):
            for obj in page.get('Contents', []):
                key = obj['Key']
                if key.endswith('.wav') or key.endswith('.mp3'):
                    files.append(key)
        return files

    def read(self, key):
        """Read an audio file from S3 and return as a byte-stream."""
        obj = self.s3.get_object(Bucket=self.bucket, Key=key)
        return io.BytesIO(obj['Body'].read())

    def write(self, stitched_audio):
        """Write a stitched audio (pydub.AudioSegment) to S3 as mp3."""
        buf = io.BytesIO()
        stitched_audio.export(buf, format="mp3")
        buf.seek(0)
        self.s3.put_object(Bucket=self.bucket_output, Key=self.output_file, Body=buf.getvalue())
        return True
    
    def get_public_url(self, expires_in=3600):
        """Generate a pre-signed URL for the stitched audio file."""
        url = self.s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket_output,
                'Key': self.output_file
            },
            ExpiresIn=expires_in
        )
        return url
    
    def exists(self, key):
        """Check if a given key exists in the S3 bucket."""
        try:
            self.s3.head_object(Bucket=self.bucket_output, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise