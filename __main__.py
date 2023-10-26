"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3
from pulumi_gcp import storage

### GCP
# Create a Google Cloud resource (Storage Bucket)
bucket = storage.Bucket("my-bucket", location="US")
#####################################################

### AWS
# Export the DNS name of the bucket
pulumi.export("bucket_name", bucket.url)

# Create an AWS resource (S3 Bucket)
bucket = s3.Bucket('my-bucket')

# Export the name of the bucket
pulumi.export('bucket_name', bucket.id)
