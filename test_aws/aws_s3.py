# Python program to list files in S3
import os
import boto3
import hashlib as hl
import collections as col

ALLOWED_AUDIO_FILE_EXTENSIONS=['.mp3','.wav']
FileInfo=col.namedtuple('FileInfo',['root','name','ext','fullpath','hash'])

# here we define helper functions
def get_hash(binary):
    print('Calculating hash')
    return hl.md5(binary).hexdigest()

def list_files(bucket_name, prefix=""):
    s3 = boto3.client('s3')
    # response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    print(f'Entering load_files for bucket: {bucket}')
    print('Files in bucket:BEFORE')
    files = s3.list_objects_v2(Bucket=bucket_name, Prefix="")
    print('Files in bucket:')
    for f in files.get('Contents', []):
        print(f)    
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            key = obj['Key']
            fname, fext = os.path.splitext(os.path.basename(key))
            print(f'Checking file {key} with extension {fext}')
            if fext.lower() in ALLOWED_AUDIO_FILE_EXTENSIONS:
                print(f'File {key} is allowed, downloading...')
                file_obj = s3.get_object(Bucket=bucket, Key=key)
                data = file_obj['Body'].read()
                fhash = get_hash(data)
                print(f'File {key} hash: {fhash}')
                # yield FileInfo(bucket, fname, fext, key, fhash)
            else:
                print(f'rejecting {key} since {fext} is not allowed')
    print('Exiting load_files')
    
    # if 'Contents' in response:
    #     return [obj['Key'] for obj in response['Contents']]
    # else:
    #     return []

# def load_files(self, bucket, log=logging):
#     print(f'Entering load_files for bucket: {bucket}')
#     print('Files in bucket:BEFORE')
#     files = self.s3.list_objects_v2(Bucket=self.bucket, Prefix="")
#     print('Files in bucket:')
#     for f in files.get('Contents', []):
#         print(f)    
#     paginator = self.s3.get_paginator('list_objects_v2')
#     for page in paginator.paginate(Bucket=bucket):
#         for obj in page.get('Contents', []):
#             key = obj['Key']
#             fname, fext = os.path.splitext(os.path.basename(key))
#             print(f'Checking file {key} with extension {fext}')
#             if fext.lower() in ALLOWED_AUDIO_FILE_EXTENSIONS:
#                 print(f'File {key} is allowed, downloading...')
#                 file_obj = self.s3.get_object(Bucket=bucket, Key=key)
#                 data = file_obj['Body'].read()
#                 fhash = get_hash(data)
#                 print(f'File {key} hash: {fhash}')
#                 yield FileInfo(bucket, fname, fext, key, fhash)
#             else:
#                 print(f'rejecting {key} since {fext} is not allowed')
#     print('Exiting load_files')
    
def download_file(bucket_name, key, download_path):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    s3 = boto3.client('s3')
    s3.download_file(bucket_name, key, download_path)

# Example usage:
if __name__ == "__main__":
    bucket = "pxd-challenge"
    prefix = ""  # Optional: specify folder/prefix
    files = list_files(bucket, prefix)
    print("Files in bucket:")
    # for f in files:
    #     print(f)
    #     # Download each file
    #     download_file(bucket, f, f)