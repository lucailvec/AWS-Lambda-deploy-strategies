import argparse
import boto3
from botocore.config import Config
from tempfile import TemporaryDirectory
from pathlib import Path
from zipfile import ZipFile
from jinja2 import Environment, FileSystemLoader

parser = argparse.ArgumentParser()
parser.add_argument('--bucket-name', dest='bucket_name', required=True, help="the name dns compliant of the s3 bucket where store the functions")
parser.add_argument('--region', dest='region', required=True, help="the region where to deploy the bucket")
parser.add_argument('--action', dest='action', required=True, help="the action to be done")
args = parser.parse_args()


config = Config(region_name=args.region)
s3 = boto3.resource('s3', config=config)

def provision_code():
    bucket_created = False
    file_uploaded = False
    bucket = s3.Bucket(args.bucket_name)
    try:
        create_response = s3.create_bucket(
            Bucket=args.bucket_name,
            CreateBucketConfiguration={'LocationConstraint': args.region}
            )
        bucket_created = True
        with TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            temp_zip_file = temp_dir_path / 'function.zip'
            with ZipFile(file=str(temp_zip_file), mode="w") as zip_file:
                zip_file.write('lambda_function.py', 'lambda_function.py')
            response = bucket.upload_file(Filename=str(temp_zip_file), Key='function.zip')
            file_uploaded=True

        print("Deploy of s3 bucket and code completed!")

        environment = Environment(loader=FileSystemLoader("./"))
        template = environment.get_template("./template_base.yml")
        new_template_content = template.render(
            {
                'template_bucket_name': args.bucket_name,
                'template_file_zip': 'function.zip'
            }
        )
        with open('filled_template.yml',"w") as new_template_fp:
            new_template_fp.write(new_template_content)
    except Exception as ex:
        print(ex)
        if file_uploaded:
            deprovision()
            print("Files removed")
        if bucket_created:
            bucket.delete()
            print("Code bucket deleted")
        print("Rollback ended")

def deprovision():
    bucket = s3.Bucket(args.bucket_name)
    response = bucket.delete_objects(Delete={'Objects': [{'Key': 'function.zip'}]})
    bucket.delete()
    print(response)

if __name__=="__main__":
    if args.action == "provision-code":
        provision_code()
    elif args.action == "deprovision":
        deprovision()
    else:
        print("Action not recognized")
