import json
import sqlite3
import os
from datetime import datetime

json_path = '/Users/zhangyayin/Documents/泰文IG/泰文網站開發/網站/database/dify_output.json'

# 確保資料夾存在
os.makedirs(os.path.dirname(json_path), exist_ok=True)

now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# SQLite 檔案路徑
db_path = "/Users/zhangyayin/Documents/泰文IG/泰文網站開發/網站/data.db"

with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    # Create tables if not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Article (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            chineseTitle TEXT,
            content TEXT,
            chineseContent TEXT,
            category TEXT,
            url TEXT,
            status TEXT,
            createdAt TEXT,
            updatedAt TEXT,
            authorId INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Word (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thai TEXT,
            chinese TEXT,
            type TEXT,
            pronunciation TEXT,
            articleId INTEGER,
            createdAt TEXT,
            updatedAt TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS WordArticle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            wordId INTEGER,
            articleId INTEGER,
            FOREIGN KEY(wordId) REFERENCES Word(id),
            FOREIGN KEY(articleId) REFERENCES Article(id),
            UNIQUE(wordId, articleId)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GrammarPoint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            explanation TEXT,
            articleId INTEGER,
            createdAt TEXT,
            updatedAt TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GrammarExample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thai TEXT,
            chinese TEXT,
            grammarPointId INTEGER,
            createdAt TEXT,
            updatedAt TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS GrammarArticle (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grammarPointId INTEGER,
            articleId INTEGER,
            FOREIGN KEY(grammarPointId) REFERENCES GrammarPoint(id),
            FOREIGN KEY(articleId) REFERENCES Article(id),
            UNIQUE(grammarPointId, articleId)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS WordExample (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thai TEXT,
            chinese TEXT,
            wordId INTEGER,
            createdAt TEXT,
            updatedAt TEXT,
            FOREIGN KEY(wordId) REFERENCES Word(id)
        )
    """)

    author_id = 999  # fixed author id as before

    # Insert Article
    article = data['article']
    cursor.execute("""
        INSERT INTO Article (title, chineseTitle, content, chineseContent, category, url, status, createdAt, updatedAt, authorId)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article['title'].strip(),
        article['chineseTitle'].strip(),
        article['content'].strip(),
        article['chineseContent'].strip(),
        article['category'].strip(),
        article['url'].strip(),
        article['status'].strip(),
        now,
        now,
        author_id
    ))
    article_id = cursor.lastrowid

    # Insert Words
    for word in data['words']:
        # 檢查是否已有該單字
        cursor.execute("SELECT id FROM Word WHERE thai = ?", (word['thai'].strip(),))
        result = cursor.fetchone()
        if result:
            word_id = result[0]
            # 更新 updatedAt 與 articleId
            cursor.execute("UPDATE Word SET updatedAt = ?, articleId = ? WHERE id = ?", (now, article_id, word_id))
        else:
            cursor.execute("""
                INSERT INTO Word (thai, chinese, type, pronunciation, articleId, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                word['thai'].strip(),
                word['meaning'].strip(),
                word['type'].strip(),
                word.get('pronunciation', '').strip(),
                article_id,
                now,
                now
            ))
            word_id = cursor.lastrowid

        # 插入 WordExample（如果有）
        for example in word.get("examples", []):
            cursor.execute("""
                INSERT INTO WordExample (thai, chinese, wordId, articleId, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                example.get('thai', '').strip(),
                example.get('chinese', '').strip(),
                word_id,
                article_id,
                now,
                now
            ))

        # 插入關聯表
        cursor.execute("""
            INSERT OR IGNORE INTO WordArticle (wordId, articleId)
            VALUES (?, ?)
        """, (word_id, article_id))
        print(f"🔗 Word '{word['thai']}' (id: {word_id}) linked to article {article_id}")

    # Insert GrammarPoints and GrammarExamples
    for grammar in data['grammarPoints']:
        cursor.execute("""
            INSERT INTO GrammarPoint (title, explanation, articleId, createdAt, updatedAt)
            VALUES (?, ?, ?, ?, ?)
        """, (
            grammar['title'].strip(),
            grammar['explanation'].strip(),
            article_id,
            now,
            now
        ))
        grammar_id = cursor.lastrowid

        # 插入多對多關聯
        cursor.execute("""
            INSERT INTO GrammarArticle (grammarPointId, articleId)
            VALUES (?, ?)
        """, (grammar_id, article_id))
        print(f"🔗 Grammar '{grammar['title']}' (id: {grammar_id}) linked to article {article_id}")

        for example in grammar['examples']:
            cursor.execute("""
                INSERT INTO GrammarExample (thai, chinese, grammarPointId, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?)
            """, (
                example['thai'].strip(),
                example['chinese'].strip(),
                grammar_id,
                now,
                now
            ))

    conn.commit()
    print("✅ SQLite 更新完成！")

except Exception as e:
    conn.rollback()
    print("❌ 發生錯誤：", e)

finally:
    cursor.close()
    conn.close()