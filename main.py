from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from jinja2 import Template
import uuid

# 儲存名片資料（注意：伺服器重啟就會消失）
card_storage = {}


app = FastAPI(title="Internal Card Generator")

# ---------------------------- HTML Templates ---------------------------- #
# 插入表單頁面（含動態新增社群 JS，提交到 /generate，於新分頁開啟結果）
FORM_HTML = Template(
    r"""<!DOCTYPE html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>公司內部名片產生器</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
    <style>
      :root { --brand-primary:#1abc9c; --gray-100:#f3f4f6; --gray-300:#d1d5db; --gray-600:#4b5563; }
      *{box-sizing:border-box;} body{margin:0 auto;max-width:720px;padding:2rem 1rem 4rem;font-family:'Inter',sans-serif;line-height:1.6;}
      h1{color:var(--brand-primary);font-size:1.9rem;margin-bottom:1.2rem;} label{display:block;margin-top:1rem;font-weight:600;}
      input{margin-top:.35rem;width:100%;padding:.55rem .7rem;border:1px solid var(--gray-300);border-radius:6px;font-size:1rem;}
      .two-cols{display:flex;gap:.75rem;} .two-cols input{flex:1 1 0;}
      .social-row{margin-top:.75rem;display:flex;gap:.5rem;align-items:center;} .social-row input{flex:1 1 0;}
      .social-row button{border:none;background:none;color:var(--gray-600);font-size:1.2rem;cursor:pointer;}
      #addSocial{margin-top:1rem;padding:.45rem 1rem;font-size:.95rem;border:1px dashed var(--brand-primary);border-radius:6px;background:var(--gray-100);cursor:pointer;color:var(--brand-primary);} 
      button[type='submit']{margin-top:2rem;padding:.7rem 1.6rem;font-size:1.05rem;border:none;border-radius:8px;background:var(--brand-primary);color:#fff;cursor:pointer;}
      footer{margin-top:3rem;font-size:.875rem;color:var(--gray-600);text-align:center;}
    </style>
  </head>
  <body>
    <h1>名片產生器</h1>
    <form id="cardForm" action="/generate" method="post" target="_blank">
      <label>姓名 (NAME) <input name="NAME" placeholder="王小明" required></label>
      <label>職稱 (TITLE) <input name="TITLE" placeholder="Software Engineer" required></label>
      <label>電子信箱 (EMAIL) <input name="EMAIL" type="email" placeholder="you@example.com" required></label>
      <div class="two-cols">
        <label style="flex:1">電話 (PHONE) <input name="PHONE" value="(02)2732-2701"></label>
        <label style="flex:1">官方/個人網站 (WEBSITE) <input name="WEBSITE" value="cancerfree.io"></label>
      </div>

      <h2 style="margin-top:2.2rem;font-size:1.15rem;color:var(--gray-600)">社群連結 (可選)</h2>
      <p style="font-size:0.9rem;margin:0.2rem 0 0.6rem;color:var(--gray-600)">點「新增」可加入多筆。</p>

      <div id="socialContainer"></div>
      <button id="addSocial" type="button">+ 新增社群連結</button>

      <button type="submit">產生名片</button>
    </form>

    <footer>產生後的新分頁可直接 Ctrl/Cmd + S 另存，內網環境即可離線存取。</footer>

    <script>
      // 動態新增/移除社群欄位
      const container = document.getElementById('socialContainer');
      const addBtn = document.getElementById('addSocial');
      function createSocialRow(name='', url=''){
        const row = document.createElement('div');
        row.className='social-row';
        row.innerHTML=`<input name="social_name" placeholder="平台 (LinkedIn)" value="${name}">\n<input name="social_url" placeholder="https://..." value="${url}">\n<button type="button" title="刪除">✕</button>`;
        row.querySelector('button').addEventListener('click',()=>row.remove());
        return row;
      }
      addBtn.addEventListener('click',()=>container.appendChild(createSocialRow()));
      container.appendChild(createSocialRow());
    </script>
  </body>
</html>"""
)

# 名片頁面模板 (Jinja2)
CARD_TEMPLATE = Template(
    r"""<!DOCTYPE html>
<html lang="zh-Hant">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="color-scheme" content="light dark" />
    <title>{{ NAME }}的名片</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet" />
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.7.0/vanilla-tilt.min.js" defer></script>
    <style>
      /* ---- 原始題目 style，為節省篇幅請按需補全 ---- */
      :root {
        --brand-primary:#1abc9c;--brand-secondary:#2ecc71;--brand-dark:#0e3d37;--brand-light:#e6fffb;--accent-light:#a8ffd9;--card-max-width:380px;
        --page-bg-light: radial-gradient(circle at 50% 120%, var(--brand-light) 0%, #0c9982 70%);
        --page-bg-dark: radial-gradient(circle at 50% 120%, #052620 0%, #022e27 70%);
      }
      *,*::before,*::after{box-sizing:border-box;margin:0;padding:0;} html,body{height:100%;display:flex;justify-content:center;align-items:center;background:var(--page-bg-light);font-family:'Inter',sans-serif;-webkit-font-smoothing:antialiased;transition:background .6s ease;} @media (prefers-color-scheme:dark){html,body{background:var(--page-bg-dark);}}
      .card-wrapper{perspective:1200px;width:min(90vw,var(--card-max-width));aspect-ratio:16/10;cursor:pointer;}
      .card-inner{position:relative;width:100%;height:100%;transform-style:preserve-3d;transition:transform .8s cubic-bezier(.4,.2,.2,1);} .card-wrapper.is-flipped .card-inner{transform:rotateY(180deg);} .card-face{position:absolute;inset:0;border-radius:20px;overflow:hidden;backface-visibility:hidden;display:flex;flex-direction:column;justify-content:center;padding:clamp(20px,6vw,32px);color:#f8fffe;text-shadow:0 1px 2px rgba(0,0,0,.55);} .card-face::before{content:'';position:absolute;inset:-2px;z-index:-1;background:linear-gradient(60deg,var(--brand-primary),var(--brand-secondary));border-radius:22px;filter:blur(6px);animation:gradientShift 6s ease-in-out infinite;background-size:200% 200%;} @keyframes gradientShift{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}} .front{backdrop-filter:blur(12px) saturate(150%);background:rgba(14,61,55,.55);} .back{backdrop-filter:blur(14px) saturate(160%);background:rgba(14,61,55,.55);transform:rotateY(180deg);} .name{font-size:clamp(1.3rem,5vw,1.8rem);font-weight:800;letter-spacing:.5px;position:relative;isolation:isolate;} .name::after{content:'';position:absolute;inset:0;left:-100%;background:linear-gradient(120deg,transparent 0%,rgba(255,255,255,.6) 50%,transparent 100%);width:100%;height:100%;border-radius:8px;z-index:-1;filter:blur(4px);animation:shine 5s ease-in-out infinite;} @keyframes shine{0%{left:-100%;}60%{left:120%;}100%{left:120%;}} .title{font-size:clamp(.85rem,3.2vw,1rem);font-weight:600;margin-top:6px;color:var(--accent-light);} .contact{display:flex;align-items:center;gap:8px;font-size:clamp(.75rem,3vw,.85rem);margin-top:10px;color:#eafff8;} .contact i{color:var(--brand-secondary);} .socials{margin-top:auto;display:flex;gap:12px;} .socials a{color:var(--brand-primary);font-size:clamp(1rem,4vw,1.2rem);transition:transform .25s ease,color .25s ease;} .socials a:hover{transform:scale(1.25) rotate(10deg);color:var(--brand-secondary);} .qr-container{margin:auto;width:28%;aspect-ratio:1/1;background:url('https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://cancerfree.io') center/cover no-repeat;border-radius:12px;filter:drop-shadow(0 0 6px rgba(0,0,0,.4));} .tagline{text-align:center;margin-top:4%;font-size:clamp(.8rem,2.6vw,.95rem);line-height:1.35;letter-spacing:.15px;color:#f4fff9;} @media (prefers-reduced-motion:reduce){*{animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important;}}
    </style>
  </head>
  <body>
    <div class="card-wrapper" data-tilt data-tilt-max="15" data-tilt-speed="600">
      <div class="card-inner">
        <div class="card-face front">
          <h1 class="name">{{ NAME }}</h1>
          <p class="title">{{ TITLE }}</p>
          <p class="contact"><i class="fa-solid fa-envelope"></i>{{ EMAIL }}</p>
          <p class="contact"><i class="fa-solid fa-phone"></i>{{ PHONE }}</p>
          <p class="contact"><i class="fa-solid fa-globe"></i>{{ WEBSITE }}</p>
          <div class="socials">{{ SOCIAL_LINKS | safe }}</div>
        </div>
        <div class="card-face back">
          <div class="qr-container"></div>
          <p class="tagline">"Put The Patient First"</p>
        </div>
      </div>
    </div>
    <script>
      document.addEventListener('DOMContentLoaded',()=>{
        const card=document.querySelector('.card-wrapper');
        VanillaTilt.init(card,{max:15,speed:600});
        card.addEventListener('click',()=>card.classList.toggle('is-flipped'));
      });
    </script>
  </body>
</html>"""
)

# ---------------------------- Routes ---------------------------- #
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
  
@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    """顯示表單頁面"""
    return HTMLResponse(content=FORM_HTML.render())


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request) -> HTMLResponse:
    """接收表單資料，儲存後轉跳到可分享名片網址"""

    form = await request.form()

    def v(key: str, default: str = "") -> str:
        return (form.get(key) or '').strip() or default

    name = v("NAME")
    title = v("TITLE")
    email = v("EMAIL")
    phone = v("PHONE", "(02)2732-2701")
    website = v("WEBSITE", "cancerfree.io")

    social_names = form.getlist("social_name") if hasattr(form, "getlist") else [form.get("social_name")]
    social_urls = form.getlist("social_url") if hasattr(form, "getlist") else [form.get("social_url")]

    def infer_icon(url: str) -> str:
        url_l = url.lower()
        BRAND_ICON_MAP = {
            "github": "fa-brands fa-github",
            "linkedin": "fa-brands fa-linkedin",
            "twitter": "fa-brands fa-twitter",
            "x.com": "fa-brands fa-x-twitter",
            "facebook": "fa-brands fa-facebook",
            "instagram": "fa-brands fa-instagram",
            "youtube": "fa-brands fa-youtube",
            "telegram": "fa-brands fa-telegram",
            "slack": "fa-brands fa-slack",
            "discord": "fa-brands fa-discord",
            "dribbble": "fa-brands fa-dribbble",
            "medium": "fa-brands fa-medium",
            "reddit": "fa-brands fa-reddit",
            "skype": "fa-brands fa-skype",
            "stackoverflow": "fa-brands fa-stack-overflow",
            "gitlab": "fa-brands fa-gitlab",
            "bitbucket": "fa-brands fa-bitbucket",
            "tiktok": "fa-brands fa-tiktok",
            "wechat": "fa-brands fa-weixin",
            "line": "fa-brands fa-line",
            "mastodon": "fa-brands fa-mastodon",
        }
        for key, icon_class in BRAND_ICON_MAP.items():
            if key in url_l:
                return icon_class
        return "fa-solid fa-link"

    links = []
    for n, u in zip(social_names, social_urls):
        u = (u or "").strip()
        if not u:
            continue
        n = (n or u).strip()
        icon = infer_icon(u)
        links.append(f'<a target="_blank" rel="noopener noreferrer" href="{u}" aria-label="{n}"><i class="{icon}"></i></a>')

    social_links_html = "\n".join(links)

    # 產生唯一 ID 並儲存資料到記憶體
    card_id = str(uuid.uuid4())[:8]
    card_storage[card_id] = {
        "NAME": name,
        "TITLE": title,
        "EMAIL": email,
        "PHONE": phone,
        "WEBSITE": website,
        "SOCIAL_LINKS": social_links_html,
    }

    # 導向 /card/{card_id}，即可分享
    return HTMLResponse(
        content=f"""
        <html><body>
        <script>
            window.location.href = "/card/{card_id}";
        </script>
        <p>名片已產生，若未自動跳轉請 <a href="/card/{card_id}">點此</a></p>
        </body></html>
        """
    )
@app.get("/card/{card_id}", response_class=HTMLResponse)
async def view_card(card_id: str) -> HTMLResponse:
    card_data = card_storage.get(card_id)
    if not card_data:
        return HTMLResponse(content="<h1>名片不存在</h1>", status_code=404)

    return HTMLResponse(content=CARD_TEMPLATE.render(**card_data))


# ---------------------------- How to Run ---------------------------- #
# 在命令列執行：
#   venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8888
# 然後瀏覽 http://<server-ip>:8888/
# ------------------------------------------------------------------- #
