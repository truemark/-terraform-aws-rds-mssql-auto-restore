resource "aws_iam_role_policy_attachment" "lambda_policy_secrets" {
  count      = var.create ? 1 : 0
  role       = aws_iam_role.this[count.index].name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

resource "aws_iam_policy" "lambda_policy" {
  name = "${var.name}-execution"
  tags = var.tags

  policy = jsonencode({
    Version = "2012-10-17"
    "Statement" : [
      {
        "Sid" : "secretsmgr",
        "Effect" : "Allow",
        "Action" : [
          "secretsmanager:GetSecretValue"
        ],
        "Resource" : "arn:aws:secretsmanager:${var.region_name}:${data.aws_caller_identity.current.account_id}:secret:database/*"
      },
      {
        "Sid" : "smlist",
        "Effect" : "Allow",
        "Action" : "secretsmanager:ListSecrets",
        "Resource" : "*"
      }
    ]
  })

}
