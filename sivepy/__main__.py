import click
from .sivepy import SIVEP, date_intervals, cities

@click.command()
@click.option('--state', required=True, help='State initials.')
@click.option('--city', default=None, help='City name.')
@click.option('--start', required=True, help='Lower bound for date. Format: dd/mm/yyyy')
@click.option('--end', required=True, help='Upper bound for date. Format: dd/mm/yyyy')
@click.option('--output', default='out', help='Name for the output file.')
@click.option('--username', prompt=True, help='SIVEP username')
@click.option('--password', prompt=True, hide_input=True, help='SIVEP password')
def sivep(username, password, state, city, start, end, output):
    client = SIVEP(username, password)
    if not city:
        municps = cities(state)
    else:
        municps = [{'nome':city}]
        
    header=True
    for municip in municps:
        click.echo('Fetching SIVEP data for %s,%s city from %s to %s ' % (municip['nome'],state,start,end))
        dates = date_intervals(init=start,\
                               end=end, delta=7)
        for date in dates:
            click.echo('Downloading batch between %s and %s' % (date[0], date[1]))
            df = client.notifications(state, municip['nome'], date[0], date[1])
            df['Municipio'] = municip['nome']
            df.to_csv(output+'.tsv', mode='a',
                      sep='\t', index=False, header=header,
                      na_rep='NA')
            header=False

if __name__ == "__main__":
    sivep()
