import os
import re
import json
import logging

import boto3 as b3
import pydub as pd
import base64 as b64
import hashlib as hl
import argparse as ap
import collections as col

from datetime import datetime as dt

# here we set global constants and variables
DEBUG_LEVEL=os.environ.get('DEBUG_LEVEL') if os.environ.get('DEBUG_LEVEL') else logging.WARNING
LOGGER_NAME=os.environ.get('LOGGER_NAME') if os.environ.get('LOGGER_NAME') else 'default'
CLEAN_CHARACTERS="abcdefghijklmnopqrstuvwxyz1234567890 "
ALLOWED_AUDIO_FILE_EXTENSIONS=['.mp3','.wav']

# here we define custom classes or named tuples
LambdaOptions=col.namedtuple('LambdaOptions',['message','audios','output'])
FileInfo=col.namedtuple('FileInfo',['root','name','ext','fullpath','hash'])
StitchFile=col.namedtuple('StitchFile',['start','end','info'])

class Repo(object):
    def __init__(self,audios,output,files=[],log=logging):
        print(f'initializing repo with audios path {audios} and output file path {output}')
        self.__audios=audios
        self.__output=output
        self.__files=files

    def output(self):
        return self.__output

    def files(self,log=logging):
        print(f'getting self.__files in Repo with {len(self.__files)} total files')
        return self.__files

    def read(self,path,log=logging):
        print(f'Called Repo.read for path: {path}')
        raise('Not implemented')

    def write(self,data):
        print('Called Repo.write')
        raise('Not implemented')

    def make_segments(self,paths,log=logging):
        print(f'Entering make_segments with paths: {paths}')
        for path in paths:
            print(f'About to read file {path}')
            with self.read(path) as fs:
                print(f'generating audio segment for {path}')
                segment=pd.AudioSegment(fs)
                print(f'returning audio segment for {path}')
                yield segment
        print('Exiting make_segments')
class BucketRepo(Repo):
    def __init__(self, audios, output, log=logging):
        print(f'initializing BucketRepo with S3 bucket {audios} and output key {output}')
        self.s3 = b3.client('s3')
        self.bucket = audios  # 'audios' is the S3 bucket name
        self.output_key = output  # S3 key for output file

        print('Loading files from S3 bucket...')
        self.__files = [f for f in self.load_files(self.bucket, log=log)]
        print(f'found {len(self.__files)} audio files in S3 bucket {audios}')
        super().__init__(audios=audios, output=output, files=self.__files, log=log)

    def load_files(self, bucket, log=logging):
        print(f'Entering load_files for bucket: {bucket}')
        paginator = self.s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket):
            for obj in page.get('Contents', []):
                key = obj['Key']
                fname, fext = os.path.splitext(os.path.basename(key))
                print(f'Checking file {key} with extension {fext}')
                if fext.lower() in ALLOWED_AUDIO_FILE_EXTENSIONS:
                    print(f'File {key} is allowed, downloading...')
                    file_obj = self.s3.get_object(Bucket=bucket, Key=key)
                    data = file_obj['Body'].read()
                    fhash = get_hash(data)
                    print(f'File {key} hash: {fhash}')
                    yield FileInfo(bucket, fname, fext, key, fhash)
                else:
                    print(f'rejecting {key} since {fext} is not allowed')
        print('Exiting load_files')

    def read(self, path, log=logging):
        print(f'reading S3 object {path} from bucket {self.bucket}')
        obj = self.s3.get_object(Bucket=self.bucket, Key=path)
        import io
        print(f'Successfully read S3 object {path}')
        return io.BytesIO(obj['Body'].read())

    def write(self, stitched, log=logging):
        print(f'writing stitched audio to S3 bucket {self.bucket} with key {self.output_key}')
        import io
        buf = io.BytesIO()
        stitched.export(buf, format="mp3")
        buf.seek(0)
        self.s3.put_object(Bucket=self.bucket, Key=self.output_key, Body=buf.getvalue())
        print('Successfully wrote stitched audio to S3')
        return True

class LocalRepo(Repo):
    def __init__(self, audios, output, log=logging):
        print(f'initializing local repo')
        print(f'enumerating files...')
        self.__files=[f for f in self.load_files(audios, log=log)]
        print(f'found {len(self.__files)} audio files in {audios} directory')
        super().__init__(audios=audios, output=output, files=self.__files, log=log)

    def load_files(self,dir,log=logging):
        print(f'Entering load_files for dir: {dir}')
        for file in os.listdir(dir):
            fname,fext=os.path.splitext(file)
            fullpath=os.path.join(dir,file)
            print(f'found file {fullpath} with extension {fext} in dir {dir} with name {fname}')
            if fext in ALLOWED_AUDIO_FILE_EXTENSIONS:
                print(f'File {fullpath} is allowed, opening...')
                with open(fullpath,'rb') as fs:
                    fhash=get_hash(fs.read())
                    result = FileInfo(dir,fname,fext,fullpath,fhash)
                    print(f'processed file {result}')
                    yield result
            else:
                print(f'rejecting {fullpath} since {fext} it\'s not one of {ALLOWED_AUDIO_FILE_EXTENSIONS}')
        print('Exiting load_files')
            
    def read(self,path,log=logging):
        print(f'opening file stream for {path}')
        return open(path,'rb')
    
    def write(self,stitched,log=logging):
        output=Repo.output(self)
        print(f'writing data to {output}')
        stitched.export(output)
        print('Successfully wrote stitched audio to local file')
        return True

# here we define helper functions
def get_hash(binary):
    print('Calculating hash')
    return hl.md5(binary).hexdigest()

def cmd_options(log=logging):
    print('Parsing command line options')
    parser=ap.ArgumentParser('audio stitcher',usage='stitcher --message "hello, name" --audios ./audios --output ./hello_name.mp3')
    parser.add_argument('-m','--message',required=True)
    parser.add_argument('-a','--audios',required=True)
    parser.add_argument('-o','--output',required=True)
    args = parser.parse_args()
    print(f'Parsed options: {args}')
    return args

def lmbd_options(event,log=logging):
    print('Parsing lambda event options')
    body=json.loads(event.get('body'))
    message=body.message
    audios=body.audios
    output=body.output
    print(f'Parsed lambda options: message={message}, audios={audios}, output={output}')
    return LambdaOptions(message,audios,output)

# this is our main logic
def main(message,repo,log=logging):
    print('Entering main with message:',message)    
    print(f'Entering main with message: {message}')
    files=repo.files()
    print(f'found {len(files)} files to stitch')    
    print(f'will search {len(files)} to determine if message can be stitched')
    clean_message=re.sub('\\s+',' ',''.join([c for c in message.lower() if c in CLEAN_CHARACTERS]))
    print(f'took {message} and cleaned it to {clean_message}')
    stitch_files=[]
    print("files : ",files)
    for file in files:
        print(f'looking for {file.name} in {clean_message}')
        found=re.search(file.name,clean_message)
        if found:
            print(f'found match for {file.name} in position {found.start()}')
            stitch_files.append(StitchFile(found.start(),found.end(),file))
        else:
            print(f'---- no match for {file.name} in {clean_message}')        
    print(f'found {len(stitch_files)} files to be used for the stitched audio {repo.output()}')
    print(f'Stitch files: {stitch_files}')
    stiched=sum(repo.make_segments([f.info.fullpath for f in sorted(stitch_files,key=lambda f: f.start)], log=log))
    print('Stitching complete, writing output...')
    repo.write(stiched)
    print('Exiting main')
    return True

# this is our lambda context handler
def lambda_handler(event,context):
    logging.basicConfig()
    logging.getLogger().setLevel(DEBUG_LEVEL)
    log = logging.getLogger(LOGGER_NAME)
    print('Lambda handler started')
    ops=lmbd_options(event,log=log)
    print(f'Lambda options: {ops}')
    result = main(message=ops.message,repo=BucketRepo(audios=ops.audios,output=ops.output, log=log),log=log)
    print('Lambda handler finished')
    return {"statusCode": 200, "body": result }

# this is our local context handler
if __name__=='__main__':
    logging.basicConfig()
    logging.getLogger().setLevel(DEBUG_LEVEL)
    log = logging.getLogger(LOGGER_NAME)
    print('Starting script')    
    print('Script started')
    ops=cmd_options(log=log)
    print(f'Command line options: {ops}')   
    print(f'Command line options: {ops}')
    # main(message=ops.message,repo=LocalRepo(audios=ops.audios,output=ops.output, log=log),log=log)
    main(message=ops.message,repo=BucketRepo(audios=ops.audios,output=ops.output, log=log),log=log)
    print('Script finished')    
    print('Script finished')


git remote add origin https://github.com/{your_github_username}/coding_challenge.git
git add .
git commit -m "Initial commit"
git push -u origin master