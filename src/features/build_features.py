import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import nltk
from nltk.corpus import stopwords
import pytz
from datetime import datetime
from dateutil import parser

################################################
## data exploration
df = pd.read_csv('/Users/linwang/Documents/YoutubeData/data/processed/mydata.csv')
category_order = ['Early Morning', 'Working Hours', 'After Work Hours', 'After Midnight']
df['TimeOfDay'] = df['TimeOfDay'].astype('category').cat.set_categories(category_order)

