# -*- coding: utf-8 -*-
"""
Created on Wed May 25 18:21:14 2022

@author: Asus
"""

#Import Libraries
import requests
from datetime import datetime
from datetime import date
import json
import traceback
import time
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import firebase_admin 
from firebase_admin import db
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import sys

#General variables
#strKey = "94d8b295ca9e47beabe1495f8a5e117f"
strKey = "aa0c548c1243464091e9918933732d83"
#strKey = "082e61f3ef2aa34a3f5e34329914c726"
lstStrKey = ["082e61f3ef2aa34a3f5e34329914c726","ed8c108adce801e378bfea9c05245e8a","94d8b295ca9e47beabe1495f8a5e117f"]
lstStrKey = ["94d8b295ca9e47beabe1495f8a5e117f","aa0c548c1243464091e9918933732d83","082e61f3ef2aa34a3f5e34329914c726"]
strCountry = "in"
strSearchQuery = "happy"
strTopHeadlinesURL = "https://newsapi.org/v2/top-headlines?country=" + strCountry + "&apiKey=" + strKey
strSearchQueryURL = "https://newsapi.org/v2/everything?q="
lstMasterNews = []
lstMasterNewsTitle = []
lstGoodNews = []
dtGoodNews = pd.DataFrame()
dicGoodNews = {"Article_Title":[],"Article_Description":[],"Article_Date":[],"Article_ImageURL":[],"Article_Source":[],"Article_Summary":[],"Article_URL":[],"Article_CompScore":[],"Article_PosScore":[],"Article_Category":[],"Article_TimeStamp":[]}
lstQueryString1 = ["happy","amazing","nice","achievement","fortunate","joyful","welfare","astonishing","peace","good","marvellous"]
lstQueryString2 = ["awesome","donate","help","lucky","grant","oppurtunity","invention","create","discover","great"]
lstNewsCategories = {"sports":["sports","cricket","football","olympics","tennis","badmintion","athletics","chess","swimming","basketball"],"politics":["politics","political economy","political science","political history","democracy","Political philosophy","liberalism","socialism","electoral systems","election results","polling","political parties","politicians"],"business":["Growth of Economy","Adaptive Leadership","Business Models","Business Plans","Competitive Strategy","Corporate Social Responsibility","Business Creativity","Cross-cultural Management","Customer-centricity","Design Thinking","Digital Transformation","Disruptive Innovation","Economics","Entrepreneurship","Workspaces Design","Venture Funding","Start-ups"],"science":["Artificial Intelligence in Farming","Engineering","Astronomy","Biology","Chemisrty","Cognitive Science","Computer Science","Ecology","Geography","Geology","Physics","Psychology","Sociology","Meteorology","Palaeontology","Methodology","Entomology","Microbiology"],"education":["Government Policies on education","Virtual classrooms","Schools","School Exam","Education Course","Exam Results","Gold Medalist","Topper"],"entertainment":["bollywood","hollywood","cinema","stand up comedy","comedy","actor","kollywood","tollywood","comedian","music","dance","circus","entertainment","magic","fireworks","shopping","theatre"],"health":["Fitness","Nutrition","Health System","Cure","Work-life balance","Workplace Health and Safety","Wellness"],"fashion":["fashion trend","fashion","costume","desginer cloth","Clothing fashion","womens fashion","mens fashion","male models","female models"],"Agriculture":["Food","Nutrition","Organic Farming","Organic Food","Sustainable Agriculture","Government Policies on Agriculture","Importance of Agriculture in Life","21st Century Agriculture","Farming with Waste Management","Role of Agriculture in the Economy","Green Farm","Artificial Intelligence in Farming"]}
lstCategoryNames = ["sports","politics","education","science","agriculture","business","entertainment","fashion","health"]
lstTempCategoryNames = []
#Definitions
def fetch_news(strURL):
    reqNews = requests.get(strURL)
    flgNews = reqNews.status_code
    if flgNews == 200:
        strNews = reqNews.text
        dicNews = json.loads(strNews)
        lstNews = dicNews["articles"]
        print(len(lstNews))
        return lstNews
    else:
        lstNews = ["No data"]
        return lstNews

def clean(raw):
    """ Remove hyperlinks and markup """
    result = re.sub("<[a][^>]*>(.+?)</[a]>", 'Link.', raw)
    result = re.sub("<[o][^>]*>", "", result)
    result = re.sub("</[o][^>]>", "", result)
    result = re.sub("<[l][^>]*>", '', result)
    result = re.sub("</[l][^>]>", '', result)
    result = re.sub('&gt;', "", result)
    result = re.sub('&#x27;', "'", result)
    result = re.sub('&quot;', '"', result)
    result = re.sub('&#x2F;', ' ', result)
    result = re.sub('<p>', ' ', result)
    result = re.sub('</i>', '', result)
    result = re.sub('&#62;', '', result)
    result = re.sub('<i>', ' ', result)
    result = re.sub("\n", '', result)
    return result

def make_sentences(text):
    """ Break apart text into a list of sentences """
    sentences = text.split(".")
    return sentences

def get_scores(sentences):
    """ Call predict on sentence of a text """
    results = []
    intPosScore = 0.0
    intCompScore = 0.0
    intNegScore = 0.0
    objSentiAnalyzer = SentimentIntensityAnalyzer()
    for sentence in sentences:
        sentiment_dict = objSentiAnalyzer.polarity_scores(sentence)
        intPosScore = intPosScore + sentiment_dict['pos']
        intCompScore = intCompScore + sentiment_dict['compound']
        intNegScore = intNegScore + sentiment_dict['neg']
    results.append(intCompScore)
    results.append(intPosScore)
    results.append(intNegScore)
    return results

def get_sum(scores):
    result = round(sum(scores), 3)
    return result

def assign_category(lstNewsCategories,strNews):
    for category in lstNewsCategories:
                lstCategoryQuery = lstNewsCategories[category]
                for query in lstCategoryQuery:# 
                    strNews = strNews
                    if strNews.find(query)>-1:
                       return category


#Main Process
#Compile good news query string
strGoodNewsQuery1 = ""
for querystring in lstQueryString1:
    strGoodNewsQuery1 = querystring + " OR " + strGoodNewsQuery1
strGoodNewsQuery1 = strGoodNewsQuery1[:strGoodNewsQuery1.rfind(" OR ")]
strGoodNewsQuery1 = "(" + strGoodNewsQuery1 + ")"

strGoodNewsQuery2 = ""
for querystring in lstQueryString2:
    strGoodNewsQuery2 =  querystring + " OR " + strGoodNewsQuery2
strGoodNewsQuery2 = strGoodNewsQuery2[:strGoodNewsQuery2.rfind(" OR ")]
strGoodNewsQuery2 = "(" + strGoodNewsQuery2 + ")"
lstCompiledQuery = [strGoodNewsQuery1,strGoodNewsQuery2]

print(len(strGoodNewsQuery1),len(strGoodNewsQuery2))

#Fetch Top Headlines
lstFetchedNews = fetch_news(strTopHeadlinesURL)
if not ( lstFetchedNews == ["No data"]):
    for news in lstFetchedNews:
        title = news["title"]
        if title not in lstMasterNewsTitle:
            strDescription = news["description"]
            if ( strDescription == None): 
                strDescription = "abc"
            news["Category"] = assign_category(lstNewsCategories,strDescription)
            lstMasterNews.append(news)
            lstMasterNewsTitle.append(title)
#Fetch search query news
intQueryCount = 0
intStrKeyCount = 0
strCurKey = lstStrKey[intStrKeyCount]
for strGoodNewsQuery in lstCompiledQuery:
    for category in lstNewsCategories:
        lstCategoryQuery = lstNewsCategories[category]
        for query in lstCategoryQuery:
            intQueryCount += 1
            if intQueryCount == 101:
                intQueryCount = 0
                intStrKeyCount += 1
                try:
                    strCurKey = lstStrKey[intStrKeyCount]
                except:
                    print("Key limit reached")
            strURL = strSearchQueryURL + query +' AND '+ strGoodNewsQuery +"&apiKey=" + strCurKey
            time.sleep(1)
            lstFetchedNews = fetch_news(strURL)
            if not ( lstFetchedNews == ["No data"]):
                for news in lstFetchedNews:
                    title = news["title"]
                    news["Category"] = category
                    if title not in lstMasterNewsTitle:
                        lstMasterNews.append(news)
                        lstMasterNewsTitle.append(title)
lstMasterNewsTitle = []
print("Total Query Count is "+str(intQueryCount))

#Filter Good News
for news in lstMasterNews:
    try:
        strNewsContent = news["content"]
        strNewsContent = clean(strNewsContent)
        lstNewsContentSent = make_sentences(strNewsContent)
        lstPolarityScore = get_scores(lstNewsContentSent)
        #Check if positive
        intCompScore = lstPolarityScore[0]
        intPosScore = lstPolarityScore[1]
        intNegScore = lstPolarityScore[2]
        if intCompScore > 0.5 and intPosScore > 0.5 and intNegScore < 0.1:
            #Update dictionary
            strSource = news["source"]
            if not news["Category"] in lstTempCategoryNames:
                lstTempCategoryNames.append( news["Category"])
            strSource = str(strSource["name"])
            strDateTime = str(news["publishedAt"])
            strDate = strDateTime
            try:
                strDateTime = strDateTime[:10]
                dat = datetime.strptime(strDateTime, '%Y-%m-%d' )
                newDat = dat.strftime('%d %b %Y')
                strDate = str(newDat)
                intTimeStamp = int(datetime.timestamp(dat))
            except:
                strDate = str(date.today())
                intTimeStamp = 0
            dicGoodNews["Article_Title"].append(news["title"])
            dicGoodNews["Article_Description"].append(news["description"])
            dicGoodNews["Article_ImageURL"].append(news["urlToImage"])
            dicGoodNews["Article_Date"].append(strDate)
            dicGoodNews["Article_Summary"].append(news["description"])
            dicGoodNews["Article_URL"].append(news["url"])
            dicGoodNews["Article_Source"].append(strSource)
            dicGoodNews["Article_CompScore"].append(intCompScore)
            dicGoodNews["Article_PosScore"].append(intPosScore)
            dicGoodNews["Article_Category"].append(news["Category"])
            dicGoodNews["Article_TimeStamp"].append(intTimeStamp)
    except Exception as e:
        strMessage = "Error in news - " + news["title"] + " ---- "
        for i in traceback.format_exception(*sys.exc_info()):
            strMessage = strMessage + " " + i
        print(strMessage)

#Fill empty category
""" for cat in lstCategoryNames:
    if not cat in lstTempCategoryNames:
        dicGoodNews["Article_Title"].append("We are fetching Good News in "+cat+" category. Please try after sometime.")
        dicGoodNews["Article_Description"].append("")
        dicGoodNews["Article_ImageURL"].append("")
        dicGoodNews["Article_Date"].append("")
        dicGoodNews["Article_Summary"].append("Chose a different category")
        dicGoodNews["Article_URL"].append("")
        dicGoodNews["Article_Source"].append("")
        dicGoodNews["Article_CompScore"].append("")
        dicGoodNews["Article_PosScore"].append("")
        dicGoodNews["Article_Category"].append(cat)
        dicGoodNews["Article_TimeStamp"].append(0) """
#Sort Good News
dtGoodNews = pd.DataFrame(dicGoodNews)
#dtGoodNews = dtGoodNews.sort_values(by=["Article_CompScore","Article_PosScore"],ascending=False)
dtGoodNews = dtGoodNews.sort_values(by=["Article_TimeStamp","Article_CompScore","Article_PosScore"],ascending=False)
dtGoodNews = dtGoodNews.reset_index()



#print(dtGoodNews)
print(len(lstMasterNews))
print(len(dtGoodNews))

#Write To FireBase
cred_obj = credentials.Certificate("C:/Users/Asus/OneDrive/Documents/Sweet Truth/News Fetcher/Firebase Key/sweettruth-34bf0-firebase-adminsdk-g2uoi-95824e4671.json")
firebase_admin.initialize_app(cred_obj)

db = firestore.client()
intArticleNum = 0
for index, row in dtGoodNews.iterrows():
    strDocumentName = str(row["Article_Title"])
    strDocumentName = strDocumentName.replace("/"," ")
    doc_ref = db.collection(u'collection_GoodNews').document(strDocumentName)
    doc = doc_ref.get()
    if doc.exists:
        print("Document already exists - ",strDocumentName)
    else:
        intArticleNum += 1
        doc_ref.set({
            u'Article_Title': str(row["Article_Title"]),
            u'Article_Description': str(row["Article_Description"]),
            u'Article_ImageURL': str(row["Article_ImageURL"]),
            u'Article_Date': str(row["Article_Date"]),
            u'Article_Summary': str(row["Article_Summary"]),
            u'Article_URL': str(row["Article_URL"]),
            u'Article_Source': str(row["Article_Source"]),
            u'Article_Category' : str(row["Article_Category"]),
            u'Article_Timestamp' : str(row["Article_TimeStamp"])
            })
print(str(intArticleNum))


 