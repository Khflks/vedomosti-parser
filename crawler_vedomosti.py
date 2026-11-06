import sqlite3
import feedparser
import time
import re

class CrawlerVedomosti:

    RSS_URLS = [
        'https://www.vedomosti.ru/rss/news',
        'https://www.vedomosti.ru/rss/issue'
    ]



    def __init__(self):
        self.keywords = []
        self.data = []
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE,
                title TEXT,
                text TEXT,
                pubdate INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE
            )
        ''')
        
        cursor.execute("SELECT COUNT(*) FROM keywords")
        if cursor.fetchone()[0] == 0:
            default_keywords = ['Путин', 'Пулково', 'экономика', 'санкции', 'Россия', 'Вкусно и точка']
            for kw in default_keywords:
                cursor.execute("INSERT INTO keywords (keyword) VALUES (?)", (kw,))
            print(" База создана. Добавлены тестовые ключевые слова.")
            
        conn.commit()
        conn.close()

    def get_database_keywords(self):
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        cursor.execute("SELECT keyword FROM keywords")
        keywords = cursor.fetchall()
        for keyword in keywords:
            self.keywords.append(keyword[0])
        cursor.close()
        conn.close()

    def clean_html(self, raw_html):
        cleanr = re.compile('<.*?>')
        cleantext = re.sub(cleanr, '', raw_html)
        return cleantext.strip()

    def parse_rss(self, keyword: str):
        for url in self.RSS_URLS:
            print(f" Сканируем ленту: {url}")
            feed = feedparser.parse(url)
            
            for entry in feed.entries:
                title = entry.title if hasattr(entry, 'title') else ""
                summary = entry.summary if hasattr(entry, 'summary') else ""
                
                if keyword.lower() in title.lower() or keyword.lower() in summary.lower():
                    clean_text = self.clean_html(summary)
                    
                    
                    pubdate_int = 0
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pubdate_int = int(time.mktime(entry.published_parsed))

                    item = {
                        "url": entry.link,
                        "title": title,
                        "text": clean_text,
                        "pubdate": pubdate_int
                    }
                    self.data.append(item)

        if self.data:
            self.insert_data(self.data)
            self.data = []
        else:
            print(f"   По слову '{keyword}' ничего не найдено.")

    def insert_data(self, data: list):
    
        conn = sqlite3.connect('db.sqlite3')
        cursor = conn.cursor()
        
        for elem in data:
            try:
                
                query = "INSERT OR IGNORE INTO articles(url, title, text, pubdate) VALUES(?,?,?,?)"
                cursor.execute(query, (elem["url"], elem["title"], elem["text"], elem["pubdate"]))
                conn.commit()
                if cursor.rowcount > 0:
                    print(f"    Добавлено: {elem['title']}")
            except Exception as e:
                print(f"    Ошибка: {e}")
                
        cursor.close()
        conn.close()

def main():
    print("Запуск парсера Ведомостей...")
    crawler = CrawlerVedomosti()
    crawler.get_database_keywords()
    
    for keyword in crawler.keywords:
        print(f"\n Ищем новости по слову: {keyword}")
        crawler.parse_rss(keyword=keyword)
    
    print("\n Работа завершена!")

if __name__ == '__main__':
    main()