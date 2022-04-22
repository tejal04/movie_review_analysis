import pandas as pd
import numpy as np

import re

from selenium import webdriver
from bs4 import BeautifulSoup
import time

import pickle
from time import sleep

MOVIE_ID = "tt0111161"
# Open IMDbPro Log in page
driver = webdriver.Chrome(executable_path='/Users/swatiagarwal/Desktop/Webdriver/chromedriver')
driver.get('https://www.imdb.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fwww.imdb.com%2Fap-signin-handler&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=imdb_us&openid.mode=checkid_setup&siteState=eyJvcGVuaWQuYXNzb2NfaGFuZGxlIjoiaW1kYl91cyIsInJlZGlyZWN0VG8iOiJodHRwczovL3d3dy5pbWRiLmNvbS8_cmVmXz1sb2dpbiJ9&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0&tag=imdbtag_reg-20')

# Grab password and login from file
login = open('<file_location_with_login_info', 'r').read()
login = login.split('\n')[0:2]


# Enter email and password on login page
driver.find_element_by_xpath('//*[@id="ap_email"]').send_keys(login[0]) # Enter your own login info
driver.find_element_by_xpath('//*[@id="ap_password"]').send_keys(login[1]) # Enter your own login info
driver.find_element_by_xpath('//*[@id="signInSubmit"]').click()
sleep(10)

# Go to reviews page
try:
    print("getting page now...")
    driver.get('https://www.imdb.com/title/'+MOVIE_ID+'/reviews?ref_=tt_ov_rt')
    sleep(20)
except Exception as e:
    print("could not get page", e)


# Get page into BeautifulSoup object
html = driver.page_source

# with open("page_source.html") as fp:
#     soup = BeautifulSoup(fp, 'html.parser')

soup = BeautifulSoup(html, features="html.parser")

# Calculate number of scrolls needed
header = soup.find_all('div', class_='header')
review_num = re.findall(r'<span>(.+)\sReviews', str(header))

print(review_num)
review_num = int(review_num[0].replace(',', ''))
loads = (review_num//25) + 6 # Each Load More adds 25 reviews
print("total page load = ", loads)


# Load new pages until all pages are present
for i in range(loads):
    print(i)
    try:
        driver.find_element_by_xpath('//*[@id="load-more-trigger"]').click()
        time.sleep(7)
    except:
        continue

# Get page into BeautifulSoup object
html = driver.page_source
soup = BeautifulSoup(html)
imdb_reviews_raw = soup.find_all('div', {'class' : re.compile("(text show-more__control|text show-more__control clickable)")})
imdb_review_list = list(imdb_reviews_raw)


# Put all reviews text into list of reviews
TAG_RE = re.compile(r'(<[^>]+>|\n)')
def remove_tags(text):
    return TAG_RE.sub("", text)

clean_imdb_reviews = []
for i in imdb_review_list:
    review = remove_tags(str(i))
    clean_imdb_reviews.append(review)

print(clean_imdb_reviews[:2])

# Get review containers soup object
imdb_review_containers_list = list(soup.find_all('div', class_="review-container"))

has_score = []
for review in imdb_review_containers_list:
    has_score.append('class="ipl-ratings-bar"' in str(review))

# print("has score find first negative", has_score.index(False))
# exit(0)

# Create list of actual scores on page
imdb_scores_raw = soup.find_all('div', class_="ipl-ratings-bar") # Find all reviews with any rating
imdb_scores_raw_list = list(imdb_scores_raw)


# Create list of scores that were left with reviews, since a number of reviews did not have scores
found_scores = re.findall(r"<span>(\d+)<\/span>", str(imdb_scores_raw_list))
print("found scores = ", len(found_scores), found_scores[:10])

# Create list of scores with actual scores as numbers and missing scores as NaN
true_scores = []
count = 0 # Keep track of indices of found_scores list

for i in has_score:
    if i == True:
        true_scores.append(found_scores[count])
        count += 1
    else:
        true_scores.append(np.nan)

print(count)

# Create series from each list
review_series = pd.Series(clean_imdb_reviews)
scores_series = pd.Series(true_scores)
TLJ_Reviews = pd.DataFrame({'Reviews': review_series, 'Scores': scores_series})

# Pickle results
write_data = TLJ_Reviews
pickle.dump(write_data, open('IMDb_TMR_Reviews.pkl', 'wb'))

# Save results to csv file
TLJ_Reviews.to_csv('IMDb_TSR_Reviews.csv')

