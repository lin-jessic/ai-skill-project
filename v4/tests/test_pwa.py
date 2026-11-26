"""PWA shell and backend integration. Run: python -m pytest -q"""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app_pwa import app, DEFAULT_CONFIG

client=TestClient(app)

def test_web_shell_and_icons():
    for p in ('/','/manifest.webmanifest','/sw.js','/assets/app.js','/assets/styles.css',
              '/assets/icons/icon-192.png','/assets/icons/icon-512.png'):
        r=client.get(p)
        assert r.status_code==200, (p,r.text)
    manifest=client.get('/manifest.webmanifest').json()
    assert manifest['display']=='standalone'
    assert {x['sizes'] for x in manifest['icons']}=={'192x192','512x512'}
    html=client.get('/').text
    assert 'apple-mobile-web-app-capable' in html
    assert 'viewport-fit=cover' in html
    assert 'href="/manifest.webmanifest"' in html

def test_service_worker_does_not_cache_sensitive_api():
    sw=client.get('/sw.js').text
    assert "url.pathname.startsWith('/api/')" in sw
    assert "req.method !== 'GET'" in sw
    assert 'skipWaiting' in sw

def test_catalog_stores_and_modules():
    response=client.get('/api/catalog')
    assert response.status_code==200
    assert len(response.json()['shops'])==20
    assert len(response.json()['decisions'])>=4
    assert len(response.json()['required_columns'])==5

def test_uploaded_csv_three_agent_end_to_end():
    data=(Path(__file__).resolve().parents[1]/'examples'/'DEMO_商圈資料_情境假設_非官方.csv').read_bytes()
    resp=client.post('/api/analyze',files={'file':('test.csv',data,'text/csv')},
                     data={'config':json.dumps(DEFAULT_CONFIG,ensure_ascii=False)})
    assert resp.status_code==200,resp.text
    body=resp.json()
    assert body['market']['agent']=='01_market_analyst'
    assert body['legal']['agent']=='02_legal_advisor'
    assert body['plan'].startswith('# 03')
    assert body['audit']['financial_formula_check']
    assert len(body['ranked'])==5
    assert '教學情境假設' in body['ranked'][0]['data_source']

def test_bad_config_fails_validation():
    invalid={**DEFAULT_CONFIG,'dinein_share':.8,'delivery_share':.7}
    r=client.post('/api/preview',json={'config':invalid})
    assert r.status_code==422
    invalid={**DEFAULT_CONFIG,'price':float('nan')}
    # JSON nonfinite is invalid; send literal valid string instead
    invalid['price']='nan'
    assert client.post('/api/preview',json={'config':invalid}).status_code==422

def test_day_simulation_is_repeatable_and_labeled():
    req={'config':DEFAULT_CONFIG,'history':[],'choice':'社群廣告','seed':42}
    a=client.post('/api/day',json=req)
    assert a.status_code==200
    b=client.post('/api/day',json=req)
    assert a.json()==b.json()
    assert a.json()['last']['is_simulation'] is True
    assert client.post('/api/day',json={'config':DEFAULT_CONFIG,'choice':'bad'}).status_code==422

def test_reject_unknown_file_extension_and_missing_columns():
    bad=client.post('/api/analyze',files={'file':('bad.txt',b'not csv')},data={'config':json.dumps(DEFAULT_CONFIG)})
    assert bad.status_code==422
    bad=client.post('/api/analyze',files={'file':('bad.csv',b'x,y\n1,2')},data={'config':json.dumps(DEFAULT_CONFIG)})
    assert bad.status_code==422
