import requests

BASE = 'http://127.0.0.1:8000/api/hr'

def get(path):
    try:
        r = requests.get(BASE + path)
        print(path, r.status_code)
        try:
            print(r.json())
        except Exception:
            print(r.text[:1000])
    except Exception as e:
        print('ERR', e)

if __name__ == '__main__':
    get('/')
    get('/attendance/today_status/')
    get('/attendance/my_summary/?month=1&year=2026')
    get('/attendance/my_records/?month=1&year=2026')
    get('/attendance/punch_in/')
