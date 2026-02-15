from typing import List, Dict, Any
from ..base import ServiceScanner, ScannerFactory
from ..aws_manager import AWSManager

@ScannerFactory.register("Amazon Elastic Compute Cloud - Compute")
class EC2Scanner(ServiceScanner):
    @property
    def service_name(self) -> str:
        return 'ec2'

    @property
    def billing_service_name(self) -> str:
        return "Amazon Elastic Compute Cloud - Compute"

    def list_resources(self, regions: List[str] = None) -> List[Dict[str, Any]]:
        resources = []
        
        # If no regions triggers, default to current session region?
        # Or scan provided regions.
        scan_regions = regions if regions else [AWSManager.get_session().region_name]
        
        for region in scan_regions:
            try:
                client = AWSManager.get_client('ec2', region_name=region)
                response = client.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
                for reservation in response['Reservations']:
                    for instance in reservation['Instances']:
                        name = ''
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                        
                        resources.append({
                            'id': instance['InstanceId'],
                            'name': name,
                            'type': instance['InstanceType'],
                            'region': region,
                            'status': instance['State']['Name'],
                            'url': f"https://{region}.console.aws.amazon.com/ec2/home?region={region}#InstanceDetails:instanceId={instance['InstanceId']}"
                        })
            except Exception as e:
                print(f"Error scanning EC2 in {region}: {e}")
            
        return resources
