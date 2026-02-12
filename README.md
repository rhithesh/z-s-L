# README

PLEASE GO THROUGHR code_understanding.md so you get a through understanding of the code base. MOST CLASS FILES have the flow of the CODE and functions at the start as comments, This is for understanding as well as suggestions and changes we feel like making,
so that we can see to and work more on development. 

first run devicecheck.py and then find the right device_index, run audiotest.py with the updated device_index if it transcribes fine, update it at pipertts and whispermodule.

API Key Setup IF YOU ARE NOT USING MLA, please ask me for the OPENROUTER API KEY and put it inside:
----
DMSLM/helper/chat.py
gi
```python
self.api_key="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"
```

note this key wont work 

---

Install `uv` if not installed:

```bash
pip install uv
```

Make sure your Python version is:

```
requires-python = ">=3.12"
```

Install all required packages:

```bash
uv sync
```

Activate your virtual environment:

```bash
source .venv/bin/activate
```

---

Run with logging (not recommended for development):

```bash
uvicorn server:app --reload 2>&1 | tee "logs/$(date +%Y-%m-%d_%H-%M-%S).log"
```

Or quick start:

```bash
uvicorn server:app
```

---

## Start the Frontend

Navigate into the frontend folder:

```bash
cd ltts
```

Check folder contents:

```bash
ls
```

Expected output:

```
app                     next.config.ts          package.json            README.md
eslint.config.mjs       node_modules            postcss.config.mjs      tsconfig.json
next-env.d.ts           package-lock.json       public
```

---

install Node.js:
[https://nodejs.org/en/download](https://nodejs.org/en/download)

Verify installation node and npm will be both installed:

```bash
node -v
npm -v
```

My versions are:

```
node v25.1.0
npm 11.6.2
```

---

now,

```bash
npm i
```

You should now see the `/node_modules` folder.

---

Start Frontend Server

```bash
npm run dev
```

Expected output:

```
▲ Next.js 16.0.1 (Turbopack)
- Local:        http://localhost:3000
- Network:      http://172.20.10.2:3000
```

---

Both backend & frontend should now be running successfully.
