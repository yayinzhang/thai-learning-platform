import sqlite3
import csv
from datetime import datetime

# 連線到你的 SQLite 資料庫
conn = sqlite3.connect('/Users/zhangyayin/Documents/泰文IG/泰文網站開發/網站/data.db')
cursor = conn.cursor()

# 讀取 CSV 檔案
with open('/Users/zhangyayin/Documents/泰文IG/泰文網站開發/網站/database/example_data.csv', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)

    for row in reader:
        wordId = int(row['wordId'])
        articleId = int(row['articleId']) if row['articleId'] else None
        thai = row['exampleThai'].strip()
        chinese = row['exampleChinese'].strip()
        now = datetime.now().isoformat()

        # 避免重複：你可以依 wordId + articleId 做唯一組合檢查
        cursor.execute('''
            SELECT id FROM WordExample WHERE wordId = ? AND articleId = ?
        ''', (wordId, articleId))
        existing = cursor.fetchone()

        if existing:
            # 已存在就更新
            cursor.execute('''
                UPDATE WordExample
                SET thai = ?, chinese = ?, updatedAt = ?
                WHERE id = ?
            ''', (thai, chinese, now, existing[0]))
        else:
            # 不存在就新增
            cursor.execute('''
                INSERT INTO WordExample (thai, chinese, wordId, articleId, createdAt, updatedAt)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (thai, chinese, wordId, articleId, now, now))

conn.commit()
conn.close()

print("✅ 資料整併完成！")