from django.utils.dateparse import parse_date


def parse_range(request):
    def read(name):
        try:
            return parse_date(request.GET.get(name, ''))
        except ValueError:
            return None
    return read('start'), read('end')


def apply_range(qs, field, start, end):
    if start:
        qs = qs.filter(**{f'{field}__gte': start})
    if end:
        qs = qs.filter(**{f'{field}__lte': end})
    return qs