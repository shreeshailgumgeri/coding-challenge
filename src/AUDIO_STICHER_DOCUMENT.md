# Audio Stitcher Serverless Application

## Overview

This project is a serverless application built with AWS Lambda, S3, and the Serverless Framework. It stitches together multiple audio files stored in an S3 bucket, caches the results for repeated requests using S3, and exposes an API endpoint for triggering the stitching process.

---

## Architecture

- **API Gateway**: REST endpoint for triggering the Lambda function.
- **Lambda Function**: Reads audio files from the input S3 bucket, stitches them using `pydub`, checks/creates cached outputs in the output S3 bucket, and returns a URL to the stitched file.
- **S3 Buckets**:
  - Input Bucket: Stores the source audio files.
  - Output Bucket: Stores stitched/cached results under a `cache/` prefix (with auto-expiration lifecycle policy).
- **IAM Roles**: Principle of least privilege is followed for Lambda execution.
- **CI/CD**: Automated with GitHub Actions.

---

## Features

- Stitches multiple audio files into a single file on demand.
- Caches stitched results in S3 based on request input hash to avoid redundant processing.
- Secure, environment-specific deployment (Dev/Test/Stage/Prod) with parameterized configuration.
- Automated S3 cache cleanup via lifecycle rules.
- Includes unit/integration tests for Lambda logic.

---

## Getting Started

### Prerequisites

- AWS account
- Node.js (v16+)
- Python 3.11+
- [Serverless Framework](https://www.serverless.com/) (`npm install -g serverless`)
- AWS CLI configured (`aws configure`)
- [pydub](https://github.com/jiaaro/pydub) and ffmpeg installed

### Install Dependencies

```sh
pip install -r requirements.txt
npm install
```

---

## Configuration

### Environment-based Buckets

Buckets are named with a `-${stage}` suffix for isolation.  
For example, for the `dev` stage:
- Input bucket: `pxd-audios-dev`
- Output bucket: `pxd-output-dev`

You can change these names in `serverless.yml`.

### Environment Variables

Set in `serverless.yml` and available to Lambda:

- `BUCKET_INPUT`: Name of the input S3 bucket
- `BUCKET_OUTPUT`: Name of the output/cache S3 bucket
- `CACHE_PREFIX`: Prefix for cached files (`cache/`)

---

## Deployment

Deploy to a specific environment (stage):

```sh
# Deploy to dev
serverless deploy --stage dev

# Deploy to prod
serverless deploy --stage prod
```

---

## Usage

Send a POST request to your API Gateway endpoint with:

```json
{
  "message_parts": ["audio1.mp3", "audio2.mp3"]
}
```

**Response:**
- `public_url`: The S3 URL (or presigned URL) to the stitched audio file.
- `cached`: Whether the result was returned from cache.

---

## Caching Strategy

- A hash of the sorted list of audio file keys is used as the cache key.
- If a result with the same inputs exists in S3 under `cache/`, it will be reused.
- Cache files are cleaned up automatically by S3 lifecycle rules (default: 7 days).

---

## Security

- Lambda IAM role only allows minimum required S3 actions on the specific buckets.
- No secrets or keys are stored in code or repository.
- AWS credentials for deployment are managed via environment variables or CI/CD secrets.
- Buckets are private by default; public URLs are signed.

---

## CI/CD

Automated via GitHub Actions:

- Linting, testing, and deployment on push/PR to `main`.
- AWS credentials are injected as GitHub secrets.

Example workflow: `.github/workflows/ci.yml`

---

## Testing

- Unit and integration tests in `tests/` directory.
- S3 interactions mocked using `moto`.

Run tests:

```sh
pytest tests/
```

---

## Change Control

- All changes tracked in Git (use branches and pull requests!).
- Releases are tagged (e.g., `v1.0.0`).
- Code and infrastructure-as-code (`serverless.yml`) are versioned together.

---

## Example Project Structure

```plaintext
.
├── src/
│   ├── stitch.py
│   ├── stitch_lambda.py
│   ├── bucket_repo.py
│   ├── TROUBLESHOOTING_GUIDE.md
│   ├── AUDIO_STICHER_DOCUMENT.md
├── tests/ //TODO
│   └── test_stitch.py //TODO
├── serverless.yml //TODO
├── requirements.txt
├── run.sh
├── setup.sh
├── README.md
└── .github/ //TODO
    └── workflows/
        └── ci.yml
```

---

## Contributors

- [Shreeshail G](mailto:shreeshailgumgeri@gmail.com)

---
