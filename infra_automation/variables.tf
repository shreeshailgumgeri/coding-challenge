variable "aws_region" {
  description = "AWS region to deploy resources in"
  type        = string
  default     = "ap-south-1"
}

variable "stage" {
  description = "Deployment environment (dev, test, stage, prod, etc.)"
  type        = string
  default     = "dev-v1"
}

variable "input_bucket_name" {
  description = "Name of the input S3 bucket"
  type        = string
}

variable "output_bucket_name" {
  description = "Name of the output S3 bucket"
  type        = string
}

variable "lambda_package" {
  description = "Path to the Lambda deployment package (zip file)"
  type        = string
}