# Troubleshooting Guide: Packaging and Using FFmpeg/FFprobe in AWS Lambda Layers

This document summarizes common issues faced when building and deploying FFmpeg/ffprobe as an AWS Lambda Layer, along with practical solutions for each.

---

## **Table of Contents**
1. [Cannot Install ffmpeg via yum](#cannot-install-ffmpeg-via-yum)
2. [yum Repository Errors (aarch64/ARM64)](#yum-repository-errors-aarch64arm64)
3. [tar or xz Not Installed in Docker](#tar-or-xz-not-installed-in-docker)
4. [Lambda Layer Upload Size Limit Exceeded (50 MB)](#lambda-layer-upload-size-limit-exceeded-50-mb)
5. [Lambda Layer Exec Format Error or Permission Denied](#lambda-layer-exec-format-error-or-permission-denied)
6. [ffmpeg/ffprobe Not Found at Runtime](#ffmpegffprobe-not-found-at-runtime)
7. [Other Tips & References](#other-tips--references)

---

## 1. Cannot Install ffmpeg via yum

**Symptom:**  
```
No package ffmpeg available.
Error: Nothing to do
```

**Root Cause:**  
- Amazon Linux 2’s default repositories do **not** provide `ffmpeg` directly.
- EPEL may be missing or not provide the needed package.

**Solution:**  
- Use a static build of ffmpeg/ffprobe (see section 4).
- Or, use a newer base image (e.g., `amazonlinux:2023`) that includes ffmpeg.

---

## 2. yum Repository Errors (aarch64/ARM64)

**Symptom:**  
Errors like:
```
Could not retrieve mirrorlist ... error was 14: HTTP Error 404 - Not Found
Cannot find a valid baseurl ...
```

**Root Cause:**  
- You are building on ARM64 (`aarch64`), but most Lambda environments use x86_64 (`amd64`).
- The ARM64 repositories are incomplete or not maintained.

**Solution:**  
- Always build the layer using the **x86_64/amd64** architecture.
    - On Docker:  
      ```bash
      docker run --platform linux/amd64 -it amazonlinux:2 bash
      ```
- If you are on Apple Silicon (M1/M2), this is especially important.

---

## 3. tar or xz Not Installed in Docker

**Symptom:**  
```
bash: tar: command not found
tar (child): xz: Cannot exec: No such file or directory
```

**Solution:**  
Install missing tools in your Docker container:
```bash
yum install -y tar xz
```

---

## 4. Lambda Layer Upload Size Limit Exceeded (50 MB)

**Symptom:**  
- "The selected file is too large. The maximum size is 50 MB."
- Your zip file (e.g., `ffmpeg-layer.zip`) is over 50 MB.

**Solution:**  
- **Use S3 Upload:**  
  1. Upload your large ZIP to an S3 bucket in the same region.
  2. In the Lambda Layer creation screen, choose "Upload a file from Amazon S3."
  3. Enter the S3 URI (e.g., `s3://your-bucket/ffmpeg-layer.zip`).
- **Reduce Size (Optional):**
  - Remove unnecessary files (docs, licenses, etc.) from the layer.
  - Compress binaries with [UPX](https://github.com/upx/upx).

---

## 5. Lambda Layer Exec Format Error or Permission Denied

**Symptoms:**  
- "Exec format error"
- "Permission denied"

**Causes/Solutions:**  
- **Exec format error:**  
  - The binaries are for the **wrong architecture**. Always use amd64/x86_64 for Lambda unless your function is configured for ARM64.
- **Permission denied:**  
  - The binaries are not executable. Run:
    ```bash
    chmod +x ffmpeg-layer/bin/ffmpeg ffmpeg-layer/bin/ffprobe
    ```

---

## 6. ffmpeg/ffprobe Not Found at Runtime

**Symptom:**  
- "No such file or directory: 'ffmpeg' or 'ffprobe'"

**Solution:**  
- Lambda layers are mounted at `/opt`.  
- Ensure your Lambda code can find `ffmpeg` and `ffprobe` by adding `/opt/bin` to the PATH.

**Example (Python):**
```python
import os
os.environ["PATH"] += os.pathsep + "/opt/bin"
```

---

## 7. Other Tips & References

- **Copying binaries from Docker:**  
  Use `docker cp` to copy files from the running container to your host:
  ```bash
  docker cp <container_id>:/tmp/ffmpeg .
  docker cp <container_id>:/tmp/ffprobe .
  ```
- **Public Lambda Layers:**  
  Consider using a public Lambda Layer ARN for ffmpeg/ffprobe if available and trusted.

- **Useful Links:**
  - [johnvansickle.com static ffmpeg builds](https://johnvansickle.com/ffmpeg/)
  - [AWS Lambda Layer documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
  - [UPX Binary Compressor](https://github.com/upx/upx)

---

## **Summary Table**

| Problem                               | Solution                                             |
|----------------------------------------|------------------------------------------------------|
| ffmpeg not in yum/EPEL                 | Use static build or Amazon Linux 2023 image          |
| Repo errors (aarch64/ARM64)            | Force Docker to use x86_64/amd64 platform            |
| tar/xz missing in Docker               | `yum install -y tar xz`                              |
| Zip > 50MB                             | Upload via S3 or reduce size                         |
| Exec format error                      | Use correct (x86_64) binary                          |
| Permission denied                      | `chmod +x` on binaries                               |
| ffmpeg/ffprobe not found in Lambda     | Add `/opt/bin` to PATH in your Lambda code           |

---

**If you hit an error not listed here, capture the full error message and environment details for further troubleshooting.**
