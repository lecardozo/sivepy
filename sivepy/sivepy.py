import re
import time
import requests
from unidecode import unidecode
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

class SIVEP():
    
    def __init__(self, username, password):
        self._UF_ID = {
            'AC':1, 'AL':2, 'AM':3,
            'AP':4, 'BA':5, 'CE':6,
            'DF':7, 'ES':8, 'GO':9,
            'MA':10,'MG':11,'MS':12,
            'MT':13,'PA':14,'PB':15,
            'PE':16,'PI':17,'PR':18,
            'RJ':19,'RN':20,'RO':21,
            'RR':22,'RS':23,'SC':24,
            'SE':25,'SP':26,'TO':27
            }
        self._LOGIN_URL = 'http://200.214.130.44/sivep_malaria/senha.asp'
        self._LOGIN_PAYLOAD = {'tx_loginname':username, 'tx_senha':password}
    
    def notifications(self, state, city, start, end, patient=''):
        url = self._search_url(**{'patient':patient, 
                                'state':state,
                                'city':city,
                                'start':start,
                                'end':end,})
        with requests.Session() as s:
            p = s.post(self._LOGIN_URL, data=self._LOGIN_PAYLOAD)
            resp = s.get(url)
            return self._process_notifications(resp.text)
    
    def _search_url(self, **kwargs):
        start = kwargs.get('start')
        end = kwargs.get('end')
        state = kwargs.get('state').upper()
        city = unidecode(kwargs.get('city')).lower()
        patient = kwargs.get('patient')
        
        if (datetime.strptime(start, '%d/%m/%Y') > \
            datetime.strptime(end, '%d/%m/%Y')):
            raise ValueError('start must be lower than end_date')

        state = self._UF_ID[state.upper()]
        city = self._sivep_city_id(state, city)
        url = 'http://200.214.130.44/sivep_malaria/relatorio/rel_lista_notificacoes.asp?'+\
              'cd_uf={state}'+\
              '&opcao_agravo=B54'+\
              '&cd_municipio={city}'+\
              '&tx_unifonte='+\
              '&tx_paciente={patient}'+\
              '&cd_unifonte='+\
              '&dt_inicial={start}'+\
              '&dt_final={end}'
 
        return url.format(state=state, city=city, patient=patient,
                          start=start, end=end)
    
    def _sivep_city_id(self, state, city):
        if isinstance(city, int):
            stype='IBGE'
        elif isinstance(city, str):
            stype='TX'

        city_id = city if stype == 'IBGE' else ''
        city_name = city if stype == 'TX' else ''

        url = "http://200.214.130.44/sivep_malaria/pesquisa_municipio.asp?"+\
              "tipo={stype}"+\
              "&cd_estado={state}"+\
              "&uf=cd_uf&cd=cd_municipio"+\
              "&tx=tx_municipio"+\
              "&ibge=cd_municipio_ibge"+\
              "&proxcampo=&span=span_municipio"+\
              "&tx_municipio={city_name}"+\
              "&cd_municipio="+\
              "&cd_ibge={city_id}"
        url = url.format(stype=stype, state=state, 
                   city_name=city_name, city_id=city_id)

        with requests.Session() as s:
            p = s.post(self._LOGIN_URL, data=self._LOGIN_PAYLOAD)
            resp = s.get(url)
            return self._process_city_id(resp.text, city_name)

    def _process_city_id(self, html, name):
        soup = BeautifulSoup(html, 'lxml')
        raw = soup.find_all('script')[1]
        raw = raw.get_text()
        cid = re.search("cd_municipio.value = \'(.*)\'", raw)
        if not cid:
            # disambiguation. E.g. "careiro" vs "careiro da varzea"
            cid = re.search("<option value=\'(.*)\'>{}</option>"\
                            .format(name.upper()), raw)
        return int(cid.group(1))

    def _process_notifications(self, html):
        soup = BeautifulSoup(html, 'lxml')
        breaks = soup.find_all('p', attrs={'class':'BREAK'})
        tables = [pbreak.fetchPreviousSiblings()[0] for pbreak in breaks]
        tables.append(soup.find_all('table')[-2])
        dfs = [pd.read_html(table.prettify(), header=0)[0] for table in tables]
        df = pd.concat(dfs)
        return df



def cities(state):
    states = requests.get('http://servicodados.ibge.gov.br/api/v1/localidades/estados').json()
    state = [i for i in states if i['sigla'] == state or i['nome'] == state][0]
    url = 'http://servicodados.ibge.gov.br/api/v1/localidades/estados/{UF}/municipios'\
            .format(UF=state['id'])
    return(requests.get(url).json())

def date_intervals(init, end, delta):
    init = datetime.strptime(init, '%d/%m/%Y')
    end = datetime.strptime(end, '%d/%m/%Y')
    delta = timedelta(days=delta)
    curr = init
    while curr < end:
        if (end - curr) >= delta :
            yield (datetime.strftime(curr, '%d/%m/%Y'), 
                   datetime.strftime(curr+delta, '%d/%m/%Y'))
        else:
            yield (datetime.strftime(curr, '%d/%m/%Y'), 
                   datetime.strftime(curr+(end-curr), '%d/%m/%Y'))
        curr += delta + timedelta(days=1)
