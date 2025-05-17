# AWS/Python Technical Assessment

## Setup

In a linux terminal where python is installed and available, run:

```bash
bash setup.sh
```

Then record two audio files:

`hello.wav`: Say "hello" in this audio file
`shreeshail.wav`: Say your name in this audio file

Save them to `./audios` and execute:

```bash
bash run.sh
```

That will generate an audio file called `hello__shreeshail.mp3` which is a stitched audio of `hello.wav` and `shreeshail.wav`.

Try running the `stitch.py` script with different messages (once you record the appropriate audio files).

## How it works

The `stitch.py` script when running locally takes as input a text message, a root audio file directory, and the full file path of the stitched audio file that will be generated from the text message.

Once the input paramters are provided, it will generate a repository (in this case a local reposity) that
will be used to list all of the files in the root audio file directory.  It will also be used to load the
audio file contents and to save the stitched audio file.

There is some additional complexity and helper functions.

## Test

As part of our interview process, we have a programming challenge. The goal is for you to become familiar with the technology we use and demonstrate your engineering proficiency.

Your first task is to add code to the BucketRepo class so that it works when called from an AWS lambda function.

The `lambda_handler` function, as the name implies, is the signature that should be used in the lambda.

You will need to add the lambda layers necessary to include the libraries specified in requirements.txt.
The lambda should return the success/failure of creating the stitched audio file, OR, the auctual stitched
audio file contents (extra bonus points for this).

Once you have completed it the code, or during as you prefer, you should deploy the lambda to AWS, provide the proper permissions so that it can perform its work, and allow it to be accessible via a public API.

You can write the necessary steps and actions required to do this, record yourself doing it, or if you would like extra points, use one of the various tools to deploy the lambda (e.g. terraform, zip file, etc.)

Your final task, if you choose to accept it, is to make the lambda publicly accessible through an API endpoint.  PxD staff should be able to call it using a curl command.  Extra points for making this API and the lambda calls secure.


Additional bonus points and tasks:

1) Add functionality to cache already stitched messages.

2) Use software engineering best practices to document your work and prepare it for deployment in one or more environments.  Hint: change control, CI/CD, etc.

3) EXTRA SUPER BONUS: Make all your infrastructure and code deployable to Dev/Test/Stage/Prod environments with appropriate security AND a test suite which tests functionality (unit tests, integration tests, functional tests) before and after the deployment (as appropriate)
