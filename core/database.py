"""SQLite persistence: salted password hashes, optimistic writes, and version history."""
from __future__ import annotations
import sqlite3, json, hashlib, hmac, secrets, os, pathlib, datetime
from core.engine import default_design
BASE=pathlib.Path(__file__).resolve().parent.parent
DATA=BASE/'data'; DB=DATA/'eco_concert.db'

def now(): return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
def connect():
    DATA.mkdir(exist_ok=True,parents=True)
    conn=sqlite3.connect(DB,timeout=10)
    conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=10000')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn

def hash_password(pwd,salt=None):
    salt=salt or secrets.token_hex(16)
    return salt+'$'+hashlib.pbkdf2_hmac('sha256',pwd.encode(),bytes.fromhex(salt),220000).hex()
def verify(pwd,encoded):
    try: salt,_=encoded.split('$',1);return hmac.compare_digest(hash_password(pwd,salt),encoded)
    except Exception:return False

def initialize():
    with connect() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY,login TEXT UNIQUE NOT NULL,display TEXT NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS designs (team_id INTEGER PRIMARY KEY REFERENCES users(id),revision INTEGER NOT NULL DEFAULT 1,body TEXT NOT NULL,updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS design_versions (id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES users(id),revision INTEGER NOT NULL,body TEXT NOT NULL,created_at TEXT NOT NULL,UNIQUE(team_id,revision));
        CREATE TABLE IF NOT EXISTS chat_messages (id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES users(id),role TEXT NOT NULL,text TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS team_documents (team_id INTEGER PRIMARY KEY REFERENCES users(id), body TEXT NOT NULL DEFAULT '', revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ai_reviews (id INTEGER PRIMARY KEY,team_id INTEGER NOT NULL REFERENCES users(id),revision INTEGER NOT NULL,feedback TEXT NOT NULL,decision TEXT NOT NULL DEFAULT '미결정',reason TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL);
        ''')
        if c.execute('SELECT COUNT(*) n FROM users').fetchone()['n']==0:
            creds={}
            teacher_pwd='999999'
            creds['teacher']=teacher_pwd
            c.execute('INSERT INTO users(login,display,password_hash,role) VALUES(?,?,?,?)',('teacher','교사용 계정',hash_password(teacher_pwd),'teacher'))
            for n in range(1,7):
                login=f'team{n}';pwd=str(n)*6
                creds[login]=pwd
                c.execute('INSERT INTO users(login,display,password_hash,role) VALUES(?,?,?,?)',(login,f'{n}모둠',hash_password(pwd),'team'))
                uid=c.execute('SELECT id FROM users WHERE login=?',(login,)).fetchone()['id']
                body=json.dumps(default_design(),ensure_ascii=False)
                c.execute('INSERT INTO designs(team_id,revision,body,updated_at) VALUES(?,?,?,?)',(uid,1,body,now()))
                c.execute('INSERT INTO design_versions(team_id,revision,body,created_at) VALUES(?,?,?,?)',(uid,1,body,now()))
            credential_path=DATA/'initial_credentials.txt'
            with open(credential_path,'x',encoding='utf-8') as f:
                f.write('최초 생성된 계정 (학교 외부 공유 금지)\n')
                for k,v in creds.items():f.write(f'{k}: {v}\n')
            try:os.chmod(credential_path,0o600)
            except OSError:pass

def authenticate(login,password):
    with connect() as c:
        r=c.execute('SELECT * FROM users WHERE login=?',(login,)).fetchone()
        if r and verify(password,r['password_hash']):
            return {'id':r['id'],'login':r['login'],'display':r['display'],'role':r['role']}
        return None

def get_design(team_id):
    with connect() as c:
        r=c.execute('SELECT revision,body,updated_at FROM designs WHERE team_id=?',(team_id,)).fetchone()
        return (json.loads(r['body']),r['revision'],r['updated_at']) if r else (None,None,None)

def save_design(team_id,d,expected_revision):
    body=json.dumps(d,ensure_ascii=False)
    with connect() as c:
        updated=c.execute('UPDATE designs SET body=?,revision=revision+1,updated_at=? WHERE team_id=? AND revision=?',(body,now(),team_id,expected_revision))
        if updated.rowcount==0: return None
        revision=expected_revision+1
        c.execute('INSERT INTO design_versions(team_id,revision,body,created_at) VALUES(?,?,?,?)',(team_id,revision,body,now()))
        return revision

def versions(team_id):
    with connect() as c:return [dict(r) for r in c.execute('SELECT revision,created_at FROM design_versions WHERE team_id=? ORDER BY revision DESC LIMIT 30',(team_id,))]
def version_design(team_id,rev):
    with connect() as c:
        r=c.execute('SELECT body FROM design_versions WHERE team_id=? AND revision=?',(team_id,rev)).fetchone()
        return json.loads(r['body']) if r else None

def add_chat(team_id,role,text):
    with connect() as c:c.execute('INSERT INTO chat_messages(team_id,role,text,created_at) VALUES(?,?,?,?)',(team_id,role,text[:6000],now()))
def chats(team_id,limit=40):
    with connect() as c:
        rows=c.execute('SELECT id,role,text,created_at FROM chat_messages WHERE team_id=? ORDER BY id DESC LIMIT ?',(team_id,limit)).fetchall()
        return list(reversed([dict(r) for r in rows]))
def add_review(team_id,rev,text):
    with connect() as c:
        cur=c.execute('INSERT INTO ai_reviews(team_id,revision,feedback,created_at) VALUES(?,?,?,?)',(team_id,rev,text[:8000],now()))
        return cur.lastrowid
def reviews(team_id):
    with connect() as c:return [dict(r) for r in c.execute('SELECT * FROM ai_reviews WHERE team_id=? ORDER BY id DESC LIMIT 20',(team_id,))]
def decision(review_id,team_id,value,reason):
    with connect() as c:c.execute('UPDATE ai_reviews SET decision=?,reason=? WHERE id=? AND team_id=?',(value,reason[:1000],review_id,team_id))
def teams():
    with connect() as c:
        return [dict(r) for r in c.execute('SELECT u.id,u.login,u.display,d.revision,d.updated_at FROM users u LEFT JOIN designs d ON u.id=d.team_id WHERE u.role="team" ORDER BY u.id')]
def change_password(user_id,old,new):
    if len(new)<8: return False
    with connect() as c:
        r=c.execute('SELECT password_hash FROM users WHERE id=?',(user_id,)).fetchone()
        if not r or not verify(old,r['password_hash']):return False
        c.execute('UPDATE users SET password_hash=? WHERE id=?',(hash_password(new),user_id))
        return True


def delete_chat(team_id, message_id):
    """Delete only one message owned by this team."""
    with connect() as c:
        return c.execute('DELETE FROM chat_messages WHERE id=? AND team_id=?',(message_id,team_id)).rowcount > 0

def clear_chats(team_id):
    """Delete a team's conversation history, not design/review records."""
    with connect() as c:
        return c.execute('DELETE FROM chat_messages WHERE team_id=?',(team_id,)).rowcount


def get_team_document(team_id):
    """Shared editable design rationale for members of the same team."""
    with connect() as c:
        r=c.execute('SELECT body,revision,updated_at FROM team_documents WHERE team_id=?',(team_id,)).fetchone()
        if not r:
            c.execute('INSERT OR IGNORE INTO team_documents(team_id,body,revision,updated_at) VALUES(?,?,?,?)',(team_id,'',1,now()))
            r=c.execute('SELECT body,revision,updated_at FROM team_documents WHERE team_id=?',(team_id,)).fetchone()
        return dict(r)

def save_team_document(team_id,body,revision):
    with connect() as c:
        cur=c.execute('UPDATE team_documents SET body=?,revision=revision+1,updated_at=? WHERE team_id=? AND revision=?',(body[:12000],now(),team_id,revision))
        return cur.rowcount==1
