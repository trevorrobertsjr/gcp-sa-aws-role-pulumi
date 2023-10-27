"""Create an Amazon S3 bucket and allow a GCP Compute Instance to Access It"""

import pulumi, json
from pulumi_aws import iam, s3
from pulumi_gcp import serviceaccount, compute

### GCP

# Create GCP Service Account and get Unique ID
aws_service_access_sa = serviceaccount.Account("awsAccessServiceAccount",
    account_id="aws-service-access",
    display_name="AWS Service Access Service Account")

# Create GCP compute resource with the custom service assigned
aws_service_instance = compute.Instance("awsserviceaccess",
    machine_type="e2-micro",
    zone="us-east4-c",
    boot_disk=compute.InstanceBootDiskArgs(
        initialize_params=compute.InstanceBootDiskInitializeParamsArgs(
            image="debian-cloud/debian-11",
        ),
    ),
    network_interfaces=[compute.InstanceNetworkInterfaceArgs(
        network="default",
        access_configs=[compute.InstanceNetworkInterfaceAccessConfigArgs()],
    )],
    service_account=compute.InstanceServiceAccountArgs(
        email=aws_service_access_sa.email,
        scopes=["cloud-platform"],
    ))
#####################################################

### AWS
# Create the S3 bucket for the GCP compute resources to access
# NOTE: Do not use the force_destroy option in PRODUCTION
#       I only used this setting because this is a demo environment.
aws_bucket = s3.Bucket('gcp-sa-access-bucket', force_destroy=True)

# Create an IAM policy allowing read access to the bucket and its contents
aws_iam_policy_bucket_read = iam.Policy("gcp-sa-access-bucket-read", policy=aws_bucket.id.apply(lambda name:
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObject",
                    "s3:ListBucket",
                    "s3:HeadBucket"

                ],
                "Resource": [
                    f"arn:aws:s3:::{name}",
                    f"arn:aws:s3:::{name}/*"
                ]
            }
        ]
    }
))

# Create IAM role and establish trust policy with the
# GCP Service Account's Unique ID created earlier
# Include the IAM policy arn as well.
aws_s3_read_only_role = iam.Role("awsS3ReadRole",
    assume_role_policy=aws_service_access_sa.unique_id.apply(lambda id:
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": "accounts.google.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        "accounts.google.com:aud": id
                    }
                }
            }
        ]
    }),
    managed_policy_arns=[
        aws_iam_policy_bucket_read.arn,
    ]
)
#####################################################

### Exports
# Export the name of the GCP instance
pulumi.export('gcp_instance_name', aws_service_instance.id)