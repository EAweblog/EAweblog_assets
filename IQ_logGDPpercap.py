import os

from urllib.request import urlretrieve
from zipfile import ZipFile

import pandas as pd
import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

here = os.path.dirname( os.path.realpath(__file__) )
data_dir = os.path.join(here, '_data')

dn = os.path.join(data_dir, 'ViewOnIQ')
url = 'https://viewoniq.org/wp-content/uploads/2023/10/NIQ-DATASET-V1.3.5.zip'
fn = url.split('/')[-1]
fp = os.path.join(dn, fn)
def download_niq_dataset():
    if not os.path.exists(fp):
        print(f'downloading {url}')
        os.makedirs(dn, exist_ok=True)
        urlretrieve(url, fp)
def read_spreadsheet(sheet_name='NAT'):
    download_niq_dataset()
    with ZipFile(fp) as myzip:
        biggest_file = max([x for x in myzip.infolist() if x is not None], key = lambda x: x.compress_size)
        with myzip.open(biggest_file) as f:
            return pd.read_excel(f, sheet_name=sheet_name, skiprows=1)
iq_df = read_spreadsheet()

dn = os.path.join(data_dir, 'WorldBank')
fn = 'API_NY.GDP.PCAP.CD.zip'
fp = os.path.join(dn, fn)
spreadsheet_fn = f'huh.xlsx'
def download_gdp_pcap_dataset():
    url = 'https://api.worldbank.org/v2/en/indicator/NY.GDP.PCAP.CD?downloadformat=csv'   
    if not os.path.exists(fp):
        print(f'downloading {url}')
        os.makedirs(dn, exist_ok=True)
        urlretrieve(url, fp)
def read_spreadsheet():
    download_gdp_pcap_dataset()
    with ZipFile(fp) as myzip:
        biggest_file = max([x for x in myzip.infolist() if x is not None], key = lambda x: x.compress_size)
        with myzip.open(biggest_file.filename) as f:
            return pd.read_csv(f, skiprows=4)
pcap_df = read_spreadsheet()

iq_df = iq_df[pd.notna(iq_df['Country name'])]
iq_df.rename(columns={'ISO 3166-1 ALPHA-3': 'ISO_A3'}, inplace=True)
iq_df.ISO_A3 = iq_df.ISO_A3.apply(lambda x: x.strip()) # France (and others?) Have a trailing ' ' which messes up the data
iq_df = iq_df.set_index('ISO_A3')
# IQ_variable = 'R'
IQ_variable = 'QNW+SAS+GEO'
# IQ_variable = 'QNW+SAS'
# IQ_variable = 'L&V12+GEO'
iq_df = iq_df[[IQ_variable]]

current_year = '2022'
pcap_variable = 'current_pcap'
pcap_df = pcap_df.fillna(method='ffill', axis=1)
pcap_df = pcap_df.set_index('Country Code')
pcap_df = pcap_df[[current_year]]
pcap_df = pcap_df.rename(columns={current_year: pcap_variable})

df = iq_df.merge(pcap_df, left_index=True, right_index=True, how='left')
df = df[pd.to_numeric(df[pcap_variable], errors='coerce').notnull()]
df[pcap_variable] = df[pcap_variable].values.astype(float)
df = df.dropna(subset=IQ_variable)
print(df)

slope, intercept, r_value, p_value, std_err =\
    scipy.stats.linregress(df[IQ_variable], np.log10(df[pcap_variable]))
    
def plot_gdpc_IQ():
    fig, ax = plt.subplots()
    x = np.linspace(55,110,200)
    y = 10**(slope*x+intercept)
    plt.plot(x, y, c='orange')
    
    plt.annotate(f"$\log_{{10}}(y) = {slope:.3f}x + {intercept:.3f}$\n$r^2 = {r_value**2:.3f}$", (85, 450))
    plt.suptitle(f'GDP per capita vs. average IQ of {len(df)} countries')
    plt.title('GDP/C from worldbank.org; average IQ from viewoniq.org')
    
    plt.yscale('log')
    ax.scatter(IQ_variable, pcap_variable, data=df)
    ax.set_ylabel(f'GDP per capita, {current_year}')
    ax.set_xlabel(f'average IQ: {IQ_variable} variable from NIQ DATASET V1.3.5\nchart by @Anglo3000')

    # for code, row in df.iterrows():
    #     ax.annotate(code, (row[IQ_variable], row[pcap_variable]))

    plt.tight_layout()
    plt.show()
plot_gdpc_IQ()