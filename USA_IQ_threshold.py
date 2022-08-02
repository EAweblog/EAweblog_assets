import os
from urllib.request import urlretrieve
from zipfile import ZipFile
from statistics import NormalDist

import pandas as pd

dn = os.path.dirname( os.path.realpath(__file__) )
fn = 'NIQ-DATASET-V1.3.3.zip'
fp = os.path.join(dn, fn)
spreadsheet_fn = 'NIQ-DATA (V1.3.3).xlsx'

def download_niq_dataset():
    url = 'https://viewoniq.org/wp-content/uploads/2019/07/NIQ-DATASET-V1.3.3.zip'   
    if not os.path.exists(fp):
        print(f'downloading {url}')
        urlretrieve(url, fp)

def read_spreadsheet():
    with ZipFile(fp) as myzip:
        with myzip.open(spreadsheet_fn) as f:
            return pd.read_excel(f, sheet_name='NAT', skiprows=1)

def main():
    download_niq_dataset()
    df = read_spreadsheet()
    index_col = 'Country name'
    population_col = 'Total pop.'
    iq_col = 'QNW+SAS+GEO'
    df = df[df[index_col].notna() & df[iq_col].notna()]
    df = df.set_index(index_col)

    world_population = sum(df[population_col])
    usa = df.loc['United States']
    usa_population_fraction = usa[population_col] / world_population

    usa_data = []
    for IQ in range(30, 200+1):
        total_above_threshold = 0
        for i,row in df.iterrows():
            fraction = 1 - NormalDist(mu=row[iq_col], sigma=15).cdf(IQ)
            total_above_threshold += fraction*row[population_col]        
        fraction = 1 - NormalDist(mu=usa[iq_col], sigma=15).cdf(IQ)
        usa_above_threshold = fraction*usa[population_col]
        usa_fraction_above_threshold = usa_above_threshold/total_above_threshold
        usa_data.append( (IQ, usa_fraction_above_threshold) )
    IQs, fractions_above_threshold = zip(*usa_data)

    import matplotlib.pyplot as plt
    handles_labels = []
    handles_labels.append((
        plt.axhline(y=usa_population_fraction, linestyle='--'),
        'USA population as a fraction of global population.'
    ))
    handles_labels.append((
        plt.plot(IQs, fractions_above_threshold)[0],
        'USA population above IQ score as a fraction of global\n'
        +'population above IQ score.'
    ))
    handles_labels.append((
        plt.axvline(x=104, c='orange', linestyle='--'),
        'IQ-104 threshold'
    ))
    handles_labels.append((
        plt.axvline(x=119, c='orange'),
        'IQ-119 threshold'
    ))
    handles, labels = zip(*handles_labels)
    plt.xlabel('IQ')
    plt.legend(handles, labels, bbox_to_anchor=(0, -0.15), loc='upper left')
    plt.savefig(os.path.join(dn, 'USA_IQ_threshold_graph.png'), bbox_inches='tight')

if __name__ == '__main__': main()
    
