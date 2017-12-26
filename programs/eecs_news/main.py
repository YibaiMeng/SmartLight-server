import requests
import bs4
import sys

r = requests.get("http://eecs.pku.edu.cn/Survey/Notice/")
parser = bs4.BeautifulSoup(r.text, "lxml")
articles = parser.findAll('a', class_="hvr-shutter-out-vertical")

try:
    sys.argv[2]
    n = int(sys.argv[2])
    if n in range(10):
        rp = requests.get("http://eecs.pku.edu.cn/Survey/Notice/"+articles[n]["href"])
        print(articles[n].p.text)
        parser2 = bs4.BeautifulSoup(rp.text, "lxml")
        text = parser2.find('div', class_="neiyeMnr")
        print(text.text)
except:
    for article in articles:
        print(article.p.text, "http://eecs.pku.edu.cn/Survey/Notice/"+article["href"])
