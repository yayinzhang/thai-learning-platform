import mysql.connector
import sqlite3
import os
base_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_path, "data.db")

# 連接 MySQL
mysql_conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    password='root',
    database='thai_learning'
)
mysql_cursor = mysql_conn.cursor(dictionary=True)

# 建立 SQLite 檔案
sqlite_conn = sqlite3.connect(db_path)
sqlite_cursor = sqlite_conn.cursor()

# 建立資料表（根據你原本結構）
sqlite_cursor.execute('DROP TABLE IF EXISTS Article')
sqlite_cursor.execute('DROP TABLE IF EXISTS Word')
sqlite_cursor.execute('DROP TABLE IF EXISTS GrammarPoint')
sqlite_cursor.execute('DROP TABLE IF EXISTS GrammarExample')
sqlite_cursor.execute('DROP TABLE IF EXISTS User')

sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS Article (
    id INTEGER PRIMARY KEY,
    title TEXT,
    content TEXT,
    chineseContent TEXT,
    category TEXT,
    url TEXT,
    status TEXT,
    createdAt TEXT,
    updatedAt TEXT,
    authorId INTEGER,
    chineseTitle TEXT
)
''')

sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS Word (
    id INTEGER PRIMARY KEY,
    thai TEXT,
    chinese TEXT,
    type TEXT,
    pronunciation TEXT,
    articleId INTEGER,
    createdAt TEXT,
    updatedAt TEXT
)
''')

sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS GrammarPoint (
    id INTEGER PRIMARY KEY,
    title TEXT,
    explanation TEXT,
    articleId INTEGER,
    createdAt TEXT,
    updatedAt TEXT
)
''')

sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS GrammarExample (
    id INTEGER PRIMARY KEY,
    thai TEXT,
    chinese TEXT,
    grammarPointId INTEGER,
    createdAt TEXT,
    updatedAt TEXT
)
''')

sqlite_cursor.execute('''
CREATE TABLE IF NOT EXISTS User (
    id INTEGER PRIMARY KEY,
    email TEXT,
    name TEXT,
    createdAt TEXT,
    updatedAt TEXT,
    role TEXT,
    username TEXT
)
''')

# 匯出 Article 資料
mysql_cursor.execute("SELECT * FROM Article")
articles = mysql_cursor.fetchall()
for a in articles:
    sqlite_cursor.execute('''
        INSERT INTO Article (id, title, content, chineseContent, category, url, status, createdAt, updatedAt, authorId, chineseTitle)
        VALUES (:id, :title, :content, :chineseContent, :category, :url, :status, :createdAt, :updatedAt, :authorId, :chineseTitle)
    ''', a)

# 匯出 Word 資料
mysql_cursor.execute("SELECT * FROM Word")
words = mysql_cursor.fetchall()
for w in words:
    sqlite_cursor.execute('''
        INSERT INTO Word (id, thai, chinese, type, pronunciation, articleId, createdAt, updatedAt)
        VALUES (:id, :thai, :chinese, :type, :pronunciation, :articleId, :createdAt, :updatedAt)
    ''', w)

# 匯出 GrammarPoint 資料
mysql_cursor.execute("SELECT * FROM GrammarPoint")
grammar_points = mysql_cursor.fetchall()
for gp in grammar_points:
    sqlite_cursor.execute('''
        INSERT INTO GrammarPoint (id, title, explanation, articleId, createdAt, updatedAt)
        VALUES (:id, :title, :explanation, :articleId, :createdAt, :updatedAt)
    ''', gp)

# 匯出 GrammarExample 資料
mysql_cursor.execute("SELECT * FROM GrammarExample")
grammar_examples = mysql_cursor.fetchall()
for ge in grammar_examples:
    sqlite_cursor.execute('''
        INSERT INTO GrammarExample (id, thai, chinese, grammarPointId, createdAt, updatedAt)
        VALUES (:id, :thai, :chinese, :grammarPointId, :createdAt, :updatedAt)
    ''', ge)

# 匯出 User 資料
mysql_cursor.execute("SELECT * FROM User")
users = mysql_cursor.fetchall()
for u in users:
    sqlite_cursor.execute('''
        INSERT INTO User (id, email, name, createdAt, updatedAt, role, username)
        VALUES (:id, :email, :name, :createdAt, :updatedAt, :role, :username)
    ''', u)

# 關閉連線
sqlite_conn.commit()
sqlite_conn.close()
mysql_cursor.close()
mysql_conn.close()

print("✅ 資料成功轉存為 data.db！")