#!/usr/bin/env python
# coding: utf-8

# In[408]:


import bs4
from bs4 import BeautifulSoup 
import requests
import csv
import pandas as pd
import numpy as np
from time import sleep
from tqdm import tqdm
import re
from selenium import webdriver
import os


# In[6]:


url1 = "https://www.legis.iowa.gov/legislation/BillBook?ga=81" # only need to use these urls for all the functions
url2 = "https://www.legis.iowa.gov/legislation/BillBook?ga=82"

r = requests.get(url1)
print(r.content[:100])


# In[116]:


# Component function
def bill_url_id(url):
    r= requests.get(url) # Save the HMTL of the webpage
    soup = BeautifulSoup(r.content,'html.parser') # Parse the HTML
    rows = soup.find_all(class_ = 'billSelect') # Select all the HTML with the class billSelect
    
    # This should be a list of bill ids in the format <option value="SF 2411" >SF 2411</option>
    
    id_matcher = re.compile(r'[SH].{,4}\d{1,6}') 
    
    # Select the bill id using regular expressions, there will be two of each bill id in the list
    
    mo = id_matcher.findall(str(rows)) # return list of all matches found
    bill_id_list = []
    for i in range(0,len(mo),2):
        # bill_id_list.append("%20".join(mo[i].split())) # Add %20 to string because thats how it appears in url (OUTDATED)
        bill_id_list.append(mo[i].replace(' ',''))
        
    return bill_id_list
    


# In[117]:


bill_url_id(url1)[:10]


# In[11]:


# Finding the index of where to insert the bill id
b = "https://www.legis.iowa.gov/legislation/BillBook?ga=81&ba=SR%201"
for i,letter in enumerate(b):
    if letter == 'S':
        print(i)
        break


# # Making the dataframe

# In[27]:


GA_81_df = pd.read_excel(r'C:\Users\lawre\Documents\Gretler\BillList.xlsx')
GA_82_df = pd.read_excel(r'C:\Users\lawre\Documents\Gretler\BillList (1).xlsx')


# In[29]:


GA_81_df.drop('Companion', axis=1, inplace=True) # Drop these empty columns
GA_82_df.drop('Companion', axis=1, inplace=True)
GA_81_df.drop('Similar', axis=1, inplace=True)
GA_82_df.drop('Similar', axis=1, inplace=True)


# In[88]:


GA_81_df['State'] = 'IA' # Create state column
GA_82_df['State'] = 'IA'


# In[89]:


GA_81_sen_disp = pd.read_html(r'C:\Users\lawre\Documents\Gretler\81senatedisposition.txt')
GA_81_house_disp = pd.read_html(r'C:\Users\lawre\Documents\Gretler\81housedisposition.txt')
GA_82_sen_disp = pd.read_html(r'C:\Users\lawre\Documents\Gretler\82senatedisposition.txt')
GA_82_house_disp = pd.read_html(r'C:\Users\lawre\Documents\Gretler\82housedisposition.txt')


# In[90]:


GA_81_df.head()


# In[91]:


GA_81_disp = pd.concat([GA_81_sen_disp[1],GA_81_house_disp[1]])
GA_82_disp = pd.concat([GA_82_sen_disp[1],GA_81_house_disp[1]])
GA_81_disp.head()


# In[358]:


GA_81_final = pd.merge(GA_81_df,GA_81_disp, left_on='Bill', right_on='Bill Number')
GA_82_final = pd.merge(GA_82_df, GA_82_disp, left_on='Bill',right_on='Bill Number')


# In[359]:


GA_81_final['Session'] = '01/10/2005 - 01/07/2007' # Create session columns
GA_82_final['Session'] = '01/08/2007 - 01/11/2009'


# In[360]:


GA_81_final.drop('Bill Number',axis=1,inplace=True) # Drop redundant column
GA_82_final.drop('Bill Number',axis=1,inplace=True)


# In[361]:


GA_81_final.set_index('State', inplace=True)
GA_82_final.set_index('State',inplace=True)


# In[391]:


GA_81_final.head()


# In[392]:


GA_81_final['Bill'] = GA_81_final['Bill'].str.replace(' ','')
GA_82_final['Bill'] = GA_82_final['Bill'].str.replace(' ','')


# # Scrape the votes and date of introduction next time. FINISH BY THIS TUESDAY !!!!

# https://www.legis.iowa.gov/legislation/billTracking/billHistory?ga=81&billName=SF2399 Use the billHistory tracking tool and replace the bill ids

# In[120]:


def IA_billtracking(url):
    bill_url = list("https://www.legis.iowa.gov/legislation/billTracking/billHistory?ga=  &billName=")
    bill_url[67:69] = list(url[-2:]) # Insert GA# as indicated in url
    bill_id_list = bill_url_id(url) # Create an object with the list of bill ids based on the url inputted
    webpages = [] 
    for bill_id in bill_id_list:
        bill_url[79:]=bill_id # Insert bill id into bill_url 
        webpages.append("".join(bill_url)) # Add the bill url to a list and loop again
    return webpages


# In[286]:


len(IA_billtracking(url1))


# In[374]:


def introdate_and_votes(url,start=0,end=None): 
    date_and_vote_list = [] 
    
    # Get a list of the urls of specific bills i.e. https://www.legis.iowa.gov/legislation/billTracking/billHistory?ga=81&billName=SF2411
    bill_webpages = IA_billtracking(url)[start:end] 
    
   
    x=0 # Counter
    for webpage in bill_webpages:
        date_and_vote = []
        
        # Get the bill id so I can join it with the dataframe
        bill_id = webpage[79:] 
        date_and_vote.append(bill_id)
        
        if webpage[79] == 'S':
            flag = 'Passed Senate'
        elif webpage[79] == 'H':
            flag = 'Passed House'
            
        r = requests.get(webpage) # Retrieve webpage HTML
        try:
            r.raise_for_status() # See if webpage is valid
            soup = BeautifulSoup(r.content, 'html.parser') # Process the HTML
        
            # Get HTML of first table that relates directly to bill in question
            first_table = soup.find("table", class_="billActionTable divideVert sortable")
            first_table_tags = soup.find_all("td")

            date_and_vote.append(first_table_tags[0].text)# Add to list the text of the first tag, the intro date

            vote_tag_list = []
            for tag in first_table_tags: # Loop through tags of the first table
                vote_tag = re.compile(flag) # Create regex object that looks for 'Passed House' or 'Passed Senate'
                mo = vote_tag.search(tag.text) # Search for flag in tag text
                if (mo != None) == True:
                    vote_tag_list.append(tag) # If the search object returns something, add it to the vote tag list

            try:
                recent_vote = vote_tag_list[-1].text #Find the last vote tag, which should be the most recent vote

                ayes = re.compile(r'ayes.(\d{1,2})') # Create regex objects to find # of votes or None votes
                nays = re.compile(r'nays.(\d{1,2})')
                ayes_none = re.compile(r'ayes.(none)')
                nays_none = re.compile(r'nays.(none)')

                mo_ayes = ayes.search(recent_vote) # Search the text of the most recent vote for the regular expression
                mo_nays = nays.search(recent_vote)
                mo_ayes_none = ayes_none.search(recent_vote)
                mo_nays_none = nays_none.search(recent_vote)

                if mo_ayes != None: # Regex to search for votes in table data
                    date_and_vote.append(mo_ayes.group(1))
                    if mo_nays != None:
                        date_and_vote.append(mo_nays.group(1))
                    else:
                        date_and_vote.append(None)
                elif mo_ayes_none != None:
                    date_and_vote.append(mo_ayes_none.group(1))
                    if mo_nays != None:
                        date_and_vote.append(mo_nays.group(1))
                    else:
                        date_and_vote.append(None)
                        
            except:
                #print(webpage,'had no votes') # Double-check to see if algorithm is working for bills with no votes
                date_and_vote.append(None)
                date_and_vote.append(None)

            date_and_vote_list.append(date_and_vote) # Add one row of dates and votes to the list
            
        except:
            date_and_vote = [bill_id] + [None]*3 # If the webpage is invalid, add a None row
            date_and_vote_list.append(date_and_vote)
    
#         x+=1
#         if x == 14:
#             break
    return(date_and_vote_list)


# In[404]:


# Scrape intro date and vote data from GA 81
intervals = range(0,4040,50)
interval_num = []
for number in intervals:
    interval_num.append(number)
sub_df81 = []
for i in tqdm(range(len(interval_num))):
    try:
        curr_list = introdate_and_votes(url1,start = interval_num[i],end = interval_num[i+1])
        df = pd.DataFrame(curr_list, columns = ['Bill','Introduction date', 'Yes votes', 'No votes'])
        sub_df81.append(df)
        sleep(10)
    except IndexError:
        curr_list = introdate_and_votes(url1,start = interval_num[i],end = None)
        df = pd.DataFrame(curr_list, columns = ['Bill','Introduction date', 'Yes votes', 'No votes'])
        sub_df81.append(df)


# In[326]:


last_list = introdate_and_votes(url1,start=4000,end=None)  
last_list_df = pd.DataFrame(last_list, columns=['Bill','Introduction date', 'Yes votes', 'No votes'])


# In[377]:


# Scrape intro date and vote data from GA 82
intervals = range(0,4256,50)
interval_num = []
for number in intervals:
    interval_num.append(number)
sub_df82 = []
for i in tqdm(range(len(interval_num))):
    try:
        curr_list = introdate_and_votes(url1,start = interval_num[i],end = interval_num[i+1])
        df = pd.DataFrame(curr_list, columns = ['Bill','Introduction date', 'Yes votes', 'No votes'])
        sub_df82.append(df)
        sleep(10)
    except IndexError:
        curr_list = introdate_and_votes(url1,start = interval_num[i],end = None)
        df = pd.DataFrame(curr_list, columns = ['Bill','Introduction date', 'Yes votes', 'No votes'])
        sub_df82.append(df)


# In[375]:


len(IA_billtracking(url2))


# In[373]:


main_df.tail()


# In[ ]:


sub_df82 = pd.concat(sub_df82)


# In[394]:


GA_82 = pd.merge(GA_82_final,sub_df82,on='Bill')
GA_82


# In[406]:


GA_81 = pd.merge(GA_81_final,main_df, on='Bill')


# In[407]:


GA_81.tail()


# In[411]:


os.getcwd()


# # Export the dataframes to CSV

# In[420]:


GA_81.to_csv(r'C:\Users\lawre\Documents\Gretler\IA_2005_to_2007.csv')
GA_82.to_csv(r'C:\Users\lawre\Documents\Gretler\IA_2007_to_2009.csv')


# Selenium

# In[ ]:



x=0
for url in IA_billtracking(url1): # To verify if the introduction dates are correct
    browser = webdriver.Chrome(r'C:\Users\lawre\Desktop\Python Modules\chromedriver.exe')
    #browser.get(url)
    x+=1
    if x == 10:
        break
                        
    # elem = browser.find_element_by_id('vertical-align:top')
    # print(elem.text)


# # Code for scraping the raw text of the bills (not needed anymore)

# In[ ]:


How I extracted bill ids before regex
def bill_url_id(rows): # replace rows with get_rows(url) 
    bill_ids = str(rows).split("\"") # Split the HTML by quotation mark to isolate bill id
    bill_url_list = []
    for i in range(9,len(bill_ids),2): # Starting at index 9, every 2 indexs is a bill id
        bill_url_list.append("%20".join(bill_ids[i].split())) # Add all the bill ids to a list and 
        # add %20 so it can be added to the url to access the bill webpage
    return(bill_url_list) # returns urls that direct you to the webpage of a bill like SF 2236
        
    


# In[12]:


# Pass in url to this function
def IA_bill_webpages(url):
    bill_url = list("https://www.legis.iowa.gov/legislation/BillBook?ga=__&ba=")
    bill_url[51:53] = list(url)[-2:] # Insert into bill_url the general assembly number as indicated in url
    bill_id_list = bill_url_id(url) # Create an object with the list of bill ids based on the url inputted
    webpages = [] 
    for bill_id in bill_id_list:
        bill_url[57:]=bill_id # Insert bill id into bill_url 
        webpages.append("".join(bill_url)) # Add the bill url to a list and loop again
    return webpages


# Testing the url of the bill specific webpage

# In[217]:


d = IA_bill_webpages(url1)[:3]
d


# In[218]:


def text_src(url): # named this way because the src of the element with id=bbContextDoc leads you to the text of the bill
    
    # Get a list of the urls of specific bills i.e. https://www.legis.iowa.gov/legislation/BillBook?ga=81&ba=SF%202411
    bill_webpages = IA_bill_webpages(url) 
    bill_text_links = [] 
    x=0 # Counter
    for webpage in tqdm(bill_webpages): # tqdm gives progress bar for the loop
        r = requests.get(webpage) # Retrieve webpage HTML
        soup = BeautifulSoup(r.content, 'html.parser') # Process the HTML
        attachment = soup.find(id='bbContextDoc') # Find the part of the URL starting with BillBook?ga=__&ba=__%20___
        # Try except block in case URL s invalid
        try:
            attachment_url = 'https://www.legis.iowa.gov' + attachment['src'] # Add BillBook portion of URL to main path
            bill_text_links.append(attachment_url) # Add it to the bill_text_links list
        except TypeError:
            attachment_url = 'None' # Add empty placeholder in list if there is no attachment['src']
            bill_text_links.append(attachment_url) 
        except:
            attachment_url = 'Try this one manually' # If the error is something else, this happens
            bill_text_links.append(attachment_url)
        # Get a sample data set of 10 texts scraped
        x+=1
        sleep(1)
        if x == 3:
            break
    return bill_text_links


# In[223]:


# # Run this with laptop plugged in
# b = text_src("https://www.legis.iowa.gov/legislation/BillBook?ga=81")
# # b


# In[16]:


def text_scraper(bill_text_links): # Takes list of bill text links and scrapes the text 
    text_soup = []
    for url in bill_text_links:
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'html.parser')
        text_soup.append(soup.get_text())
    return text_soup


# In[221]:


c = text_scraper(b)
# for text in c[0]:
#     print(text)


# In[222]:


for text in c: 
    description_type1 = re.compile(r'A BILL(.*)BE IT ENACTED',re.DOTALL) 
    description_type2 = re.compile(r'AN ACT(.*)BE IT ENACTED', re.DOTALL)
    description_type3 = re.compile(r'A Joint(.*)BE IT ENACTED', re.DOTALL)
    description_type4 = re.compile(r'A concurrent(.*)Whereas', re.DOTALL)
    description_type5 = re.compile(r'A Resolution(.*)Whereas', re.DOTALL)
    # find descriptions beginning with BEGINNING PHRASE and ending with ENDING PHRASE and taking the text inbetween
    # there are five possible combinations so there are five re.compile objects
    mo1 = description_type1.search(str(text))
    mo2 = description_type2.search(str(text))
    mo3 = description_type3.search(str(text))
    mo4 = description_type4.search(str(text))
    mo5 = description_type5.search(str(text))
    # Returns either None or a description of where a match was found
    mo_list = [mo1,mo2,mo3,mo4,mo5]
    for mo in mo_list:
        if not mo == None: # Find the object where there was a match
#             print(mo.group()) # Print the string


# In[311]:





# In[ ]:




