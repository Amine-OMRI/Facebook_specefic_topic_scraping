# Scraping Facebook with Selenium and Beautifulsoup 
---
Scrape public Facebook posts that match a requested topic and Save the results to a json file and a mongodb database:</br> 
* Scrape the name of the page/user who published the post.
* Scrape the date the post was posted
* Scrape the text of the post content
* Scrape the image(s) attached to the post
* Scrape the link of the publication

```` 
0): Install Requirements:
1): cd to the directory where the requirements.txt file is located.
2): activate your virtualenv.
3): run: pip install -r requirements.txt in your command prompt.
````
How to run it:
```
clean_code_fb_scraping.py [-h] -wdpath WDPATH -credspath CREDSPATH -topic TOPIC -dbname DBNAME [-numOfPost NUMOFPOST] [-infinite INFINITE]

```

* Required arguments:

**-wdpath** WDPATH, -w WDPATH The webdriver path </br>
**-credspath** CREDSPATH, -c CREDSPATH The facebook Credentials path</br>
**-topic** TOPIC, -t TOPIC The requested topic you wanna scrape</br>
**-dbname** DBNAME, -d DBNAME The name of the mongodb database</br>

* Optional arguments:
**-numOfPost** NUMOFPOST, -n NUMOFPOST The requested number of post to scrape4</br>
**-infinite** INFINITE, -i INFINITE Scroll until the end of the page (1 = infinite) (Default is 0)</br>
