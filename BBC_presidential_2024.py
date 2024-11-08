import os, io
from time import sleep

# to install package dependencies:
# pip install pandas matplotlib
import pandas as pd
import matplotlib.pyplot as plt

# to install package dependencies:
# pip install selenium undetected_chromedriver diskcache
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
import diskcache as dc

_1_day = 60*60*24
here = os.path.dirname( os.path.realpath(__file__) )
cache_dir = os.path.join(here, 'cache_dir')
cache = dc.Cache(cache_dir)
@cache.memoize(expire = _1_day)
def get_rendered_DOM(url):
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')  # Run headless if you don't need to see the browser
    options.add_argument('--save-page-as-mhtml')
    driver = uc.Chrome(options=options)

    driver.get(url)
    driver.implicitly_wait(10)
    sleep(10)
    mhtml = driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})
    return mhtml['data']

# steps to get the url that I assign to `url_2024` below:
# step 1: Go to https://www.bbc.com/news/election/2024/us/results
# step 2: Click on "Get the results in table format"
url_2024 = "https://www.bbc.com/news/articles/cvglg3klrpzo"
rendered_DOM_2024 = get_rendered_DOM(url_2024)
df_2024 = pd.read_html(io.StringIO(rendered_DOM_2024))
df_2024_presidential = df_2024[0]
df_2024_presidential["Expected ratio"] = df_2024_presidential["Expected votes counted (%)"].str.replace('%','').astype(float) / 100

candidates_2024 = dict()
for candidate in ['Donald Trump', 'Kamala Harris']:
    candidate_subset_2024 = df_2024_presidential[df_2024_presidential['Candidate'].str.contains(candidate)].set_index("State")
    candidate_votes_2024 = candidate_subset_2024['Votes'] / candidate_subset_2024['Expected ratio']
    candidates_2024[candidate] = candidate_votes_2024

All_Votes_2024 = pd.DataFrame(candidates_2024)
All_Votes = {
    # remaining years from wikipedia:
    "2008": {"Democrat": 69498516, "Republican": 59948323},
    "2012": {"Democrat": 65915795, "Republican": 60933504},
    "2016": {"Democrat": 65853514, "Republican": 62984828},
    "2020": {"Democrat": 81283501, "Republican": 74223975},
    "2024": {"Democrat": All_Votes_2024['Kamala Harris'].sum(), "Republican": All_Votes_2024['Donald Trump'].sum()},
}
All_Votes_df = pd.DataFrame.from_dict(All_Votes, orient='index')
All_Votes_df.index.name = 'Year'
print(All_Votes_df)
All_Votes_df.plot.bar(color = {"Democrat": "royalblue", "Republican": "indianred"})
plt.axhline(y=65853514, color='orange', linestyle='dashed', linewidth=1.5)


plt.xlabel("Year")
plt.ylabel("Votes")
plt.title("USA Presidential Votes by Party by Election Year")
plt.xticks(rotation=0)  # Rotate x-axis labels for better readability
plt.legend()
plt.tight_layout()

plt.subplots_adjust(bottom=0.25)
plt.figtext(0.95, .05, "Plot by @Anglo3000 (copying @jonatanpallesen)\nData: 2008-2020 wikipedia, 2024 BBC", ha="right", fontsize=10, color="gray")
plt.show()
