
# coding: utf-8

# # Read in the data

# In[2]:


import pandas
import numpy
import re
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
data_files = [
    "ap_2010.csv",
    "class_size.csv",
    "demographics.csv",
    "graduation.csv",
    "hs_directory.csv",
    "sat_results.csv"
]

data = {}

for f in data_files:
    d = pandas.read_csv("schools/{0}".format(f))
    data[f.replace(".csv", "")] = d


# # Read in the surveys

# In[3]:


all_survey = pandas.read_csv("schools/survey_all.txt", delimiter="\t", encoding='windows-1252')
d75_survey = pandas.read_csv("schools/survey_d75.txt", delimiter="\t", encoding='windows-1252')
survey = pandas.concat([all_survey, d75_survey], axis=0)

survey["DBN"] = survey["dbn"]

survey_fields = [
    "DBN", 
    "rr_s", 
    "rr_t", 
    "rr_p", 
    "N_s", 
    "N_t", 
    "N_p", 
    "saf_p_11", 
    "com_p_11", 
    "eng_p_11", 
    "aca_p_11", 
    "saf_t_11", 
    "com_t_11", 
    "eng_t_10", 
    "aca_t_11", 
    "saf_s_11", 
    "com_s_11", 
    "eng_s_11", 
    "aca_s_11", 
    "saf_tot_11", 
    "com_tot_11", 
    "eng_tot_11", 
    "aca_tot_11",
]
survey = survey.loc[:,survey_fields]
data["survey"] = survey


# # Add DBN columns

# In[4]:


data["hs_directory"]["DBN"] = data["hs_directory"]["dbn"]

def pad_csd(num):
    string_representation = str(num)
    if len(string_representation) > 1:
        return string_representation
    else:
        return "0" + string_representation
    
data["class_size"]["padded_csd"] = data["class_size"]["CSD"].apply(pad_csd)
data["class_size"]["DBN"] = data["class_size"]["padded_csd"] + data["class_size"]["SCHOOL CODE"]


# # Convert columns to numeric

# In[5]:


cols = ['SAT Math Avg. Score', 'SAT Critical Reading Avg. Score', 'SAT Writing Avg. Score']
for c in cols:
    data["sat_results"][c] = pandas.to_numeric(data["sat_results"][c], errors="coerce")

data['sat_results']['sat_score'] = data['sat_results'][cols[0]] + data['sat_results'][cols[1]] + data['sat_results'][cols[2]]

def find_lat(loc):
    coords = re.findall("\(.+, .+\)", loc)
    lat = coords[0].split(",")[0].replace("(", "")
    return lat

def find_lon(loc):
    coords = re.findall("\(.+, .+\)", loc)
    lon = coords[0].split(",")[1].replace(")", "").strip()
    return lon

data["hs_directory"]["lat"] = data["hs_directory"]["Location 1"].apply(find_lat)
data["hs_directory"]["lon"] = data["hs_directory"]["Location 1"].apply(find_lon)

data["hs_directory"]["lat"] = pandas.to_numeric(data["hs_directory"]["lat"], errors="coerce")
data["hs_directory"]["lon"] = pandas.to_numeric(data["hs_directory"]["lon"], errors="coerce")


# # Condense datasets

# In[6]:


class_size = data["class_size"]
class_size = class_size[class_size["GRADE "] == "09-12"]
class_size = class_size[class_size["PROGRAM TYPE"] == "GEN ED"]

class_size = class_size.groupby("DBN").agg(numpy.mean)
class_size.reset_index(inplace=True)
data["class_size"] = class_size

data["demographics"] = data["demographics"][data["demographics"]["schoolyear"] == 20112012]

data["graduation"] = data["graduation"][data["graduation"]["Cohort"] == "2006"]
data["graduation"] = data["graduation"][data["graduation"]["Demographic"] == "Total Cohort"]


# # Convert AP scores to numeric

# In[7]:


cols = ['AP Test Takers ', 'Total Exams Taken', 'Number of Exams with scores 3 4 or 5']

for col in cols:
    data["ap_2010"][col] = pandas.to_numeric(data["ap_2010"][col], errors="coerce")


# # Combine the datasets

# In[8]:


combined = data["sat_results"]

combined = combined.merge(data["ap_2010"], on="DBN", how="left")
combined = combined.merge(data["graduation"], on="DBN", how="left")

to_merge = ["class_size", "demographics", "survey", "hs_directory"]

for m in to_merge:
    combined = combined.merge(data[m], on="DBN", how="inner")

combined = combined.fillna(combined.mean())
combined = combined.fillna(0)


# # Add a school district column for mapping

# In[9]:


def get_first_two_chars(dbn):
    return dbn[0:2]

combined["school_dist"] = combined["DBN"].apply(get_first_two_chars)


# # Find correlations

# In[10]:


correlations = combined.corr()
correlations = correlations["sat_score"]
print(correlations)


# In[11]:


get_ipython().magic('matplotlib inline')
survey_corr = combined.corr()['sat_score'][survey_fields].plot.bar()
plt.show()


# rr_s being the student respnse rate has the strongest positive correlation with the SAT results. That shows that students' voice is the most important

# In[12]:


fig,ax = plt.subplots()
ax.scatter(combined['saf_s_11'],combined['sat_score'])


# In[13]:


safety = ['saf_s_11','saf_p_11','saf_t_11','saf_tot_11']

districts = combined.groupby('school_dist').agg(numpy.mean)
districts.reset_index(inplace=True)
m = Basemap(projection='merc', 
    llcrnrlat=40.496044, 
    urcrnrlat=40.915256, 
    llcrnrlon=-74.255735, 
    urcrnrlon=-73.700272,
    resolution='i')
m.drawmapboundary(fill_color='#85A6D9')
m.drawcoastlines(color='#6D5F47', linewidth=.4)
m.drawrivers(color='#6D5F47', linewidth=.4)
m.fillcontinents(color='white',lake_color='#85A6D9')
latitudes = districts['lat'].tolist()
longitudes = districts['lon'].tolist()
m.scatter(longitudes,latitudes,
          latlon=True,s=100,zorder=2,
          c=districts['saf_s_11'],
         cmap='summer')
plt.show()


# In[14]:


race = ['white_per','asian_per','black_per','hispanic_per']
combined.corr()['sat_score'][race].plot.bar()


# In[15]:


fig,ax = plt.subplots()
ax.scatter(combined['hispanic_per'],combined['sat_score'])
ax.set_xlabel('hispanic_per')
ax.set_ylabel('sat_score')


# The last graphs show how unfair the US SAT system is. It clearly shows that racism is still a big concern in the USA

# In[16]:


schools_greater_hisp = combined[combined['hispanic_per']>95]


# In[17]:


print(schools_greater_hisp['SCHOOL NAME'])


# After researching the schools with above 95% of hispanics, my previous conclusion might be wrong. It appears that these schools primarely teach recent US immigrants with low level of English language, which could explain the lower SAT results.

# In[18]:


schools_low_hisp = combined[(combined['hispanic_per']<10) & 
                           (combined['sat_score']>1800)]


# In[19]:


schools_low_hisp['SCHOOL NAME']


# In[20]:


combined.corr()['sat_score'][['male_per','female_per']].plot.bar()


# In[21]:


combined.plot.scatter('sat_score','female_per')


# In[29]:


print(data['class_size'])


# In[ ]:




