data "aws_sns_topic" "s3_notifications" {
  count = var.create ? 1 : 0
  name  = "537551041389-prod-data-archive-notifications"
}

module "pyodbc_layer39" {
  source     = "truemark/lambda-pyodbc-layer39-mssql/aws"
  version    = "1.1.0"
  layer_name = "${var.name}-pyodbc-layer39"
  create = var.create
}

data "aws_secretsmanager_secret" "this" {
  name = var.secret_name
}

data "aws_iam_policy_document" "this" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
    effect = "Allow"
  }
}

resource "aws_iam_role" "this" {
  count              = var.create ? 1 : 0
  assume_role_policy = data.aws_iam_policy_document.this.json
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs" {
  count      = var.create ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.this[count.index].name
}

resource "aws_iam_role_policy_attachment" "vpc_attachment" {
  count      = var.create ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.this[count.index].name
}

resource "aws_security_group" "this" {
  count = var.create ? 1 : 0
  vpc_id = var.vpc_id
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = -1
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}

data "archive_file" "this" {
  count = var.create ? 1 : 0
  type        = "zip"
  output_path = "${path.module}/lambda.zip"
  source_dir = "${path.module}/lambda"
}

resource "aws_lambda_function" "this" {
  count         = var.create ? 1 : 0
  function_name = var.name
  role          = aws_iam_role.this[count.index].arn
  layers = [module.pyodbc_layer39.lambda_layer_version_arn]
  filename = data.archive_file.this[count.index].output_path
  runtime = "python3.9"
  handler = "handler.handler"
  source_code_hash = data.archive_file.this[count.index].output_base64sha256

  environment {
    variables = {
      CREDENTIALS_SECRET_ARN = data.aws_secretsmanager_secret.this.arn
    }
  }

  vpc_config {
    security_group_ids = [aws_security_group.this[count.index].id]
    subnet_ids         = var.subnet_ids
  }
}

resource "aws_lambda_permission" "subscription" {
  count         = var.create ? 1 : 0
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this[count.index].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = data.aws_sns_topic.s3_notifications[count.index].arn
}

resource "aws_sns_topic_subscription" "subscription" {
  count     = var.create ? 1 : 0
  endpoint  = aws_lambda_function.this[count.index].arn
  protocol  = "lambda"
  topic_arn = data.aws_sns_topic.s3_notifications[count.index].arn
}
