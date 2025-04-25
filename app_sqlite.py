from flask import Flask, render_template
import os
import sqlite3

app = Flask(__name__)

# 共用的資料查詢函數
def get_db_connection():
    base_path = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_path, 'data.db')
    conn = sqlite3.connect(db_path)  # SQLite 檔名
    conn.row_factory = sqlite3.Row     # 讓取出的資料像字典一樣操作
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    articles = conn.execute('SELECT * FROM Article WHERE status = "published" ORDER BY createdAt DESC').fetchall()
    
    # 加入字數與文法數量查詢
    article_data = []
    for article in articles:
        article_id = article['id']
        word_count = conn.execute('SELECT COUNT(*) FROM WordArticle WHERE articleId = ?', (article_id,)).fetchone()[0]
        grammar_count = conn.execute('SELECT COUNT(*) FROM GrammarArticle WHERE articleId = ?', (article_id,)).fetchone()[0]
        article_data.append({**dict(article), 'wordCount': word_count, 'grammarCount': grammar_count})
    
    conn.close()
    return render_template('index_adjust.html', articles=article_data)

@app.route('/article/<int:article_id>')
def article_detail(article_id):
    conn = get_db_connection()

    article = conn.execute('SELECT * FROM Article WHERE id = ?', (article_id,)).fetchone()
    words = conn.execute('''
        SELECT Word.* FROM Word
        JOIN WordArticle ON Word.id = WordArticle.wordId
        WHERE WordArticle.articleId = ?
    ''', (article_id,)).fetchall()

    grammar_points = conn.execute(
        '''
        SELECT GrammarPoint.*
        FROM GrammarPoint
        JOIN GrammarArticle ON GrammarPoint.id = GrammarArticle.grammarPointId
        WHERE GrammarArticle.articleId = ?
        ''', (article_id,)
    ).fetchall()

    grammars = []
    for gp in grammar_points:
        examples = conn.execute(
            'SELECT * FROM GrammarExample WHERE grammarPointId = ?', (gp['id'],)
        ).fetchall()
        grammars.append({
            'id': gp['id'],
            'title': gp['title'],
            'explanation': gp['explanation'],
            'examples': examples
        })

    conn.close()

    if article and article['status'] == 'published':
        return render_template(
            'article_detail_adjust.html',
            article=article,
            words=words,
            grammars=grammars
        )
    else:
        return "文章不存在", 404

@app.route('/vocabulary')
def vocabulary():
    conn = get_db_connection()
    words = conn.execute("""
        SELECT DISTINCT Word.*
        FROM Word
        JOIN WordArticle ON Word.id = WordArticle.wordId
        JOIN Article ON WordArticle.articleId = Article.id
        WHERE Article.status = 'published'
        ORDER BY Word.createdAt DESC
    """).fetchall()
    conn.close()
    return render_template('vocabulary_adjust.html', words=words)

@app.route('/word/<int:word_id>')
def word_detail(word_id):
    conn = get_db_connection()
    word = conn.execute('SELECT * FROM Word WHERE id = ?', (word_id,)).fetchone()

    # 找出所有對應的已發佈文章
    articles = conn.execute("""
        SELECT Article.*
        FROM Article
        JOIN WordArticle ON Article.id = WordArticle.articleId
        WHERE WordArticle.wordId = ? AND Article.status = 'published'
        ORDER BY Article.createdAt DESC
    """, (word_id,)).fetchall()

    # 抓取這個單字的例句
    examples = conn.execute("""
        SELECT * FROM WordExample
        WHERE wordId = ?
        ORDER BY createdAt DESC
    """, (word_id,)).fetchall()

    conn.close()
    return render_template('word_detail.html', word=word, articles=articles, examples=examples)

# 編輯單字頁面功能
from flask import request, redirect, url_for
from datetime import datetime

@app.route('/word/<int:word_id>/edit', methods=['GET', 'POST'])
def edit_word(word_id):
    conn = get_db_connection()
    word = conn.execute('SELECT * FROM Word WHERE id = ?', (word_id,)).fetchone()
    examples = conn.execute('SELECT * FROM WordExample WHERE wordId = ? ORDER BY createdAt DESC', (word_id,)).fetchall()

    if request.method == 'POST':
        new_thai = request.form['thai']
        new_chinese = request.form['chinese']
        now = datetime.now().isoformat()

        # 更新 Word
        conn.execute('UPDATE Word SET thai = ?, chinese = ?, updatedAt = ? WHERE id = ?',
                     (new_thai, new_chinese, now, word_id))

        # 遍歷所有例句做更新
        for example in examples:
            example_id = str(example['id'])
            example_thai = request.form.get(f'exampleThai_{example_id}', '').strip()
            example_chinese = request.form.get(f'exampleChinese_{example_id}', '').strip()

            conn.execute('''
                UPDATE WordExample SET thai = ?, chinese = ?, updatedAt = ?
                WHERE id = ?
            ''', (example_thai, example_chinese, now, example_id))

        conn.commit()
        conn.close()
        return redirect(url_for('word_detail', word_id=word_id))

    conn.close()
    return render_template('edit_word.html', word=word, examples=examples)

@app.route('/grammar')
def grammar():
    conn = get_db_connection()
    grammar_points = conn.execute("""
        SELECT DISTINCT GrammarPoint.*
        FROM GrammarPoint
        JOIN GrammarArticle ON GrammarPoint.id = GrammarArticle.grammarPointId
        JOIN Article ON GrammarArticle.articleId = Article.id
        WHERE Article.status = 'published'
        ORDER BY GrammarPoint.createdAt DESC
    """).fetchall()

    # 多對多: 查出每個 grammarPointId 關聯的所有文章（已發佈）
    grammar_article_map = {}
    grammar_article_counts = {}
    grammar_article_links = {}

    rows = conn.execute("""
        SELECT grammarPointId, Article.id as articleId, Article.chineseTitle
        FROM GrammarArticle
        JOIN Article ON GrammarArticle.articleId = Article.id
        WHERE Article.status = 'published'
    """).fetchall()

    for row in rows:
        gid = row['grammarPointId']
        grammar_article_map.setdefault(gid, []).append(row['chineseTitle'])
        grammar_article_links.setdefault(gid, []).append({'id': row['articleId'], 'title': row['chineseTitle']})
        grammar_article_counts[gid] = grammar_article_counts.get(gid, 0) + 1

    grammar_data = []
    for point in grammar_points:
        examples = conn.execute('SELECT * FROM GrammarExample WHERE grammarPointId = ?', (point['id'],)).fetchall()
        grammar_data.append({
            'id': point['id'],
            'title': point['title'],
            'explanation': point['explanation'],
            'examples': examples,
            'articleLinks': grammar_article_links.get(point['id'], []),
            'articleCount': grammar_article_counts.get(point['id'], 0),
            'detailUrl': f'/grammar/{point["id"]}'
        })

    conn.close()
    return render_template('grammar_adjust.html', grammar_points=grammar_data)

@app.route('/grammar/<int:grammar_id>')
def grammar_detail(grammar_id):
    conn = get_db_connection()

    grammar_point = conn.execute(
        'SELECT * FROM GrammarPoint WHERE id = ?', (grammar_id,)
    ).fetchone()

    examples = conn.execute(
        'SELECT * FROM GrammarExample WHERE grammarPointId = ?', (grammar_id,)
    ).fetchall()

    articles = conn.execute("""
        SELECT Article.*
        FROM Article
        JOIN GrammarArticle ON Article.id = GrammarArticle.articleId
        WHERE GrammarArticle.grammarPointId = ? AND Article.status = 'published'
        ORDER BY Article.createdAt DESC
    """, (grammar_id,)).fetchall()

    conn.close()
    return render_template('grammar_detail.html', grammar=grammar_point, examples=examples, articles=articles)

@app.route('/grammar/<int:grammar_id>/edit', methods=['GET', 'POST'])
def edit_grammar(grammar_id):
    conn = get_db_connection()

    if request.method == 'POST':
        new_title = request.form['title']
        new_explanation = request.form['explanation']
        now = datetime.now().isoformat()

        conn.execute('UPDATE GrammarPoint SET title = ?, explanation = ?, updatedAt = ? WHERE id = ?',
                     (new_title, new_explanation, now, grammar_id))

        examples = conn.execute(
            'SELECT * FROM GrammarExample WHERE grammarPointId = ?', (grammar_id,)
        ).fetchall()

        for example in examples:
            ex_id = example['id']
            thai = request.form.get(f'example_thai_{ex_id}', '').strip()
            chinese = request.form.get(f'example_chinese_{ex_id}', '').strip()

            conn.execute('''
                UPDATE GrammarExample
                SET thai = ?, chinese = ?, updatedAt = ?
                WHERE id = ?
            ''', (thai, chinese, now, ex_id))

        conn.commit()
        conn.close()
        return redirect(url_for('grammar_detail', grammar_id=grammar_id))

    grammar_point = conn.execute(
        'SELECT * FROM GrammarPoint WHERE id = ?', (grammar_id,)
    ).fetchone()

    examples = conn.execute(
        'SELECT * FROM GrammarExample WHERE grammarPointId = ?', (grammar_id,)
    ).fetchall()

    articles = conn.execute("""
        SELECT Article.*
        FROM Article
        JOIN GrammarArticle ON Article.id = GrammarArticle.articleId
        WHERE GrammarArticle.grammarPointId = ? AND Article.status = 'published'
        ORDER BY Article.createdAt DESC
    """, (grammar_id,)).fetchall()

    conn.close()
    return render_template('edit_grammar.html', grammar=grammar_point, examples=examples, articles=articles)

@app.route('/admin')
def admin():
    conn = get_db_connection()
    # 加入 status 欄位
    articles = conn.execute('SELECT id, title, createdAt, status FROM Article ORDER BY createdAt DESC').fetchall()
    conn.close()
    return render_template('admin.html', articles=articles)

# 編輯文章頁面，支援 status 欄位更新
from flask import request, redirect
@app.route('/admin/edit-article/<int:article_id>', methods=['GET', 'POST'])
def edit_article(article_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_title = request.form['title']
        new_chinese_title = request.form['chineseTitle']
        new_content = request.form['content']
        new_chinese = request.form['chineseContent']
        new_status = request.form['status']

        cursor.execute("""
            UPDATE Article
            SET title = ?, chineseTitle = ?, content = ?, chineseContent = ?, status = ?
            WHERE id = ?
        """, (new_title, new_chinese_title, new_content, new_chinese, new_status, article_id))

        conn.commit()
        conn.close()
        return redirect('/admin')

    article = conn.execute("SELECT * FROM Article WHERE id = ?", (article_id,)).fetchone()
    conn.close()
    return render_template("edit_article.html", article=article)

# 狀態切換路由
@app.route('/admin/toggle-status/<int:article_id>', methods=['POST'])
def toggle_status(article_id):
    conn = get_db_connection()
    article = conn.execute('SELECT status FROM Article WHERE id = ?', (article_id,)).fetchone()
    new_status = 'draft' if article['status'] == 'published' else 'published'

    conn.execute('UPDATE Article SET status = ? WHERE id = ?', (new_status, article_id))
    conn.commit()
    conn.close()
    return redirect('/admin')

if __name__ == "__main__":
    app.run(debug=True, port=5050)
