"""An AWS and GCP Python Pulumi program"""

import pulumi, json
from pulumi_aws import iam
from pulumi_gcp import serviceaccount, compute

### GCP

# Create GCP Service Account and get Unique ID
aws_service_access_sa = serviceaccount.Account("awsAccessServiceAccount",
    account_id="aws-service-access",
    display_name="AWS Service Access Service Account")

# Store the GCP IAM Service Account UniqueId for creating the AWS IAM Role later
unique_id = aws_service_access_sa.id

# Create GCP compute resource with service account from #1 assigned
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
# Create a function to use with the Pulumi Output apply() method call
# This creates the policy used in the AWS trust relationship configuration for the IAM role
def gcp_sa_assume_role_trust(unique_id):
    return json.dumps({
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
					"accounts.google.com:aud": unique_id
				}
			}
		}
	]
    })

# Create IAM role and establish trust policy with Unique ID from Step 1
aws_s3_read_only_role = iam.Role("awsS3ReadRole",
    assume_role_policy=unique_id.apply(gcp_sa_assume_role_trust)
)
#####################################################
