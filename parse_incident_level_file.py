# Intended to be run on the delimited file manually downloaded from:
# https://www.icpsr.umich.edu/web/NACJD/studies/38566#
# Or manually downloaded from:
# https://www.icpsr.umich.edu/web/ICPSR/studies/38566
# As follows:
# (Windows):
# python -m parse_incident_level_file "ICPSR_38566\DS0003\38566-0003-Data.tsv"
# (POSIX):
# python -m parse_incident_level_file "ICPSR_38566/DS0003/38566-0003-Data.tsv"

import sys, os
from functools import lru_cache
from urllib.request import urlretrieve

import pandas as pd
import numpy as np

def download_file(url, fp):
    if os.path.exists(fp): return
    directory = os.path.dirname(fp)
    os.makedirs(directory, exist_ok=True)
    print(f'downloading {url}')
    urlretrieve(url, fp)
    print(f'saving to {fp}')

@lru_cache()
def state_ansi_codes():
    # see https://www.census.gov/library/reference/code-lists/ansi/ansi-codes-for-states.html
    url = r"https://www2.census.gov/geo/docs/reference/state.txt"
    fp = os.path.join('_data', 'census', 'ansi')
    download_file(url, fp)
    df = pd.read_csv(fp, sep='|')
    return df.set_index('STUSAB')

@lru_cache()
def county_race_populations():
    url = r"https://www2.census.gov/programs-surveys/popest/datasets/2020-2021/counties/asrh/cc-est2021-all.csv"
    fp = os.path.join('_data', 'census', '2021', 'cc-est2021-all.csv')
    download_file(url, fp)

    dtype = {"STATE": str, "COUNTY": str}
    df = pd.read_csv(fp, encoding = "ISO-8859-1", dtype=dtype)
    df = df[(df['AGEGRP'] == 0) & (df['YEAR'] == 2)]
    df = df.drop(axis=1, labels=[
        'AGEGRP', 'YEAR', 'SUMLEV'])
    df = df.set_index(['STATE','COUNTY'])
    return df

def state_white_black_ratio(state_name):
    df = state_race_populations()
    white = df.loc[(state_name, 1), 'POPESTIMATE2020']
    black = df.loc[(state_name, 2), 'POPESTIMATE2020']
    return white / black

def county_white_pop(FIPS):
    try: row = county_race_populations().loc[FIPS]
    except KeyError: return np.nan
    return int(row['WA_MALE'] + row['WA_FEMALE'])

def county_black_pop(FIPS):
    try: row = county_race_populations().loc[FIPS]
    except KeyError: return np.nan
    return int(row['BA_MALE'] + row['BA_FEMALE'])

def interracial_violence():
    fp = sys.argv[1]
    with open(fp) as f:
        header = f.readline().split('\t')
        print(header)
        violent_offences = {
            '91', # Murder/Nonnegligent manslaughter
            #92, # Negligent Manslaughter
            '120', # Robbery
            '131', # Aggravated Assault
            '132', # Simple Assault
        }
        race_of_victim_codes = ['V40201', 'V40202', 'V40203']
        race_of_offender_codes = ['V50091', 'V50092', 'V50093']
        white = '1'
        black = '2'
        columns=['STATE', 'COUNTY', 'white on black', 'black on white']
        violence = pd.DataFrame(columns = columns)
        violence.set_index(['STATE', 'COUNTY'], inplace=True)

        for i, line in enumerate(f):
            data = dict(zip(header, line.split('\t')))
            if data['V20061'] not in violent_offences: continue

            victim_races = [data[code] for code in race_of_victim_codes]
            offender_races = [data[code] for code in race_of_offender_codes]
            white_on_black = (white in offender_races) and (black in victim_races)
            black_on_white = (black in offender_races) and (white in victim_races)
            if not (white_on_black or black_on_white): continue

            state = data['BH008']
            if state == 'NB': state = 'NE'
            #if state == 'DC': state = 'MD'

            FIPS_state = state_ansi_codes().loc[state, 'STATE']
            FIPS_state = str(FIPS_state).zfill(2)
            FIPS_county = data['BH054']
            FIPS_county = str(FIPS_county).zfill(3)
            if state == 'DC': FIPS_county = '001'
            FIPS = (FIPS_state, FIPS_county)
            if FIPS not in violence.index:
                violence.loc[FIPS,:] = 0
            
            violence.loc[FIPS,'white on black'] += white_on_black
            violence.loc[FIPS,'black on white'] += black_on_white
    return violence

def series_safe_divide(A, B):
    B = B.apply(lambda x: np.nan if x==0 else x)
    return A / B

def main():
    ivdf = interracial_violence()
    ivdf['white pop'] = [county_white_pop(FIPS) for FIPS in ivdf.index]
    ivdf['black pop'] = [county_black_pop(FIPS) for FIPS in ivdf.index]
    ivdf.loc['USA'] = ivdf.sum()
    ivdf['incidents ratio'] = series_safe_divide(
        ivdf['black on white'], ivdf['white on black'] )
    ivdf['pop ratio'] = series_safe_divide(
        ivdf['white pop'], ivdf['black pop'] )
    ivdf = ivdf[(ivdf['incidents ratio']>0) & (ivdf['pop ratio']>0)]

    USA = ivdf.loc['USA']
    ivdf = ivdf.drop('USA')

    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    plt.suptitle('County-Level Crime and Population Ratios')
    plt.title('2020 NIBRS Incident-Level File')
    plt.xscale('log')
    plt.yscale('log')
    ax.scatter(ivdf['pop ratio'], ivdf['incidents ratio'] )
    ax.scatter([USA['pop ratio']], [USA['incidents ratio']], c='orange')
    ax.annotate('USA', (USA['pop ratio'], USA['incidents ratio']))

    from math import log10
    a, b = np.polyfit(ivdf['pop ratio'].apply(log10), ivdf['incidents ratio'].apply(log10), 1)
    x = np.array(ivdf['pop ratio'])
    plt.plot(x, (x**a*10**b), c='orange')
    plt.annotate(f"$\log_{{10}}(y) = {a:.3f} \log_{{10}}(x) + {b:.3f}$", (1.5, 2))
    print(USA['incidents ratio'])

    ax.set_ylabel('ratio of black-on-white violent incidents\nto white-on-black violent incidents')
    ax.set_xlabel('ratio of white population to black population')

    plt.axvline(1)
    plt.axhline(1)
    plt.show()

if __name__ == '__main__':
    main()
