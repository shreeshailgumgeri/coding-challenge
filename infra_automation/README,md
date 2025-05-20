# Audio Stitcher Infrastructure and Deployment

This README documents the process and steps followed to set up an AWS Lambda-based audio stitching backend, including infrastructure-as-code with Terraform and deployment via CI/CD using Github Action.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Infrastructure Overview](#infrastructure-overview)
- [Lambda Packaging & Deployment](#lambda-packaging--deployment)
- [API Gateway Integration](#api-gateway-integration)
- [GitHub CI/CD Contribution](#github-cicd-contribution)
- [Directory Structure](#directory-structure)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)


---

## Project Overview

This project provides an audio stitching backend using AWS Lambda, invoked via HTTP API Gateway. The Lambda function uses the `ffmpeg` binary (bundled with the deployment package) to process audio files, and stores input/output audio in S3 buckets.

---

## Infrastructure Overview

Infrastructure is managed via [Terraform](https://www.terraform.io/), and includes:

- **AWS Lambda Function**  
  Handles audio stitching logic (Python 3.11).
- **API Gateway (HTTP API v2)**  
  Exposes a secure HTTP POST endpoint : [Link](https://alnsxs4duwimivhdmxxc5ic6gu0jnczo.lambda-url.ap-south-1.on.aws/)
- **S3 Buckets**  
  For audio input and output.
- **IAM Roles and Policies**  
  Grant Lambda access to S3 and execution rights.

### Key Terraform Components

- `aws_lambda_function.stitch`
- `aws_apigatewayv2_api.http_api`
- `aws_s3_bucket.input` / `aws_s3_bucket.output`

---

## Lambda Packaging & Deployment

### Packaging

- Bundle your Python source files (`stich_lambda.py`, `bucket_repo.py`, etc.) at the root of the ZIP.
- Include the `bin/` directory with `ffmpeg` and `ffprobe` tools at the same level.

**Example Structure in ZIP:**
```
stich_lambda.py
bucket_repo.py
bin/
  ffmpeg
  ffprobe
```

**Packaging Command Example:**
```sh
cd src
zip -r ../audio_stitcher.zip stich_lambda.py bucket_repo.py
cd ..
zip -r audio_stitcher.zip bin/
```
*(Or use a single zip command if all files are in one folder.)*

### Deployment

- **Upload the ZIP to S3**:
  ```sh
  aws s3 cp audio_stitcher.zip s3://<your-s3-bucket>/ffmpeg-layer.zip --region ap-south-1
  ```
- **Update Lambda code** (via CI/CD or CLI):
  ```sh
  aws lambda update-function-code \
    --function-name audio-stitcher-dev \
    --s3-bucket <your-s3-bucket> \
    --s3-key ffmpeg-layer.zip \
    --region ap-south-1
  ```

- **Terraform deployment**:
  ```sh
  terraform apply -auto-approve -var-file=dev.tfvars
  ```

---

## API Gateway Integration

- API Gateway is configured to route `POST /stitch` requests to the Lambda function.
- Only `POST` requests to `/stitch` are accepted.
- Example endpoint (from Terraform output):
  ```
  https://qz9jbbsjr2.execute-api.ap-south-1.amazonaws.com/stitch
  ```

---

## How to Use the Endpoint

### Example Request

```sh
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{ "audio_url": "https://example.com/audio.mp3" }' \
  https://qz9jbbsjr2.execute-api.ap-south-1.amazonaws.com/stitch
```

- Replace the payload with the JSON structure your Lambda expects.
- Only the `/stitch` path with POST method is valid; other paths/methods return `{"message":"Not Found"}`.

---

## GitHub CI/CD Contribution

This repository leverages **GitHub Actions** for automated deployment and infrastructure management:

- **CI/CD Workflow Highlights:**
  - On push, GitHub Actions builds and packages the Lambda deployment artifact.
  - The workflow uploads the artifact to an S3 bucket (to support Lambda's deployment size limits).
  - The workflow then triggers an update of the Lambda function code using the S3 artifact.
  - Terraform is run in a dedicated step to provision and update AWS infrastructure.
  - Secrets (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) are securely managed via GitHub repository secrets.

**Sample CI/CD Workflow Step:**
```yaml
- name: Upload Lambda package to S3
  working-directory: infra_automation
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    aws s3 cp build/audio_stitcher.zip s3://your-s3-bucket/audio_stitcher.zip --region ap-south-1

- name: Deploy Lambda function code from S3
  working-directory: infra_automation
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    aws lambda update-function-code \
      --function-name audio-stitcher-dev \
      --s3-bucket your-s3-bucket \
      --s3-key audio_stitcher.zip \
      --region ap-south-1
```
- Replace `your-s3-bucket` with the actual S3 bucket name.
- Terraform apply is triggered as part of the pipeline for infrastructure updates.

**How to contribute:**  
- Fork and clone the repo.
- Make changes or improvements.
- Open a pull request—CI/CD will validate and deploy changes automatically upon merging.

---

## Directory Structure

Your project should be organized as follows:

```
project-root/
├── bin/
│   ├── ffmpeg
│   └── ffprobe
├── src/
│   ├── stich_lambda.py
│   └── bucket_repo.py
├── audio_stitcher.zip
├── infra_automation/
│   └── ... (Terraform files)
├── .github/
│   └── workflows/
│       └── ci.yaml
└── ...
```

---

## Troubleshooting

- **Not Found Error:**  
  Make sure you are sending a POST to `/stitch`. Only this route is mapped in API Gateway.

- **Lambda Not Using Your Code:**  
  Ensure your deployment ZIP contains Python files at the root (not in a subdirectory) along with the `bin` directory.

- **Large Package Error:**  
  Deploy via S3, not direct upload, for packages >50MB.

- **Handler Error:**  
  Set Lambda handler to `stich_lambda.lambda_handler` (if your file is `stich_lambda.py` and function is `lambda_handler`).

---
## Credits

- Infrastructure setup and troubleshooting: Shreeshail G

---
