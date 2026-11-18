"""Run with: python test_core.py (no Streamlit/Ollama required)."""
import tempfile, pathlib
from core import engine
from core import database as db

def test():
    d=engine.default_design()
    s=engine.simulate(d)
    assert s['before']['total'] > s['after']['total']
    assert s['reduction_pct'] > 0
    assert engine.plan_bytes(d).startswith(b'\x89PNG')
    assert any(i['level']=='안내' for i in s['issues'])
    with tempfile.TemporaryDirectory() as temp:
        db.DATA=pathlib.Path(temp);db.DB=db.DATA/'eco_concert.db'
        db.initialize()
        assert len(db.teams()) == 6
        txt=(db.DATA/'initial_credentials.txt').read_text(encoding='utf8')
        assert 'teacher:' in txt and 'team6:' in txt
        username,password=txt.split('team1: ')[1].splitlines()[0],None
        # parse first team password
        pwd=txt.split('team1: ')[1].splitlines()[0]
        user=db.authenticate('team1',pwd)
        assert user and user['role']=='team'
        loaded,rev,_=db.get_design(user['id'])
        assert rev==1
        new=db.save_design(user['id'],loaded,1)
        assert new==2
        assert db.save_design(user['id'],loaded,1) is None
        db.add_chat(user['id'],'user','안녕하세요')
        mid=db.chats(user['id'])[0]['id']
        assert db.chats(user['id'])[0]['text']=='안녕하세요'
        assert db.delete_chat(user['id'],mid)
        assert not db.chats(user['id'])
        db.add_chat(user['id'],'user','다시 질문')
        assert db.clear_chats(user['id']) == 1
        rid=db.add_review(user['id'],2,'추가 검증이 필요합니다.')
        db.decision(rid,user['id'],'추가 검증','통로 조도를 실제로 측정')
        assert db.reviews(user['id'])[0]['decision']=='추가 검증'
    print('OK: engine, PNG, DB initialization/authentication/revisions/chat deletion/reviews')

if __name__=='__main__':test()
