# MyStore Project Setup Guide

เอกสารนี้รวบรวมขั้นตอนการเปิดใช้งานโปรเจกต์สำหรับผู้ที่เพิ่งดึงโค้ด (Clone) มาลงเครื่องเป็นครั้งแรก โดยจะแบ่งเป็นส่วน Backend และ Frontend

## 🛠 สิ่งที่ต้องมีในเครื่อง (Prerequisites)
1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (เปิดโปรแกรมทิ้งไว้ก่อนเริ่มรันโค้ด)
2. **[Node.js](https://nodejs.org/)** (สำหรับรันฝั่ง Frontend)

---

## 📦 1. การตั้งค่าฝั่ง Backend (Django + PostgreSQL)

เปิด Terminal แล้วเข้าไปที่โฟลเดอร์ `mystore_backend`
```bash
cd mystore_backend
```

### 0. การเตรียมไฟล์ Environment (.env)
เนื่องจากไฟล์ `.env` ถูกตั้งค่าไม่ให้อัปโหลดขึ้น Git เพื่อความปลอดภัยของข้อมูล ก่อนรันโปรเจกต์ครั้งแรกในแต่ละเครื่องจะต้องทำดังนี้:
1. คัดลอกไฟล์ `.env.example` แล้วเปลี่ยนชื่อเป็น `.env.dev`
2. สร้าง `SECRET_KEY` ใหม่ที่ไม่ซ้ำกัน โดยรันคำสั่งนี้ใน Terminal (เครื่องต้องมี Python):
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
3. นำรหัสที่ได้มา (Copy ไปทั้งบรรทัด) ไปใส่ไว้ในไฟล์ `.env.dev` ที่บรรทัด `SECRET_KEY=...`

### ขั้นตอนการรัน
1. **เริ่มการทำงานของ Server และฐานข้อมูล**
   ระบบจะทำการดาวน์โหลดและสร้างคอนเทนเนอร์ (ขั้นตอนนี้อาจใช้เวลาสักพักในครั้งแรก)
   ```bash
   docker compose -f docker-compose.dev.yaml --env-file .env.dev up -d --build
   ```

2. **สร้างโครงสร้างฐานข้อมูล (Migrate)**
   เนื่องจากฐานข้อมูลที่เพิ่งสร้างยังว่างเปล่า เราต้องสั่งให้ Django นำโครงสร้างตารางไปใส่ในฐานข้อมูล
   ```bash
   docker compose -f docker-compose.dev.yaml exec backend python manage.py migrate
   ```

3. **สร้างบัญชีแอดมิน (Superuser)**
   ใช้สำหรับล็อกอินเข้าหน้าจัดการข้อมูลหลังบ้านของระบบ
   ```bash
   docker compose -f docker-compose.dev.yaml exec backend python manage.py createsuperuser
   ```
   *(ทำตามขั้นตอนใน Terminal เพื่อตั้งชื่อผู้ใช้ อีเมล และรหัสผ่าน)*

---

## 🎨 2. การตั้งค่าฝั่ง Frontend (React / Vite)

เปิด Terminal อันใหม่ แล้วเข้าไปที่โฟลเดอร์ของ Frontend (ตัวอย่างเช่น `mystore/my-store-frontend`)
```bash
cd ../mystore/my-store-frontend
```

### ขั้นตอนการรัน
1. **ติดตั้ง Dependencies ทั้งหมด**
   ```bash
   npm install
   ```

2. **เปิดเซิร์ฟเวอร์สำหรับ Frontend**
   ```bash
   npm run dev
   ```

---

## 🌐 ช่องทางการเข้าถึง (Useful Links)

หลังจากที่รันคำสั่งทั้งหมดเรียบร้อยแล้ว คุณสามารถเข้าใช้งานระบบต่างๆ ได้ตามลิงก์ด้านล่างนี้:

| ระบบ | URL | ข้อมูลการเข้าสู่ระบบ (ถ้ามี) |
|---|---|---|
| **หน้าเว็บไซต์ (Frontend)** | [http://localhost:5173/](http://localhost:5173/) | - |
| **Backend API** | [http://localhost:8000/](http://localhost:8000/) | - |
| **Django Admin (หลังบ้าน)** | [http://localhost:8000/admin/](http://localhost:8000/admin/) | ใช้บัญชี Superuser ที่สร้างไว้ |
| **pgAdmin (จัดการฐานข้อมูล)** | [http://localhost:5050/](http://localhost:5050/) | **Email:** admin@admin.com<br>**Password:** admin |

---

## 💡 คำสั่งที่ใช้บ่อยใน Backend (Cheat Sheet)

- **ปิดการทำงาน Server ทั้งหมด:**
  ```bash
  docker compose -f docker-compose.dev.yaml down
  ```
- **เปิด Server ใหม่อีกครั้ง (กรณีเคย build แล้ว):**
  ```bash
  docker compose -f docker-compose.dev.yaml --env-file .env.dev up -d
  ```
- **ดู Logs ว่าเกิดอะไรขึ้น (Error / Request):**
  ```bash
  docker compose -f docker-compose.dev.yaml logs -f backend
  ```
