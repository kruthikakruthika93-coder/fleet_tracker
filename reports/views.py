import csv

from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from accounts.decorators import role_required
from expenses.utils import apply_range, parse_range
from vehicles.models import Vehicle


def build_summary(start, end):
    rows = []
    totals = {'litres': 0, 'fuel': 0, 'repair': 0, 'service': 0, 'total': 0}
    for v in Vehicle.objects.order_by('registration_number'):
        fuel = apply_range(v.fuel_logs.all(), 'date', start, end)
        repairs = apply_range(v.repair_expenses.all(), 'date', start, end)
        services = apply_range(v.maintenance_records.filter(status='APPROVED'), 'service_date', start, end)

        fuel_agg = fuel.aggregate(cost=Sum('total_cost'), litres=Sum('litres'))
        fuel_cost = fuel_agg['cost'] or 0
        litres = fuel_agg['litres'] or 0
        repair_cost = repairs.aggregate(t=Sum('cost'))['t'] or 0
        service_cost = services.aggregate(t=Sum('cost'))['t'] or 0
        total = fuel_cost + repair_cost + service_cost

        rows.append({
            'vehicle': v, 'litres': litres, 'fuel': fuel_cost,
            'repair': repair_cost, 'service': service_cost, 'total': total,
        })
        totals['litres'] += litres
        totals['fuel'] += fuel_cost
        totals['repair'] += repair_cost
        totals['service'] += service_cost
        totals['total'] += total
    return rows, totals


@role_required('ADMIN')
def report_summary(request):
    start, end = parse_range(request)
    rows, totals = build_summary(start, end)
    context = {
        'rows': rows,
        'totals': totals,
        'start_str': start.isoformat() if start else '',
        'end_str': end.isoformat() if end else '',
        'qs': request.GET.urlencode(),
    }
    return render(request, 'reports/report_summary.html', context)


@role_required('ADMIN')
def report_csv(request):
    start, end = parse_range(request)
    rows, totals = build_summary(start, end)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="fleet_expense_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Vehicle', 'Make', 'Model', 'Fuel litres', 'Fuel cost', 'Repair cost', 'Service cost', 'Total cost'])
    for r in rows:
        v = r['vehicle']
        writer.writerow([v.registration_number, v.make, v.model, r['litres'], r['fuel'],
                         r['repair'], r['service'], r['total']])
    writer.writerow(['TOTAL', '', '', totals['litres'], totals['fuel'],
                     totals['repair'], totals['service'], totals['total']])
    return response