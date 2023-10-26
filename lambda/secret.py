import boto3
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_secret(in_db_name=None, in_account_name=None, in_source_db_secret_name=None, in_source_db_secret_arn=None):

    secret_value = None
    get_secret_value_response = None

    # TODO: get rid of hard coded region name
    client = boto3.client(service_name="secretsmanager")

    # secret_name = in_source_db_secret_name

    # If we know exactly which secret to retrieve, pull that one.

    # This function works when either secret name or secret arn
    # is passed in as the SecretId.
    secret_id = in_source_db_secret_arn if in_source_db_secret_arn is not None else in_source_db_secret_name

    if secret_id != None:
        try:
            logger.info(f"Starting to access secret {secret_id}\n")
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_id
            )
            return get_secret_value_response['SecretString']
        except Exception as e:
            logger.critical(
                f"Error decrypting specific secret {secret_id}: {e}\n")
            exit(1)

    else:

        # List secrets and search for the first match.
        # This could be improved by considering tags, versions, etc.
        secret_lists = client.get_paginator("list_secrets").paginate(
            PaginationConfig={"MaxItems": 100}
        )

        try:
            for secret_list in secret_lists:
                secrets = secret_list["SecretList"]

                for secret in secrets:
                    if secret["Name"].startswith(f"database/{in_db_name}/{in_account_name}"):
                        logger.info(
                            f"Accessing secret: {secret['Name']}")

                        try:
                            get_secret_value_response = client.get_secret_value(
                                SecretId=secret["Name"]
                            )

                            if get_secret_value_response:
                                raise StopIteration

                        except ClientError as e:
                            print(e)
                            if e.response["Error"]["Code"] == "ExpiredTokenException":
                                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                                # Deal with the exception here, and/or rethrow at your discretion.
                                print("die")
                                raise (e)
                            elif e.response["Error"]["Code"] == "InternalServiceErrorException":
                                # An error occurred on the server side.
                                # Deal with the exception here, and/or rethrow at your discretion.
                                exit(1)
                            elif e.response["Error"]["Code"] == "InvalidParameterException":
                                # You provided an invalid value for a parameter.
                                # Deal with the exception here, and/or rethrow at your discretion.
                                exit(1)
                            elif e.response["Error"]["Code"] == "InvalidRequestException":
                                # You provided a parameter value that is not valid for the current state of the resource.
                                # Deal with the exception here, and/or rethrow at your discretion.
                                exit(1)
                            elif e.response["Error"]["Code"] == "ResourceNotFoundException":
                                # We can't find the resource that you asked for.
                                # Deal with the exception here, and/or rethrow at your discretion.
                                exit(1)
        except StopIteration:
            pass

        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.

        if "SecretString" in get_secret_value_response:
            secret_value = get_secret_value_response["SecretString"]

        else:
            secret_value = base64.b64decode(
                get_secret_value_response["SecretBinary"]
            )

        if secret_value:
            return secret_value
        else:
            logging.critical(f"No password retrieved from Secrets Manager for db: {in_db_name} account: {in_account_name} secret: {in_source_db_secret_name}\n"
                                )
            raise Exception(
                f"No password retrieved from Secrets Manager for db: {in_db_name} account: {in_account_name} secret: {in_source_db_secret_name}"
            )
