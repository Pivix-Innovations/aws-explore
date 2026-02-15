import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

class AWSManager:
    _session = None

    @classmethod
    def get_session(cls):
        if cls._session is None:
            # Check for static credentials in env first
            if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
                # AWS_PROFILE triggers ProfileNotFound if set but not present in ~/.aws/config,
                # even if we pass explicit credentials. Unset it to be safe.
                if 'AWS_PROFILE' in os.environ:
                    del os.environ['AWS_PROFILE']

                cls._session = boto3.Session(
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    aws_session_token=os.getenv('AWS_SESSION_TOKEN') or None,
                    region_name=os.getenv('AWS_REGION', 'us-east-1')
                )
            else:
                # Fallback to default chain (profile, instance role, etc.)
                try:
                    cls._session = boto3.Session()
                except Exception:
                    # If default session fails (e.g. ProfileNotFound), try without profile
                    # explicitly if it was set in env but invalid
                    if 'AWS_PROFILE' in os.environ:
                        del os.environ['AWS_PROFILE']
                        cls._session = boto3.Session()
            
            # Verify credentials
            try:
                sts = cls._session.client('sts')
                sts.get_caller_identity()
            except (NoCredentialsError, PartialCredentialsError, Exception) as e:
                cls._session = None
                print(f"AWS Auth Error: {e}")
                raise ValueError(f"Valid AWS credentials not found. Error: {e}")
        return cls._session

    @classmethod
    def get_client(cls, service_name, region_name=None):
        session = cls.get_session()
        return session.client(service_name, region_name=region_name)

    @classmethod
    def get_resource(cls, service_name, region_name=None):
        session = cls.get_session()
        return session.resource(service_name, region_name=region_name)
