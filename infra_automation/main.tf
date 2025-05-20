terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
  required_version = ">= 1.3.0"

  backend "s3" {
    bucket  = "pxd-terraform-state-dev"            # Use your dedicated state bucket name
    key     = "infra_automation/terraform.tfstate" # Path in the bucket
    region  = "ap-south-1"                         # Your AWS region
    encrypt = true                                 # Encrypt state at rest
  }
}


provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "input" {
  bucket = var.input_bucket_name
}

resource "aws_s3_bucket" "output" {
  bucket = var.output_bucket_name
}

resource "aws_s3_bucket_lifecycle_configuration" "output_lifecycle" {
  bucket = aws_s3_bucket.output.id

  rule {
    id     = "expire_cache"
    status = "Enabled"

    filter {
      prefix = "cache/"
    }

    expiration {
      days = 7
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name = "lambda-audio-stitcher-exec-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "lambda_policy" {
  name        = "lambda-audio-stitcher-policy-${var.stage}"
  description = "Policy for Lambda to access S3 buckets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.input_bucket_name}",
          "arn:aws:s3:::${var.input_bucket_name}/*",
          "arn:aws:s3:::${var.output_bucket_name}",
          "arn:aws:s3:::${var.output_bucket_name}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_lambda_function" "stitch" {
  function_name = "audio-stitcher-${var.stage}"
  s3_bucket     = "pxd-ffmpeg-layer"
  s3_key        = "ffmpeg-layer.zip"
  handler       = "stitch.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec.arn
  filename      = var.lambda_package

  environment {
    variables = {
      BUCKET_INPUT  = var.input_bucket_name
      BUCKET_OUTPUT = var.output_bucket_name
      CACHE_PREFIX  = "cache/"
    }
  }

  timeout = 60
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stitch.arn
  principal     = "apigateway.amazonaws.com"
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "audio-stitcher-api-${var.stage}"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.stitch.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "stitch_route" {
  api_id    = aws_apigatewayv2_api.http_api.id
  route_key = "POST /stitch"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true
}

output "api_endpoint" {
  value = aws_apigatewayv2_api.http_api.api_endpoint
}