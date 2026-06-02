import json
import os
import hashlib
from datetime import datetime, timedelta, timezone
import boto3
import qrcode
from io import BytesIO

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'zosia-qr')
TABLE_NAME = os.environ.get('TABLE_NAME', 'qr_metadata')
MAX_URL_LENGTH = 2048

def lambda_handler(event, context):
    body = event.get('body', event)

    # Validate input
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError:
            return {"statusCode": 400, "body": json.dumps("Invalid JSON")}
            
    url = body.get('url', '').strip()
    
    if not url:
        return {"statusCode": 400, "body": json.dumps("URL cannot be empty.")}
        
    if len(url) > MAX_URL_LENGTH:
        return {"statusCode": 400, "body": json.dumps(f"URL is too long (max {MAX_URL_LENGTH} characters).")}
        
    if not (url.startswith('http://') or url.startswith('https://')):
        return {"statusCode": 400, "body": json.dumps("URL must start with http:// or https://.")}

    try:
        # hash the URL
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        file_extension = "png"
        filename = f"{url_hash}.{file_extension}"
        
        # Set expiration date to 1 year from now
        now = datetime.now(timezone.utc)
        expiration_date = now + timedelta(days=365)
        
        created_at_ts = int(now.timestamp())
        expires_at_ts = int(expiration_date.timestamp())
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        
        # Create an image from the QR code
        img = qr.make_image(fill_color="black", back_color="pink")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        file_size = len(buffer.getvalue())
        
        # Upload image to S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=buffer,
            ContentType=f"image/{file_extension}"
        )
        
        region = s3_client.meta.region_name
        public_url = f"https://{BUCKET_NAME}.s3.{region}.amazonaws.com/{filename}"
        
        # Upload metadata to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(
            Item={
                'url_hash': url_hash,
                'url': url,
                'filename': filename,
                'file_extension': file_extension,
                'file_size_bytes': file_size,
                'created_at': created_at_ts,
                'expires_at': expires_at_ts,
                's3_url': public_url
            }
        )
        
        # Return the public URL of the QR code image
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "QR code generated successfully. Yay! =^.^=",
                "qr_public_url": public_url
            }, ensure_ascii=False)
        }
        
    # Catch any unexpected errors and return a 500 response
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"An internal server error occurred: {str(e)}")
        }