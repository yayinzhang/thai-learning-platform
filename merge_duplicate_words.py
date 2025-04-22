import sqlite3
from collections import defaultdict

# 資料庫路徑（請根據你實際的位置調整）
DB_PATH = '/Users/zhangyayin/Documents/泰文IG/泰文網站開發/網站/data.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1️⃣ 找出所有重複的 word（用四欄比對）
cur.execute("""
SELECT thai, chinese, type, COUNT(*) as count
FROM Word
GROUP BY thai, chinese, type
HAVING count > 1
""")
duplicates = cur.fetchall()

print(f"🔍 找到 {len(duplicates)} 組重複的單字")

# 2️⃣ 依序處理每組重複單字
for d in duplicates:
    key = (d["thai"], d["chinese"], d["type"])

    # 取得這組重複的所有 id
    cur.execute("""
        SELECT id FROM Word
        WHERE thai = ? AND chinese = ? AND type = ?
        ORDER BY id ASC
    """, key)
    word_ids = [row["id"] for row in cur.fetchall()]

    # 保留最小的那筆，其餘刪除
    keep_id = word_ids[0]
    remove_ids = word_ids[1:]

    # 更新 WordArticle 的關聯
    for rid in remove_ids:
        print(f"🔁 將 WordArticle 中 wordId {rid} -> {keep_id}")
        cur.execute("""
            UPDATE OR IGNORE WordArticle SET wordId = ?
            WHERE wordId = ?
        """, (keep_id, rid))

    # 刪除重複的 word
    cur.execute("DELETE FROM Word WHERE id IN ({})".format(
        ','.join(['?'] * len(remove_ids))), remove_ids)

    print(f"🗑️ 已刪除重複的 word id: {remove_ids}")

# 儲存變更
conn.commit()
conn.close()
print("✅ 完成重複單字的合併與清理！")