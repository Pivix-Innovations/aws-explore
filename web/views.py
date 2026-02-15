from django.shortcuts import render
from django.views import View
from scanner.billing import CostExplorerScanner
from scanner.base import ScannerFactory
# Ensure scanners are registered
import scanner.services.ec2 

class DashboardView(View):
    @staticmethod
    def _format_usage(usage_by_unit):
        if not usage_by_unit:
            return "No usage"
        parts = []
        for unit, amount in sorted(usage_by_unit.items(), key=lambda x: x[1], reverse=True):
            if amount <= 0:
                continue
            parts.append(f"{amount:.2f} {unit}")
        return ", ".join(parts) if parts else "No usage"

    def get(self, request):
        ce_scanner = CostExplorerScanner()
        active_services = ce_scanner.get_active_services()

        # Decorate billing results with scanner state and resource summaries.
        services_data = []
        for service in active_services:
            name = service.get('Service', 'Unknown Service')
            scanner = ScannerFactory.get_scanner(name)
            regions = sorted(service.get('Regions', []))
            amount = float(service.get('Amount', 0.0))

            service_info = {
                'name': name,
                'cost': round(amount, 2),
                'unit': service.get('Unit', 'USD'),
                'has_scanner': scanner is not None,
                'regions': regions,
                'usage_by_unit': service.get('UsageByUnit', {}),
                'usage_display': self._format_usage(service.get('UsageByUnit', {})),
                'resources': []
            }

            if scanner:
                try:
                    target_regions = service.get('Regions', [])
                    resources = scanner.list_resources(regions=target_regions)
                    service_info['resource_count'] = len(resources or [])
                    service_info['resources'] = resources or []
                except Exception as e:
                    service_info['error'] = str(e)

            service_info.setdefault('resource_count', 0)
            services_data.append(service_info)

        query = (request.GET.get('q') or '').strip().lower()
        status_filter = (request.GET.get('status') or 'all').strip().lower()
        sort_by = (request.GET.get('sort') or 'cost_desc').strip().lower()

        filtered_services = services_data

        if query:
            filtered_services = [
                svc for svc in filtered_services
                if query in svc['name'].lower()
                or any(query in region.lower() for region in svc['regions'])
            ]

        if status_filter == 'scanned':
            filtered_services = [svc for svc in filtered_services if svc['has_scanner']]
        elif status_filter == 'billing':
            filtered_services = [svc for svc in filtered_services if not svc['has_scanner']]
        else:
            status_filter = 'all'

        sort_map = {
            'cost_desc': (lambda x: x['cost'], True),
            'cost_asc': (lambda x: x['cost'], False),
            'name_asc': (lambda x: x['name'].lower(), False),
            'name_desc': (lambda x: x['name'].lower(), True),
            'resources_desc': (lambda x: x.get('resource_count', 0), True),
        }
        sort_key, reverse = sort_map.get(sort_by, sort_map['cost_desc'])
        if sort_by not in sort_map:
            sort_by = 'cost_desc'
        filtered_services.sort(key=sort_key, reverse=reverse)

        total_cost = round(sum(svc['cost'] for svc in filtered_services), 2)
        total_resources = sum(svc.get('resource_count', 0) for svc in filtered_services)
        services_with_usage = sum(1 for svc in filtered_services if any(v > 0 for v in svc.get('usage_by_unit', {}).values()))
        scanned_services = sum(1 for svc in filtered_services if svc['has_scanner'])
        billing_only_services = len(filtered_services) - scanned_services
        coverage_pct = round((scanned_services / len(filtered_services)) * 100, 1) if filtered_services else 0.0
        top_services = sorted(filtered_services, key=lambda x: x['cost'], reverse=True)[:5]
        highest_cost_service = top_services[0] if top_services else None

        region_service_count = {}
        for svc in filtered_services:
            for region in svc.get('regions') or []:
                region_service_count[region] = region_service_count.get(region, 0) + 1
        top_regions = sorted(region_service_count.items(), key=lambda x: x[1], reverse=True)[:5]

        context = {
            'services': filtered_services,
            'top_services': top_services,
            'top_regions': top_regions,
            'query': request.GET.get('q', ''),
            'status_filter': status_filter,
            'sort_by': sort_by,
            'kpis': {
                'total_cost': total_cost,
                'active_services': len(filtered_services),
                'services_with_usage': services_with_usage,
                'scanned_services': scanned_services,
                'billing_only_services': billing_only_services,
                'total_resources': total_resources,
                'coverage_pct': coverage_pct,
                'highest_cost_service': highest_cost_service,
            },
        }
        return render(request, 'web/dashboard.html', context)
