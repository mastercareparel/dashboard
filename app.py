import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import pymysql


load_dotenv()
app = Flask(__name__)


app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")



def get_db_connection():
    host = os.getenv("DB_HOST")
    port = int(os.getenv("DB_PORT"))
    print("USING HOST:", host, "PORT:", port)
    conn = pymysql.connect(
        host=host,
        port=port,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    print("DB CONNECTED (PyMySQL)")
    return conn

def get_db():
    return get_db_connection()

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()


        if not username or not email or not password:
            return render_template('registration.html', error="All fields are required.")
        if password != confirm:
            return render_template('registration.html', error="Passwords do not match.")


        try:
            conn = get_db_connection()
            cur = conn.cursor()

            cur.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            existing = cur.fetchone()
            if existing:
                cur.close()
                conn.close()
                return render_template('registration.html', error="Username or email already exists.")


            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email, password)
            )
            conn.commit()
            cur.close()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            print("REGISTER ERROR:", e)
            return render_template('registration.html', error="Server error, try again.")

    return render_template('registration.html')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip() 
        password = request.form.get('password', '').strip()


        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT id, username, email, password FROM users "
                "WHERE username=%s OR email=%s",
                (identifier, identifier)
            )
            user = cur.fetchone()
            cur.close()
            conn.close()


            if not user or user['password'] != password:
                return render_template('login.html', error="Invalid credentials.")

            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('performance_page'))
        except Exception as e:
            print("LOGIN ERROR:", e)
            return render_template('login.html', error="Server error, try again.")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/home')
def performance_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('home.html', username=session.get('username'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template('index.html', username=session.get('username'))


from datetime import datetime
from flask import Flask, request, jsonify, session

@app.route('/performance-save', methods=['POST'])
def performance_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    total_score = float(data.get('total_score', 0))
    grade = data.get('grade', 'D')
    date_str = data.get('calc_date')     

    if date_str:
        calc_date = date_str
    else:
        calc_date = datetime.utcnow().strftime('%Y-%m-%d')

    user_id = session['user_id']

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO PerformanceDashboard (calc_datetime, total_score, grade, user_id)
            VALUES (%s, %s, %s, %s)
            """,
            (calc_date, total_score, grade, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'calc_datetime': calc_date})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/performance-history', methods=['GET'])
def performance_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, calc_datetime, total_score, grade "
            "FROM PerformanceDashboard "
            "WHERE user_id = %s "
            "ORDER BY calc_datetime DESC",
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'items': rows})
    except Exception as e:
        print("HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/performance-delete/<int:row_id>', methods=['POST'])
def performance_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM PerformanceDashboard WHERE id = %s AND user_id = %s",
            (row_id, user_id)
        )
        conn.commit()   
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route("/Exltp")
def Exltp():
    if 'user_id' not in session:
        return redirect(url_for('login'))
   
    return render_template("calculators/LTP.html", username=session.get('username'))

@app.route('/ltp-save', methods=['POST'])
def ltp_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    user_id     = session['user_id']

    service_no  = data.get('service_no')
    date_reg    = data.get('date_reg')      
    date_close  = data.get('date_close')    
    days        = data.get('days')          
    status      = data.get('status')        
    hours_diff  = data.get('hours_diff')   
    within_2hr  = data.get('within_2hr')    

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO LTP
                (user_id, service_no, date_reg, date_close,
                 days, status, hours_diff, within_2hr)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                user_id,
                service_no,
                date_reg if date_reg else None,
                date_close if date_close else None,
                days,
                status,
                hours_diff,
                within_2hr
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("LTP INSERT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ltp-history', methods=['GET'])
def ltp_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT id, service_no, date_reg, date_close,
                   days, status, hours_diff, within_2hr, created_at
            FROM LTP
            WHERE user_id = %s
            ORDER BY date_reg DESC, id DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'items': rows})
    except Exception as e:
        print("LTP HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ltp-delete/<int:row_id>', methods=['DELETE'])
def ltp_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("DELETE FROM LTP WHERE id=%s AND user_id=%s", (row_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("LTP DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ltp-edit/<int:row_id>', methods=['PUT'])
def ltp_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    user_id = session['user_id']

    service_no  = data.get('service_no')
    date_reg    = data.get('date_reg')
    date_close  = data.get('date_close')
    days        = data.get('days')
    status      = data.get('status')
    hours_diff  = data.get('hours_diff')
    within_2hr  = data.get('within_2hr')

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            UPDATE LTP
               SET service_no=%s,
                   date_reg=%s,
                   date_close=%s,
                   days=%s,
                   status=%s,
                   hours_diff=%s,
                   within_2hr=%s
             WHERE id=%s AND user_id=%s
            """,
            (
                service_no,
                date_reg if date_reg else None,
                date_close if date_close else None,
                days,
                status,
                hours_diff,
                within_2hr,
                row_id,
                user_id,
            )
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("LTP UPDATE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/d0_overall")
def d0_overall():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("calculators/d0_overall.html",
                           username=session.get('username'))


# ---------- D+0 (OVERALL) APIs ----------

@app.route('/d0-overall/save', methods=['POST'])
def d0_overall_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()          # obj from calculateAll()
    print("D0 OVERALL JSON:", data)

    user_id    = session['user_id']
    record_date = data.get('date')     # "YYYY-MM-DD"
    actual      = data.get('actual', 0)
    percent_d0  = data.get('percentage', 0)
    score       = data.get('score', 0)

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO d0_overall_history
                (record_datetime, actual, percent_d0, score, user_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (record_date, actual, percent_d0, score, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 OVERALL INSERT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/d0-overall/history', methods=['GET'])
def d0_overall_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            SELECT
              id,
              record_datetime,
              actual,
              percent_d0,
              score
            FROM d0_overall_history
            WHERE user_id = %s
            ORDER BY record_datetime DESC, id DESC
            """,
            (user_id,)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        cleaned = []
        for r in rows:
            dt = r.get('record_datetime')
            s = str(dt)
            # "Wed, 03 Dec 2025 00:00:00 GMT" -> "Wed, 03 Dec 2025"
            if '00:00:00' in s and 'GMT' in s:
                date_str = s.split('00:00:00')[0].strip()
            else:
                # "2025-12-03 00:00:00" -> "2025-12-03"
                date_str = s[:10]
            cleaned.append({
                'id': r['id'],
                'record_date': date_str,
                'actual': r['actual'],
                'percent_d0': r['percent_d0'],
                'score': r['score'],
            })

        return jsonify({'status': 'ok', 'items': cleaned})
    except Exception as e:
        print("D0 OVERALL HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/d0-overall/edit/<int:row_id>', methods=['PUT'])
def d0_overall_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data    = request.get_json()
    user_id = session['user_id']

    record_date = data.get('date')
    actual      = data.get('actual', 0)
    percent_d0  = data.get('percentage', 0)
    score       = data.get('score', 0)

    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            UPDATE d0_overall_history
               SET record_datetime = %s,
                   actual          = %s,
                   percent_d0      = %s,
                   score           = %s
             WHERE id = %s AND user_id = %s
            """,
            (record_date, actual, percent_d0, score, row_id, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 OVERALL EDIT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/d0-overall/delete/<int:row_id>', methods=['DELETE'])
def d0_overall_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "DELETE FROM d0_overall_history WHERE id = %s AND user_id = %s",
            (row_id, user_id)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 OVERALL DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/d0_premium")
def d0_premium():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("calculators/d0_premium.html")


# ---------- D+0 PREMIUM APIs ----------

from datetime import datetime

@app.route('/d0-premium/save', methods=['POST'])
def d0_premium_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id    = session['user_id']
        actual     = float(data.get('actual', 0))
        percent_d0 = float(data.get('percentage', 0))
        score      = float(data.get('score', 0))

        # NEW: get date string from frontend and parse it
        date_str = data.get('date')        # e.g. '2025-12-06'
        if not date_str:
            # fallback: today if user didn’t pick a date
            record_datetime = datetime.today()
        else:
            # HTML input type="date" uses YYYY-MM-DD
            record_datetime = datetime.strptime(date_str, "%Y-%m-%d")

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO d0_premium_history
                (user_id, record_datetime, actual, percent_d0, score)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, record_datetime, actual, percent_d0, score))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 PREMIUM SAVE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/d0-premium/history', methods=['GET'])
def d0_premium_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT id,
                   DATE(record_datetime) AS record_date,
                   actual,
                   percent_d0,
                   score
            FROM d0_premium_history
            WHERE user_id = %s
            ORDER BY record_datetime DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # IMPORTANT: convert date object -> 'YYYY-MM-DD' string
        items = []
        for r in rows:
            rd = r['record_date']
            if rd is not None:
                rd_str = rd.strftime("%Y-%m-%d")
            else:
                rd_str = ""
            items.append({
                'id': r['id'],
                'record_date': rd_str,
                'actual': r['actual'],
                'percent_d0': r['percent_d0'],
                'score': r['score']
            })

        return jsonify({'status': 'ok', 'items': items})
    except Exception as e:
        print("D0 PREMIUM HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/d0-premium/edit/<int:row_id>', methods=['PUT'])
def d0_premium_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id     = session['user_id']
        actual      = float(data.get('actual', 0))
        percent_d0  = float(data.get('percentage', 0))
        score       = float(data.get('score', 0))

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE d0_premium_history
               SET actual = %s,
                   percent_d0 = %s,
                   score = %s
             WHERE id = %s AND user_id = %s
        """, (actual, percent_d0, score, row_id, user_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 PREMIUM EDIT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/d0-premium/delete/<int:row_id>', methods=['DELETE'])
def d0_premium_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            DELETE FROM d0_premium_history
             WHERE id = %s AND user_id = %s
        """, (row_id, user_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'status': 'ok'})
    except Exception as e:
        print("D0 PREMIUM DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/re_do")
def re_do():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("calculators/re_do.html")

@app.route("/re_do/save", methods=["POST"])
def re_do_save():
    data = request.get_json()
    record_date = data.get("record_date")
    percentage  = float(data.get("percentage", 0))
    score       = float(data.get("score", 0))
    user_id     = session.get("user_id")

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql = """
                INSERT INTO RE_DO (user_id, record_date, percentage, score)
                VALUES (%s, %s, %s, %s)
            """
            cur.execute(sql, (user_id, record_date, percentage, score))
        conn.commit()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route("/re_do/history", methods=["GET"])
def re_do_history():
    if 'user_id' not in session:
        return jsonify([])

    user_id = session["user_id"]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
              SELECT id,
                     DATE_FORMAT(record_date, '%%Y-%%m-%%d') AS record_date,
                     percentage, score
              FROM RE_DO
              WHERE user_id = %s
              ORDER BY record_date DESC, id DESC
            """
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
        return jsonify(rows)
    finally:
        conn.close()

@app.route("/re_do/edit/<int:row_id>", methods=["PUT"])
def re_do_edit(row_id):
    data = request.get_json()
    record_date = data.get("record_date")
    percentage  = float(data.get("percentage", 0))
    score       = float(data.get("score", 0))
    user_id     = session.get("user_id")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            sql = """
              UPDATE RE_DO
              SET record_date=%s, percentage=%s, score=%s
              WHERE id=%s AND user_id=%s
            """
            cur.execute(sql, (record_date, percentage, score, row_id, user_id))
        conn.commit()
        return jsonify({"status": "ok"})
    finally:
        conn.close()

@app.route("/re_do/delete/<int:row_id>", methods=["DELETE"])
def re_do_delete(row_id):
    user_id = session.get("user_id")
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM RE_DO WHERE id=%s AND user_id=%s", (row_id, user_id))
        conn.commit()
        return jsonify({"status": "ok"})
    finally:
        conn.close()

@app.route('/iqc_skip')
def iqc_skip():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('calculators/iqc_skip.html')


# ---------- IQC SKIP APIs ----------

@app.route('/iqc-skip/save', methods=['POST'])
def iqc_skip_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id   = session['user_id']
        record_date = data.get('date')          # 'YYYY-MM-DD'
        percentage  = float(data.get('percentage', 0))
        score       = float(data.get('score', 0))

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO IQC_SKIP_HISTORY
                (user_id, record_date, percentage, score, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (user_id, record_date, percentage, score))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("IQC SKIP SAVE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/iqc-skip/history', methods=['GET'])
def iqc_skip_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT id,
                   record_date,
                   percentage,
                   score
            FROM IQC_SKIP_HISTORY
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'items': rows})
    except Exception as e:
        print("IQC SKIP HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/iqc-skip/edit/<int:row_id>', methods=['PUT'])
def iqc_skip_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id    = session['user_id']
        percentage = float(data.get('percentage', 0))
        score      = float(data.get('score', 0))

        # frontend se '' ya None aaye to ignore karo
        record_date = data.get('date')
        if record_date:
            record_date = record_date.strip()
        if not record_date:
            record_date = None

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            UPDATE IQC_SKIP_HISTORY
               SET percentage = %s,
                   score      = %s,
                   record_date = COALESCE(%s, record_date)
             WHERE id = %s AND user_id = %s
        """, (percentage, score, record_date, row_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("IQC SKIP EDIT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500



@app.route('/iqc-skip/delete/<int:row_id>', methods=['DELETE'])
def iqc_skip_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("""
            DELETE FROM IQC_SKIP_HISTORY
             WHERE id = %s AND user_id = %s
        """, (row_id, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("IQC SKIP DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route("/rnps")
def rnps():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("calculators/rnps.html", username=session.get('username'))


# ---------- R‑NPS APIs ----------

@app.route("/rnps/history", methods=["GET"])
def rnps_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql = """
                SELECT id,
                       DATE_FORMAT(record_date, '%%Y-%%m-%%d') AS record_date,
                       overall_percent, premium_percent,
                       overall_score, premium_score
                FROM R_NPS_HISTORY
                WHERE user_id = %s
                ORDER BY record_date DESC, id DESC
            """
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
        # rows yaha dicts ka list hoga (DictCursor)
        return jsonify({
            'status': 'ok',
            'items': rows
        })
    except Exception as e:
        print("R_NPS HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route("/rnps/history", methods=["POST"])
def rnps_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    user_id        = session['user_id']
    record_date    = data.get("date")
    overall_percent = float(data.get("overallPerc", 0))
    premium_percent = float(data.get("premiumPerc", 0))
    overall_score   = float(data.get("overallScore", 0))
    premium_score   = float(data.get("premiumScore", 0))

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql = """
                INSERT INTO R_NPS_HISTORY
                    (user_id, record_date,
                     overall_percent, premium_percent,
                     overall_score, premium_score)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cur.execute(sql, (
                user_id, record_date,
                overall_percent, premium_percent,
                overall_score, premium_score
            ))
        conn.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("R_NPS SAVE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route("/rnps/history/<int:row_id>", methods=["PUT"])
def rnps_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data    = request.get_json()
    user_id = session['user_id']

    record_date     = data.get("date")
    overall_percent = float(data.get("overallPerc", 0))
    premium_percent = float(data.get("premiumPerc", 0))
    overall_score   = float(data.get("overallScore", 0))
    premium_score   = float(data.get("premiumScore", 0))

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            sql = """
                UPDATE R_NPS_HISTORY
                   SET record_date     = %s,
                       overall_percent = %s,
                       premium_percent = %s,
                       overall_score   = %s,
                       premium_score   = %s
                 WHERE id = %s AND user_id = %s
            """
            cur.execute(sql, (
                record_date,
                overall_percent,
                premium_percent,
                overall_score,
                premium_score,
                row_id,
                user_id,
            ))
        conn.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("R_NPS EDIT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass


@app.route("/rnps/history/<int:row_id>", methods=["DELETE"])
def rnps_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    user_id = session['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM R_NPS_HISTORY WHERE id = %s AND user_id = %s",
                (row_id, user_id),
            )
        conn.commit()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("R_NPS DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        try:
            conn.close()
        except:
            pass

@app.route("/google_rating")
def google_rating():
    return render_template("calculators/google.html")

@app.route("/dealer_visit")
def dealer_visit():
    return render_template("calculators/dealer_visit.html")

@app.route("/negative")
def negative():
    return render_template("calculators/negative.html")

@app.route("/credit_block")
def credit_block():
    return render_template("calculators/credit_block.html")

from flask import request, jsonify, session, redirect, url_for, render_template
import pymysql


# ---------- ROUTE PAGE ----------

@app.route("/ofs")
def ofs():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("calculators/ofs.html", username=session.get('username'))

# ------------------------------------------
# SAVE (INSERT)
# ------------------------------------------
@app.route("/ofs/save_v2", methods=["POST"])
def ofs_save_v2():
    if 'user_id' not in session:
        return jsonify(status="error", message="Not logged in"), 401

    data = request.get_json()
    user_id = session['user_id']

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ofs_history_v2
                (user_id, calc_date, line_total, line_ordered, line_percent,
                 line_score, qty_total, qty_ordered, qty_percent, qty_score,
                 final_score, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id,
                data["date"],
                data["line_total"],
                data["line_ordered"],
                data["line_percent"],
                data["line_score"],
                data["qty_total"],
                data["qty_ordered"],
                data["qty_percent"],
                data["qty_score"],
                data["final_score"],
                data["status"]
            ))
        conn.commit()
        return jsonify(status="ok")

    except Exception as e:
        print("OFS SAVE ERROR:", e)
        return jsonify(status="error", message=str(e)), 500

    finally:
        conn.close()

# ------------------------------------------
# HISTORY (SELECT)
# ------------------------------------------
@app.route("/ofs/history_v2", methods=["GET"])
def ofs_history_v2():
    if 'user_id' not in session:
        return jsonify(status="error", message="Not logged in"), 401

    user_id = session['user_id']

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, calc_date, line_total, line_ordered, line_percent,
                       line_score, qty_total, qty_ordered, qty_percent, qty_score,
                       final_score, status
                FROM ofs_history_v2
                WHERE user_id = %s
                ORDER BY calc_date DESC, id DESC
            """, (user_id,))
            rows = cur.fetchall()

        return jsonify(status="ok", items=rows)

    except Exception as e:
        print("OFS HISTORY ERROR:", e)
        return jsonify(status="error", message=str(e)), 500

    finally:
        conn.close()

# ------------------------------------------
# EDIT (UPDATE)
# ------------------------------------------
@app.route("/ofs/edit_v2/<int:id>", methods=["PUT"])
def ofs_edit_v2(id):
    if 'user_id' not in session:
        return jsonify(status="error", message="Not logged in"), 401

    data = request.get_json()
    user_id = session['user_id']

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE ofs_history_v2
                SET calc_date=%s, line_total=%s, line_ordered=%s, line_percent=%s,
                    line_score=%s, qty_total=%s, qty_ordered=%s, qty_percent=%s,
                    qty_score=%s, final_score=%s, status=%s
                WHERE id=%s AND user_id=%s
            """, (
                data["date"],
                data["line_total"],
                data["line_ordered"],
                data["line_percent"],
                data["line_score"],
                data["qty_total"],
                data["qty_ordered"],
                data["qty_percent"],
                data["qty_score"],
                data["final_score"],
                data["status"],
                id,
                user_id
            ))

            if cur.rowcount == 0:
                return jsonify(status="error", message="Not found"), 404

        conn.commit()
        return jsonify(status="ok")

    except Exception as e:
        print("OFS EDIT ERROR:", e)
        return jsonify(status="error", message=str(e)), 500

    finally:
        conn.close()

# ------------------------------------------
# DELETE
# ------------------------------------------
@app.route("/ofs/delete/<int:id>", methods=["DELETE"])
def ofs_delete_v2(id):
    if 'user_id' not in session:
        return jsonify(status="error", message="Not logged in"), 401

    user_id = session['user_id']

    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                DELETE FROM ofs_history_v2
                WHERE id=%s AND user_id=%s
            """, (id, user_id))

            if cur.rowcount == 0:
                return jsonify(status="error", message="Not found"), 404

        conn.commit()
        return jsonify(status="ok")

    except Exception as e:
        print("OFS DELETE ERROR:", e)
        return jsonify(status="error", message=str(e)), 500

    finally:
        conn.close()

from datetime import datetime
import pymysql

@app.route('/sc-d1')
def sc_d1_page():
    if 'user_id' not in session:
        return redirect('/')
    return render_template("sc_d1.html")

@app.route('/sc-d1/save', methods=['POST'])
def sc_d1_save():
    if 'user_id' not in session:
        return jsonify({"status":"error","msg":"login required"}), 401

    data = request.get_json()
    service_no = data.get("service_no")
    reg_date   = data.get("reg_date")

    if not service_no or not reg_date:
        return jsonify({"status":"error","msg":"missing fields"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sc_d1_history(user_id, service_no, reg_date, close_date, within_2)
        VALUES(%s,%s,%s,NULL,0)
    """, (session['user_id'], service_no, reg_date))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status":"ok"})

@app.route('/sc-d1/close/<int:row_id>', methods=['PUT'])
def sc_d1_close(row_id):
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401

    data = request.get_json()
    close_date = data.get("close_date")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT reg_date FROM sc_d1_history WHERE id=%s AND user_id=%s",
                (row_id, session['user_id']))
    row = cur.fetchone()

    if not row:
        return jsonify({"status":"error","msg":"not found"})

    reg = datetime.strptime(str(row['reg_date']), "%Y-%m-%d")
    clo = datetime.strptime(close_date, "%Y-%m-%d")
    diff = (clo - reg).days
    within = 1 if diff <= 2 else 0

    cur.execute("""
        UPDATE sc_d1_history
        SET close_date=%s, within_2=%s
        WHERE id=%s AND user_id=%s
    """, (close_date, within, row_id, session['user_id']))

    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status":"ok"})

@app.route('/sc-d1/delete/<int:row_id>', methods=['DELETE'])
def sc_d1_delete(row_id):
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM sc_d1_history WHERE id=%s AND user_id=%s",
                (row_id, session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"status":"ok"})
    
@app.route('/sc-d1/history')
def sc_d1_history():
    if 'user_id' not in session:
        return jsonify({"status":"error"}), 401

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, service_no, reg_date, close_date, within_2
        FROM sc_d1_history
        WHERE user_id=%s
        ORDER BY id DESC
    """, (session['user_id'],))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify({"status":"ok","items":rows})

@app.route('/sc-d1/edit/<int:row_id>', methods=['PUT'])
def sc_d1_edit(row_id):
    if 'user_id' not in session:
        return jsonify({"status": "error", "msg": "login required"}), 401

    data = request.get_json()

    reg_date   = data.get("reg_date")
    close_date = data.get("close_date")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE sc_d1_history
        SET reg_date = COALESCE(%s, reg_date),
            close_date = COALESCE(%s, close_date)
        WHERE id=%s AND user_id=%s
    """, (reg_date, close_date, row_id, session['user_id']))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status":"ok"})

@app.route('/ub-repair')
def ub_repair():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('calculators/ub_repair.html')


# ---------- UB REPAIR APIs ----------

@app.route('/ub-repair/save', methods=['POST'])
def ub_repair_save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id   = session['user_id']
        source    = data.get('source', 'unknown')
        ub_cons   = float(data.get('ubConsume', 0))
        total_lcd = float(data.get('totalLCD', 0))
        direct_p  = float(data.get('directPercent', 0))
        pct       = float(data.get('percentage', 0))
        score     = float(data.get('score', 0))
        date_str  = data.get('date')  # 'YYYY-MM-DD'

        # date string -> datetime
        if date_str:
            created_at = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            created_at = datetime.now()

        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            INSERT INTO ub_repair_history
                (user_id, created_at, source, ub_consume, total_lcd,
                 direct_percent, percentage, score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, created_at, source, ub_cons, total_lcd,
             direct_p, pct, score),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("UB REPAIR SAVE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ub-repair/history', methods=['GET'])
def ub_repair_history():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute(
            """
            SELECT
                id,
                created_at,
                source,
                ub_consume,
                total_lcd,
                direct_percent,
                percentage,
                score
            FROM ub_repair_history
            WHERE user_id = %s
            ORDER BY created_at DESC, id DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # yahan clean date string bana do
        items = []
        for r in rows:
            created = r['created_at']
            if isinstance(created, (datetime, )):
                date_str = created.strftime("%Y-%m-%d")
            else:
                # safety fallback
                date_str = str(created)[:10]

            items.append({
                'id': r['id'],
                'record_date': date_str,  # sirf YYYY-MM-DD
                'source': r['source'],
                'ub_consume': r['ub_consume'],
                'total_lcd': r['total_lcd'],
                'direct_percent': r['direct_percent'],
                'percentage': r['percentage'],
                'score': r['score'],
            })

        return jsonify({'status': 'ok', 'items': items})
    except Exception as e:
        print("UB REPAIR HISTORY ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ub-repair/edit/<int:row_id>', methods=['PUT'])
def ub_repair_edit(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    data = request.get_json()
    try:
        user_id = session['user_id']

        # ✅ Match frontend keys EXACTLY
        payload = {
            'source': data.get('source'),
            'ub_consume': float(data.get('ubConsume', 0)),
            'total_lcd': float(data.get('totalLCD', 0)),
            'direct_percent': float(data.get('directPercent', 0)),
            'percentage': float(data.get('percentage', 0)),
            'score': float(data.get('score', 0))
        }

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ub_repair_history
               SET source = %s,
                   ub_consume = %s,
                   total_lcd = %s,
                   direct_percent = %s,
                   percentage = %s,
                   score = %s
             WHERE id = %s AND user_id = %s
        """, (
            payload['source'],
            payload['ub_consume'],
            payload['total_lcd'],
            payload['direct_percent'],
            payload['percentage'],
            payload['score'],
            row_id,
            user_id
        ))
        
        # Check if update affected any rows
        if cur.rowcount == 0:
            return jsonify({'status': 'error', 'message': 'No record found'}), 404
            
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("UB REPAIR EDIT ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/ub-repair/delete/<int:row_id>', methods=['DELETE'])
def ub_repair_delete(row_id):
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not logged in'}), 401

    try:
        user_id = session['user_id']
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            """
            DELETE FROM ub_repair_history
            WHERE id = %s AND user_id = %s
            """,
            (row_id, user_id),
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'})
    except Exception as e:
        print("UB REPAIR DELETE ERROR:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route to handle parameter selection from home page
@app.route('/select', methods=['POST'])
def select_parameter():
    parameter = request.form.get('parameter', '')
    print(f"Parameter selected: {parameter}")
    
    # Map parameter names to routes
    param_map = {
        'performance scoring dashboard': '/index.html',
        'ltp': '/LTP.html',
        'd+0 (overall)': '/D+0 (Overall).html',
        'd+0 (premium)': '/D+0 (Premium).html',  # Assuming you have this
        're-do': '/RE-DO.html',
        'iqc skip%': '/IQC SKIP%.html',  # If you have this file
        'r-nps': '/R-NPS.html',
        'google rating': '/google.html',
        'dealer visit': '/Dealer.html',
        'ub repair': '/UB.html',
        'credit block cases': '/Credit Block Cases.html',  # If you have this
        'ofs': '/OFS.html',  # If you have this
        'negative sentiments (google)': '/negative.html'
    }
    
    route = param_map.get(parameter.lower())
    if route:
        return redirect(url_for('catch_all', filename=route.replace('/templates/', '')))
    else:
        return redirect('/home.html')

# API routes for your PHP files
@app.route('/insert', methods=['POST'])
def insert_data():
    """Route to call your PHP insert.php"""
    data = request.form
    print("Data to insert:", data)
    # Call your PHP insert.php (integration code)
    return jsonify({
        'status': 'success',
        'message': 'Data sent to PHP insert.php',
        'data': dict(data)
    })

@app.route('/fetch')
def fetch_data():
    """Route to call your PHP fetch.php"""
    parameter = request.args.get('parameter', '')
    print("Fetching data for:", parameter)
    # Call your PHP fetch.php (integration code)
    return jsonify({
        'parameter': parameter,
        'status': 'success',
        'data': []  # Replace with actual PHP call
    })



if __name__ == "__main__":
    print("FLASK STARTING...")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)