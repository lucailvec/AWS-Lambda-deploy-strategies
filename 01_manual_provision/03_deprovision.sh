python3 util.py --bucket-name $BUCKET_NAME --region $REGION --action deprovision && \
aws cloudformation delete-stack --stack-name $STACK_NAME && \
rm ./filled_template.yml