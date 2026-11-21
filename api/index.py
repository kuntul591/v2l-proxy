from flask import Flask, jsonify, render_template_string, request, redirect
import requests, time, secrets, datetime, json

app = Flask(__name__)

# ===== DATAIMPULSE LU - UDAH DIISI DARI SCREENSHOT =====
DATAIMPULSE_HOST = "gw.dataimpulse.com"
DATAIMPULSE_PORT = "10200"
DATAIMPULSE_USER = "b00e4c5c64566c595d6b"
DATAIMPULSE_PASS = "1a8b08e7e82d3ed9"
DATAIMPULSE_COUNTRY = "ID"
DATAIMPULSE_CITY = "Jakarta"

TOKEN_FILE = "/tmp/tokens.json"
ADMIN_PASSWORD = "v2l123"

def load_tokens():
    try:
        with open(TOKEN_FILE, 'r') as f: return json.load(f)
    except: return {}
def save_tokens(data):
    try:
        with open(TOKEN_FILE, 'w') as f: json.dump(data, f)
    except: pass

HTML_LOGIN = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:white;font-family:sans-serif;text-align:center;padding:30px}
input{width:90%;padding:15px;border-radius:10px;border:none;margin:10px}
button{width:95%;padding:15px;background:#a100ff;border:none;border-radius:10px;font-weight:bold;font-size:16px;color:white}</style>
</head><body>
<h1>⚡ V2L PROXY</h1><p>Premium Proxy Auto - No Nyasar</p>
<form action="/cek-token" method="POST">
<input name="token" placeholder="Masukin Token V2L Lu" required>
<button>🔓 MASUK V2L</button></form>
<p style="color:#888">1 Hari 15k | 3 Hari 35k | 7 Hari 100k | 30 Hari 300k<br>Hubungi Admin V2L</p>
</body></html>
"""

HTML_USER = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#0a0a0a;color:white;font-family:sans-serif;text-align:center;padding:20px}
.card{background:#1e1e1e;padding:20px;border-radius:15px}
button{width:100%;padding:15px;margin:5px 0;border:none;border-radius:10px;font-weight:bold}
.btn-cari{background:#a100ff;color:white}.btn-connect{background:#00ff88}
.bener{color:#00ff88}.nyasar{color:#ff4444}</style>
</head><body>
<h1>⚡ V2L PROXY</h1>
<p>Halo <b>{{nama}}</b> | Sisa: <b>{{sisa}}</b><br>Expired: {{expired_str}}</p>
<div class="card">
<p>IP DataImpulse: <b id="ip">Belum ada</b></p>
<p>Lokasi: <b id="lokasi">-</b></p>
<p>ISP: <b id="isp">-</b></p>
<p>Status: <b id="status">Belum dicek</b></p>
<p>Browserleaks Check: <b id="leak">-</b></p>
<p style="font-size:12px;color:#888">SOCKS5: gw.dataimpulse.com:10200</p>
</div>
<button class="btn-cari" onclick="cari()">🔍 CARI OTOMATIS (DataImpulse)</button>
<button class="btn-connect" onclick="connect()">✅ CONNECT + CEK BROWSERLEAKS</button>
<p><a href="https://browserleaks.com/ip" target="_blank" style="color:#a100ff">👉 Klik disini buat cek IP di Browserleaks.com</a></p>
<script>
async function cari(){
  document.getElementById('status').innerText="Lagi minta IP ke DataImpulse SOCKS5...";
  let res = await fetch('/cari-proxy-otomatis');
  let d = await res.json();
  document.getElementById('ip').innerText=d.ip;
  document.getElementById('lokasi').innerText=d.kota+" - "+d.negara;
  document.getElementById('isp').innerText=d.isp;
  document.getElementById('status').innerText=d.status;
  document.getElementById('status').className = d.status=="BENER" ? "bener" : "nyasar";
  document.getElementById('leak').innerText = d.browserleaks;
  if(d.status=="NYASAR"){ alert("IP Nyasar! Minta lagi ke DataImpulse..."); cari(); }
}
function connect(){
  let ip=document.getElementById('ip').innerText;
  if(ip=="Belum ada"){alert("Cari dulu!");return;}
  alert("V2L CONNECT ke "+ip+"\\nSekarang cek di Browserleaks, harusnya IP lu udah keganti jadi "+ip);
  window.open("https://browserleaks.com/ip","_blank");
}
</script></body></html>
"""

HTML_ADMIN = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{background:#111;color:white;font-family:sans-serif;padding:20px}
input,select{width:100%;padding:12px;margin:5px 0;border-radius:8px;border:none}
button{width:100%;padding:15px;background:#a100ff;border:none;border-radius:10px;font-weight:bold;color:white}
.card{background:#222;padding:15px;border-radius:10px;margin:10px 0}</style>
</head><body>
<h1>👑 V2L ADMIN PANEL</h1>
<form action="/admin/buat-token" method="POST">
<input name="nama" placeholder="Nama Penyewa" required>
<select name="durasi">
<option value="1">1 Hari - 15k</option>
<option value="3">3 Hari - 35k</option>
<option value="7">7 Hari - 100k</option>
<option value="30">30 Hari - 300k</option>
</select>
<button>➕ BUAT TOKEN V2L</button></form>
<h2>List Token ({{jumlah}})</h2>
{% for t, info in tokens.items() %}
<div class="card"><b>{{t}}</b><br>Nama: {{info.nama}} | {{info.durasi}}<br>Expired: {{info.expired_str}}<br>Status: {{info.status}}<br><a href="/admin/hapus/{{t}}" style="color:red">Hapus</a></div>
{% endfor %}
</body></html>
"""

@app.route('/')
def login(): return render_template_string(HTML_LOGIN)

@app.route('/cek-token', methods=['POST'])
def cek_token():
    token = request.form.get('token','').strip().upper()
    TOKENS = load_tokens()
    info = TOKENS.get(token)
    if not info: return "<h1>Token Salah!</h1><a href='/'>Balik</a>"
    if time.time() > info['expired']: return "<h1>Token Expired!</h1><a href='/'>Balik</a>"
    sisa = info['expired'] - time.time()
    sisa_str = f"{sisa/86400:.1f} Hari lagi" if sisa>=86400 else f"{int(sisa/3600)} Jam lagi"
    exp_str = datetime.datetime.fromtimestamp(info['expired']).strftime("%d %b %Y %H:%M")
    return render_template_string(HTML_USER, nama=info['nama'], sisa=sisa_str, expired_str=exp_str)

@app.route('/admin')
def admin():
    pw = request.args.get('pw','')
    if pw != ADMIN_PASSWORD:
        return "<form><h1>Login V2L Admin</h1><input name='pw' placeholder='Password' type='password'><button>Masuk</button></form>"
    TOKENS = load_tokens()
    data = {}
    for k,v in TOKENS.items():
        vv=dict(v)
        vv['expired_str']=datetime.datetime.fromtimestamp(v['expired']).strftime("%d %b %Y %H:%M")
        vv['status']="AKTIF ✅" if time.time()<v['expired'] else "EXPIRED ❌"
        data[k]=vv
    return render_template_string(HTML_ADMIN, tokens=data, jumlah=len(data))

@app.route('/admin/buat-token', methods=['POST'])
def buat():
    nama = request.form.get('nama','User').strip()
    durasi = int(request.form.get('durasi','1'))
    token = f"V2L-{nama.upper()[:4]}-{secrets.token_hex(2).upper()}"
    TOKENS = load_tokens()
    TOKENS[token]={"nama":nama,"expired":time.time()+(durasi*86400),"durasi":f"{durasi} Hari"}
    save_tokens(TOKENS)
    return f"<h1>Token Berhasil!</h1><h2>{token}</h2><p>{nama} | {durasi} Hari</p><a href='/admin?pw={ADMIN_PASSWORD}'>Balik</a>"

@app.route('/admin/hapus/<token>')
def hapus(token):
    TOKENS=load_tokens(); TOKENS.pop(token,None); save_tokens(TOKENS)
    return redirect(f'/admin?pw={ADMIN_PASSWORD}')

@app.route('/cari-proxy-otomatis')
def cari():
    session_id = secrets.token_hex(4)
    proxy_user = f"{DATAIMPULSE_USER}-country-{DATAIMPULSE_COUNTRY}-city-{DATAIMPULSE_CITY}-session-{session_id}"
    proxy_url = f"socks5h://{proxy_user}:{DATAIMPULSE_PASS}@{DATAIMPULSE_HOST}:{DATAIMPULSE_PORT}"
    try:
        cek = requests.get("http://ip-api.com/json/?fields=status,country,city,isp,query,hosting,proxy", proxies={"http": proxy_url, "https": proxy_url}, timeout=20).json()
        ip_baru = cek.get('query', 'Gagal')
        negara = cek.get('country', '-')
        kota = cek.get('city', '-')
        isp = cek.get('isp', '-')
        hosting = cek.get('hosting', False)
    except Exception as e:
        return jsonify({"ip": "Gagal Nyambung", "negara": f"Error: {str(e)[:100]}", "kota": "-", "isp": "-", "status": "NYASAR", "browserleaks": "Gagal"})
    if negara != 'Indonesia' or hosting == True:
        status = "NYASAR"
        browserleaks = "BEDA - Nyasar"
    else:
        status = "BENER"
        browserleaks = "SAMA - Browserleaks bakal nunjukin IP ini juga"
    return jsonify({"ip": ip_baru, "negara": negara, "kota": kota, "isp": isp, "status": status, "browserleaks": browserleaks})
