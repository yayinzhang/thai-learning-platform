import sqlite3
import os
import mysql.connector

# 連接資料庫
base_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_path, "data.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

mysql_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="thai_learning"
)
mysql_cursor = mysql_conn.cursor()

# 取得最新一筆 article 的 id
mysql_cursor.execute("SELECT id FROM Article ORDER BY createdAt DESC LIMIT 1")
latest_article = mysql_cursor.fetchone()

if latest_article:
    article_id = latest_article[0]

    # 刪除 MySQL 資料
    mysql_cursor.execute("DELETE FROM Word WHERE articleId = %s", (article_id,))
    mysql_cursor.execute("""
        DELETE FROM GrammarExample WHERE grammarPointId IN (
            SELECT id FROM GrammarPoint WHERE articleId = %s
        )
    """, (article_id,))
    mysql_cursor.execute("DELETE FROM GrammarPoint WHERE articleId = %s", (article_id,))
    mysql_cursor.execute("DELETE FROM Article WHERE id = %s", (article_id,))
    mysql_conn.commit()

    # 刪除 SQLite 資料
    cursor.execute("DELETE FROM Word WHERE articleId = ?", (article_id,))
    cursor.execute("""
        DELETE FROM GrammarExample WHERE grammarPointId IN (
            SELECT id FROM GrammarPoint WHERE articleId = ?
        )
    """, (article_id,))
    cursor.execute("DELETE FROM GrammarPoint WHERE articleId = ?", (article_id,))
    cursor.execute("DELETE FROM Article WHERE id = ?", (article_id,))
    conn.commit()

    print(f"✅ 已成功刪除最新文章（ID: {article_id}）及相關資料")
else:
    print("⚠️ 找不到任何文章可以刪除")

cursor.close()
conn.close()
mysql_cursor.close()
mysql_conn.close()