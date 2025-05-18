import os
import json
import logging
import boto3 as b3
import pydub as pd
import base64 as b64
import hashlib as hl
import argparse as ap
import collections as col

from datetime import datetime as dt

# Constants and configs
DEBUG_LEVEL = os.environ.get('DEBUG_LEVEL', 'WARNING')
LOGGER_NAME = os.environ.get('LOGGER_NAME', 'default')
CLEAN_CHARACTERS = "abcdefghijklmnopqrstuvwxyz1234567890 "
ALLOWED_AUDIO_FILE_EXTENSIONS = ['.mp3', '.wav']

LambdaOptions = col.namedtuple('LambdaOptions', ['message', 'audios', 'output'])
FileInfo = col.namedtuple('FileInfo', ['root', 'name', 'ext', 'fullpath', 'hash'])
StitchFile = col.namedtuple('StitchFile', ['start', 'end', 'info'])

def get_hash(binary):
    return hl.md5(binary).hexdigest()

class Repo(object):
    def __init__(self, audios, output, files=None, log=logging):
        self._audios = audios
        self._output = output
        self._files = files or []
        self.log = log

    def output(self):
        return self._output

    def files(self):
        return self._files

    def read(self, path):
        raise NotImplementedError("Repo.read must be implemented in a subclass.")

    def write(self, data):
        raise NotImplementedError("Repo.write must be implemented in a subclass.")

    def make_segments(self, paths):
        for path in paths:
            with self.read(path) as fs:
                segment = pd.AudioSegment(fs)
                yield segment

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
        
class BucketRepo(Repo):
    def __init__(self, audios, output, log=logging):
        self.s3 = b3.client('s3')
        self.bucket = audios
        self.output_key = output
        self.log = log
        files = list(self.load_files())
        super().__init__(audios, output, files, log)

    def load_files(self):
        paginator = self.s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=self.bucket):
            for obj in page.get('Contents', []):
                key = obj['Key']
                fname, fext = os.path.splitext(os.path.basename(key))
                if fext.lower() in ALLOWED_AUDIO_FILE_EXTENSIONS:
                    file_obj = self.s3.get_object(Bucket=self.bucket, Key=key)
                    data = file_obj['Body'].read()
                    fhash = get_hash(data)
                    yield FileInfo(self.bucket, fname, fext, key, fhash)

    def read(self, path):
        import io
        obj = self.s3.get_object(Bucket=self.bucket, Key=path)
        return io.BytesIO(obj['Body'].read())

    def write(self, stitched):
        import io
        buf = io.BytesIO()
        stitched.export(buf, format="mp3")
        buf.seek(0)
        self.s3.put_object(Bucket=self.bucket, Key=self.output_key, Body=buf.getvalue())
        return True

def lmbd_options(event, log=logging):
    try:
        body = event.get('body')
        if body is None:
            raise ValueError("Missing 'body' in event.")
        if isinstance(body, str):
            body = json.loads(body)
        message = body.get('message')
        audios = body.get('audios')
        output = body.get('output')
        if not all([message, audios, output]):
            raise ValueError("Missing one or more required fields: message, audios, output.")
        return LambdaOptions(message, audios, output)
    except Exception as e:
        log.error(f"Error parsing Lambda options: {e}")
        raise

def main(message, repo, log=logging):
    try:
        files = repo.files()
        clean_message = ''.join([c for c in message.lower() if c in CLEAN_CHARACTERS])
        stitch_files = []
        for file in files:
            import re
            found = re.search(file.name, clean_message)
            if found:
                stitch_files.append(StitchFile(found.start(), found.end(), file))
        if not stitch_files:
            log.warning("No audio segments matched the message.")
            return {"success": False, "reason": "No matching audio segments found."}

        ordered_files = [f.info.fullpath for f in sorted(stitch_files, key=lambda f: f.start)]
        stitched = sum(repo.make_segments(ordered_files))
        repo.write(stitched)
        return {
            "success": True,
            "output_location": repo.output(),
            "segments_used": [f.info.fullpath for f in stitch_files]
        }
    except Exception as e:
        log.error(f"Error in main(): {e}")
        return {"success": False, "error": str(e)}

def lambda_handler(event, context):
    logging.basicConfig()
    log = logging.getLogger(LOGGER_NAME)
    try:
        options = lmbd_options(event, log=log)
        repo = BucketRepo(audios=options.audios, output=options.output, log=log)
        result = main(message=options.message, repo=repo, log=log)
        status_code = 200 if result.get("success") else 400
        return {"statusCode": status_code, "body": json.dumps(result)}
    except Exception as e:
        log.error(f"lambda_handler error: {e}")
        return {"statusCode": 500, "body": json.dumps({"success": False, "error": str(e)})}
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audio Stitcher")
    parser.add_argument("--message", "-m", required=True, help="Message to stitch")
    parser.add_argument("--audios", "-a", required=True, help="Directory with audio files")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    args = parser.parse_args()

    # Use LocalRepo if you want to work with local files!
    repo = LocalRepo(audios=args.audios, output=args.output)
    result = main(message=args.message, repo=repo)
    print(result)
