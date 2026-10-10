"""CSV reads the exact same recorded projection as the table and plot."""
from io import StringIO
import csv


def spreadsheet_text(value):
    """Labels are data, not spreadsheet formulas. Numerical cells stay numerical."""
    return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value


def series_csv(resources,project_id,file_id):
    offset=0
    while True:
        page=resources.series(project_id,file_id,offset,1000)
        stream=StringIO(newline='')
        writer=csv.writer(stream)
        if offset==0:
            writer.writerow(['Evidence scope','Time ('+page['time_unit']+')']+
                [spreadsheet_text(s['compartment']+' / '+s['species']+' ('+s['unit']+')') for s in page['series']])
        scope='Synthetic demo; not experimental validation' if page['source_type']=='synthetic' else page['claim_scope'] or 'Recorded output; not experimental validation'
        for i,time in enumerate(page['time']):
            writer.writerow([spreadsheet_text(scope),time]+[page['values'][s['id']][i] for s in page['series']])
        yield stream.getvalue()
        if not page['has_more']: break
        offset+=len(page['time'])
