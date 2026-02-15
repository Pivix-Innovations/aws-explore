from datetime import datetime, timedelta
from .aws_manager import AWSManager

class CostExplorerScanner:
    def __init__(self):
        self.client = AWSManager.get_client('ce')

    def get_active_services(self, days=30):
        """
        Query Cost Explorer for services with checks > 0 in the last N days.
        Returns a list of dictionaries: [{'Service': 'Amazon EC2', 'Amount': 10.5, 'Unit': 'USD'}]
        """
        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=days)
        
        active_services = {}
        next_token = None
        try:
            while True:
                request_payload = {
                    'TimePeriod': {
                        'Start': start_date.isoformat(),
                        'End': end_date.isoformat()
                    },
                    'Granularity': 'MONTHLY',
                    'Metrics': ['UnblendedCost', 'UsageQuantity'],
                    'GroupBy': [
                        {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                        {'Type': 'DIMENSION', 'Key': 'REGION'}
                    ]
                }
                if next_token:
                    request_payload['NextPageToken'] = next_token

                response = self.client.get_cost_and_usage(**request_payload)

                for result in response.get('ResultsByTime', []):
                    for group in result.get('Groups', []):
                        # Group Keys are [Service, Region]
                        service_name = group['Keys'][0]
                        region = group['Keys'][1]

                        cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])
                        cost_unit = group['Metrics']['UnblendedCost']['Unit']
                        usage_amount = float(group['Metrics']['UsageQuantity']['Amount'])
                        usage_unit = group['Metrics']['UsageQuantity']['Unit']

                        if cost_amount > 0 or usage_amount > 0:
                            if service_name not in active_services:
                                active_services[service_name] = {
                                    'Service': service_name,
                                    'Amount': 0.0,
                                    'Unit': cost_unit,
                                    'Regions': set(),
                                    'UsageByUnit': {}
                                }

                            active_services[service_name]['Amount'] += cost_amount
                            # UsageQuantity can be mixed unit types, so keep per unit.
                            usage_map = active_services[service_name]['UsageByUnit']
                            usage_map[usage_unit] = usage_map.get(usage_unit, 0.0) + usage_amount

                            # Accumulate active regions for this service
                            if region != 'NoRegion':  # 'NoRegion' often appears for global costs
                                active_services[service_name]['Regions'].add(region)

                next_token = response.get('NextPageToken')
                if not next_token:
                    break
        except Exception as e:
            # Handle cases where CE is not enabled or permissions are missing
            print(f"Error fetching cost data: {e}")
            return []

        # Convert to list
        final_list = []
        for svc in active_services.values():
            svc['Regions'] = list(svc['Regions'])
            final_list.append(svc)
            
        return final_list
