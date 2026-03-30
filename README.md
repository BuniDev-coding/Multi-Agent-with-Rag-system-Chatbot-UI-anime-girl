# Multi-Agent AI System — Website Creator

ระบบ Multi-Agent AI สำหรับสร้างเว็บไซต์และพัฒนาซอฟต์แวร์แบบครบวงจร โดยทีมตัวแทน AI เฉพาะทาง 8 คน ที่ทำงานร่วมกันผ่าน LangGraph

---

## ภาพรวม (Overview)

แอปพลิเคชันนี้ใช้ **Supervisor/Orchestrator Pattern** ในการส่งต่อคำขอของผู้ใช้ไปยัง Agent ที่เหมาะสม โดยแต่ละ Agent มีความเชี่ยวชาญเฉพาะด้าน และทุก Agent ถูกฝังด้วย **TIGERSOFT Brand Guidelines** เพื่อให้ผลลัพธ์มีความสอดคล้องกับ Design System

```
User Input
    └─→ Supervisor Agent (routing)
            ├─→ PM Agent
            ├─→ R&D Agent
            ├─→ Frontend Agent  ─→  สร้างเว็บไซต์ (HTML/CSS/JS)
            ├─→ Backend Agent
            ├─→ Tester (QA) Agent
            ├─→ DevOps Agent
            └─→ Consultant Agent
```

![alt text](image-1.png)
![alt text](image.png)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JavaScript, HTML5, CSS3 |
| Backend | FastAPI, Python |
| Agent Framework | LangGraph + LangChain |
| LLM | OpenAI GPT-4o / Google Gemini |
| Vector DB | ChromaDB + all-MiniLM-L6-v2 |
| File Parsing | pypdf, python-docx |
| Web Server | Uvicorn (ASGI) |

---

## โครงสร้างโปรเจกต์ (Project Structure)

```
Multi-Agent-with-UI-create-website/
├── .agents/                    # Skill definitions (prompt injection per agent)
│   ├── PM/skill.md
│   ├── Frontend/skill.md
│   ├── Backend/skill.md
│   ├── RD/skill.md
│   ├── DevOps/skill.md
│   ├── Tester(QA)/skill.md
│   ├── Consultant/skill.md
│   └── Supervisor/skill.md
├── backend/
│   ├── agent.py                # LangGraph multi-agent orchestration
│   ├── main.py                 # FastAPI server & API routes
│   └── rag.py                  # RAG layer (ChromaDB + embeddings)
├── frontend/
│   ├── index.html              # Single-page application
│   ├── app.js                  # Client-side logic
│   └── style.css               # TIGERSOFT Design System
├── public/Image/               # Agent avatar images
├── chroma_db/                  # Local vector store (auto-generated)
├── design.md                   # TIGERSOFT Brand Identity guidelines
├── requirements.txt
└── .env
```

---

## การติดตั้ง (Installation)

### 1. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

สำหรับรองรับ PDF และ DOCX:

```bash
pip install pypdf python-docx
```

### 2. ตั้งค่า API Key

สร้างหรือแก้ไขไฟล์ `.env`:

```env
OPENAI_API_KEY=your_openai_key_here
Google_genai=your_gemini_key_here
```

### 3. รันเซิร์ฟเวอร์

```bash
python backend/main.py
```

เปิดเบราว์เซอร์ที่ `http://localhost:8000`

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/chat` | ส่งข้อความหา Agent |
| `POST` | `/api/upload` | อัปโหลดไฟล์เข้า Knowledge Base |
| `GET` | `/api/documents` | แสดงรายการเอกสารใน KB |
| `DELETE` | `/api/documents/{id}` | ลบเอกสารออกจาก KB |

---

## ความสามารถของ Agent แต่ละตัว

| Agent | หน้าที่ |
|-------|--------|
| **Supervisor** | วิเคราะห์คำขอและ route ไปยัง Agent ที่เหมาะสม |
| **PM** | วางแผนโปรเจกต์, เขียน requirements, user stories |
| **R&D** | ออกแบบ architecture, เลือก technology stack |
| **Frontend** | สร้างเว็บไซต์ HTML/CSS/JS (single-file, vanilla) |
| **Backend** | ออกแบบ API, database schema |
| **Tester (QA)** | เขียน test cases, QA plan |
| **DevOps** | Docker config, CI/CD pipeline |
| **Consultant** | Q&A ทั่วไป, brainstorming |

---

## ฟีเจอร์หลัก (Key Features)

- **Live HTML Preview** — รันเว็บไซต์ที่ AI สร้างได้ทันทีใน iFrame
- **Download Project** — ดาวน์โหลดไฟล์ HTML จาก response
- **Knowledge Base (RAG)** — อัปโหลดไฟล์ (.txt, .pdf, .docx, .md) เพื่อให้ Agent ใช้ข้อมูล
- **Chat History** — ส่งประวัติสนทนา 10 รายการล่าสุดให้ Agent มีบริบท
- **Agent Badges** — แสดงว่า Agent ไหนตอบ เช่น `[Frontend Agent]`
- **Dual LLM Support** — สลับระหว่าง GPT-4o และ Gemini ได้ใน `agent.py`

---

## การเปลี่ยน LLM

เปิด `backend/agent.py` และแก้บริเวณบรรทัด 51-55:

```python
# ใช้ OpenAI GPT-4o
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

# หรือใช้ Google Gemini (default)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
```

---

## Design System

UI ใช้ **TIGERSOFT Brand Identity** ตามที่กำหนดใน `design.md`:

| ชื่อ | Hex |
|-----|-----|
| Vivid Red (Primary) | `#F4001A` |
| Oxford Blue | `#0B1F38` |
| UFO Green | `#50C8B5` |
| White | `#FFFFFF` |
| Quick Silver | `#A3A3A3` |

Design ใช้ Glassmorphism, Gradient overlays, Micro-animations, และ Responsive layout (375px – 1440px)

---

## Notes

- `chroma_db/` จะถูกสร้างอัตโนมัติเมื่อรันครั้งแรก
- Frontend เป็น Vanilla JS ไม่ต้อง build
- CORS เปิดกว้าง (all origins) เหมาะสำหรับ local development
- Server รันด้วย `reload=True` (auto-reload เมื่อแก้ไขโค้ด)
