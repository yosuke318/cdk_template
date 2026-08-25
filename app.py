from aws_cdk import App
from stacks.s3 import S3Stack

app = App()
S3Stack(app, "S3Stack")
app.synth()