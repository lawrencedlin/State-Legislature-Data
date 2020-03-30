#!/usr/bin/env python
# coding: utf-8

# In[158]:


import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import lxml
import re
from tqdm import tqdm


# In[2]:


legis_dfs = []
legis_no = [22,23,24,25,26]
for num in legis_no:
    url = 'http://www.akleg.gov/basis/Bill/Range/#?session=&bill1=&bill2='.replace('#', f'{num}')
    df = pd.read_html(url)
    legis_dfs.append(df[0])


# In[190]:


len(legis_dfs[2])


# In[182]:


def ScrapeData(linklist):
    
    data = []
    
    for link in tqdm(linklist):
        url = link
        r = requests.get(url)
        soup = BeautifulSoup(r.content, 'lxml')
        date_yes_no = [None,None,None,None,None] # Create list that can be appended to entries in dataframe
        
        x=0
        for tr in soup.find_all(class_ ='floorAction'): # Find all tags (will be tr) will class = 'floorAction'
        #   print('______####ROW####________')
            x+=1
            for entry in tr.contents: # Loop through children of tr tags, the td tags
        #       print('_____####CELL####_____')

                if x == 1:
                    date_yes_no[0] = tr.contents[1].string

                HouseVoteRegEx = re.compile('\(H\) PASSED Y(\d\d).*(N)?(\d){1,2}?') # Find most recent vote for Senate
                if HouseVoteRegEx.search(str(entry)) != None:
                    mo = HouseVoteRegEx.search(str(entry))
                    date_yes_no[1]= mo.group(1) # Add yes vote
                    date_yes_no[2]= mo.group(3) # Add no vote          

                SenateVoteRegEx = re.compile('\(S\) PASSED Y(\d\d).*(N)?(\d){1,2}?') # Find most recent Senate Vote
                if SenateVoteRegEx.search(str(entry)) != None:
                    mo1 = SenateVoteRegEx.search(str(entry))
                    date_yes_no[3]= mo1.group(1) # Add yes vote
                    date_yes_no[4]= mo1.group(3) # Add no vote   
                    
        data.append(date_yes_no)
    return data
    

    


# In[183]:


legis22data = ScrapeData(link_list[0])


# In[185]:


legis23data = ScrapeData(link_list[1])
legis24data = ScrapeData(link_list[2])
legis25data = ScrapeData(link_list[3])
legis26data = ScrapeData(link_list[4])


# In[192]:


DataList = [legis22data,legis23data,legis24data,legis25data,legis26data]


# In[211]:


type(DataList[0])


# In[194]:


for data in DataList:
    data.insert(0,['Introduction Date','H Yes Vote',' H No Vote','S Yes Vote','S No Vote'])


# In[213]:


DataList[0] = pd.DataFrame(legis22data)
DataList[1] = pd.DataFrame(legis23data)
DataList[2] = pd.DataFrame(legis24data)
DataList[3] = pd.DataFrame(legis25data)
DataList[4] = pd.DataFrame(legis26data)


# In[223]:


DataList[0] = pd.concat([legis_dfs[0],DataList[0]],axis=1)
DataList[1] = pd.concat([legis_dfs[1],DataList[1]],axis=1)
DataList[2] = pd.concat([legis_dfs[2],DataList[2]],axis=1)
DataList[3] = pd.concat([legis_dfs[3],DataList[3]],axis=1)
DataList[4] = pd.concat([legis_dfs[4],DataList[4]],axis=1)


# ## Work on this

# In[225]:


DataList[0].to_csv('Alaska_2001_2002.csv')
DataList[1].to_csv('Alaska_2003-2004.csv')
DataList[2].to_csv('Alaska_2005_2006.csv')
DataList[3].to_csv('Alaska_2007-2008.csv')
DataList[4].to_csv('Alaska_2009_2010.csv')


# In[175]:


link_list = []
for num in legis_no:
    links = []
    
    url = 'http://www.akleg.gov/basis/Bill/Range/#?session=&bill1=&bill2='.replace('#', f'{num}')
    r = requests.get(url)
    soup = BeautifulSoup(r.content,'lxml')
    
    for entry in soup.find_all('nobr'):
        links.append(''.join(['http://www.akleg.gov',entry.a['href']]))
        
    link_list.append(links)


# In[176]:


link_list[0]


# # Test Case

# In[148]:



url = 'http://www.akleg.gov/basis/Bill/Detail/24?Root=HB%20%2015'
r = requests.get(url)
soup = BeautifulSoup(r.content, 'lxml')
date_yes_no = [None,None,None,None,None]# Create list that can be appended to entries in dataframe
for tr in soup.find_all(class_ ='floorAction'): # Find all tags (will be tr) will class = 'floorAction'
#   print('______####ROW####________')
    for entry in tr.contents: # Loop through children of tr tags, the td tags
#       print('_____####CELL####_____')
        
        introdateRegEx = re.compile('PREFILE RELEASED') # Regex object to find intro date
        if introdateRegEx.search(str(entry)) != None:
            date_yes_no[0] = tr.contents[1].string
        
        HouseVoteRegEx = re.compile('\(H\) PASSED Y(\d\d).*(N)?(\d){1,2}?') # Find most recent vote for Senate
        if HouseVoteRegEx.search(str(entry)) != None:
            mo = HouseVoteRegEx.search(str(entry))
            date_yes_no[1]= mo.group(1) # Add yes vote
            date_yes_no[2]= mo.group(3) # Add no vote          
        
        SenateVoteRegEx = re.compile('\(S\) PASSED Y(\d\d).*(N)?(\d){1,2}?') # Find most recent Senate Vote
        if SenateVoteRegEx.search(str(entry)) != None:
            mo1 = SenateVoteRegEx.search(str(entry))
            date_yes_no[3]= mo1.group(1) # Add yes vote
            date_yes_no[4]= mo1.group(3) # Add no vote 
        
          

    


# In[149]:


date_yes_no


# In[174]:


r = requests.get('http://www.akleg.gov/basis/Bill/Detail/24?Root=HB%20%20%204')
r.raise_for_status()


# In[ ]:




