# 🚀 GUÍA DE INSTALACIÓN RÁPIDA - MEJORAS IMPLEMENTADAS

**Tiempo estimado:** 15 minutos

---

## 📋 PREREQUISITOS

- Python 3.11+
- Node.js 18+
- OpenSSL (para generar secret key)

---

## 🔧 INSTALACIÓN

### PASO 1: Backend

```bash
# 1.1 Navegar al backend
cd backend

# 1.2 Instalar nueva dependencia
pip install slowapi==0.1.9

# 1.3 Generar SECRET_KEY segura
openssl rand -hex 32
# Copia el resultado, lo necesitarás para el .env

# 1.4 Crear directorio de logs
mkdir -p logs

# 1.5 Actualizar .env (o crear si no existe)
# Agrega o modifica estas líneas:
```

```env
# === Agregar estas líneas a backend/.env ===

# Authentication & Security
SECRET_KEY=<pegar-aqui-el-resultado-del-openssl>
DASHBOARD_URL=http://localhost:3000

# CORS - Allowed origins
CORS_ORIGINS=["http://localhost:3000"]

# Meta WhatsApp (asegúrate de tener este)
WHATSAPP_VERIFY_TOKEN=tu-verify-token-aqui

# === Mantén las otras variables que ya tenías ===
```

```bash
# 1.6 Verificar instalación
python -c "import slowapi; print('✅ SlowAPI instalado')"

# 1.7 Reiniciar servidor
uvicorn app.main:app --reload
```

**Verificación Backend:**
```bash
# Debe mostrar logs estructurados
curl http://localhost:8000/health/

# Verificar que se creó el archivo de log
ls -la logs/
```

---

### PASO 2: Frontend

```bash
# 2.1 Navegar al frontend
cd ../frontend

# 2.2 Verificar que zod está instalado
npm list zod
# Si no está, instalarlo:
# npm install zod

# 2.3 Crear/actualizar .env.local
```

```env
# === Crear/actualizar frontend/.env.local ===

NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development
```

```bash
# 2.4 Verificar que compila sin errores
npm run build

# 2.5 Iniciar dev server
npm run dev
```

**Verificación Frontend:**
```bash
# Debe redirigir a /auth
curl -I http://localhost:3000/dashboard
```

---

## ✅ TESTS DE VERIFICACIÓN

### Test 1: CORS (Backend)
```bash
# Debe FALLAR (origen no permitido)
curl -X OPTIONS http://localhost:8000/api/v1/chat/ \
  -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep "Access-Control-Allow-Origin"
# No debe mostrar el header

# Debe FUNCIONAR (origen permitido)
curl -X OPTIONS http://localhost:8000/api/v1/chat/ \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v 2>&1 | grep "Access-Control-Allow-Origin"
# Debe mostrar: Access-Control-Allow-Origin: http://localhost:3000
```

### Test 2: Logging (Backend)
```bash
# Hacer una request
curl http://localhost:8000/health/

# Verificar que se creó el log
cat logs/loki_$(date +%Y%m%d).log | tail -5
# Debe mostrar logs estructurados con timestamp
```

### Test 3: Rate Limiting (Backend)
```bash
# Hacer 101 requests rápidos (Linux/Mac)
for i in {1..101}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    http://localhost:8000/whatsapp/webhook \
    -X POST -H "Content-Type: application/json" -d '{}' &
done | grep 429

# Windows PowerShell
1..101 | ForEach-Object {
  Start-Job -ScriptBlock {
    Invoke-WebRequest -Uri "http://localhost:8000/whatsapp/webhook" -Method POST
  }
}
# Algunos requests deben retornar 429
```

### Test 4: Middleware (Frontend)
```bash
# Sin token debe redirigir
curl -I http://localhost:3000/dashboard 2>&1 | grep "307\|Location"
# Expected: 307 Temporary Redirect
# Location: http://localhost:3000/auth?error=auth_required
```

### Test 5: Variables de Entorno (Frontend)
```bash
cd frontend

# Renombrar .env.local temporalmente
mv .env.local .env.local.backup

# Intentar build (debe fallar)
npm run build 2>&1 | grep "Invalid environment"
# Expected: Error de Zod

# Restaurar
mv .env.local.backup .env.local
```

### Test 6: Error Boundaries (Frontend)
1. Abrir http://localhost:3000
2. Abrir Dev Tools Console
3. En cualquier componente, forzar un error:
   ```typescript
   throw new Error('Test error');
   ```
4. Debe mostrar la UI de error personalizada (no pantalla blanca)

---

## 🐛 TROUBLESHOOTING

### Problema: "SECRET_KEY is required"

**Solución:**
```bash
# Generar nueva key
openssl rand -hex 32

# Agregarla a backend/.env
echo "SECRET_KEY=<tu-key-aqui>" >> backend/.env
```

### Problema: "slowapi not found"

**Solución:**
```bash
cd backend
pip install --upgrade slowapi==0.1.9
pip list | grep slowapi
```

### Problema: "Invalid environment variables (Frontend)"

**Solución:**
```bash
# Verificar que existe .env.local
cat frontend/.env.local

# Debe contener:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_ENV=development
```

### Problema: "CORS error en frontend"

**Solución:**
```bash
# Verificar que CORS_ORIGINS incluye el frontend
cat backend/.env | grep CORS_ORIGINS
# Debe incluir: ["http://localhost:3000"]

# Si usa puerto diferente, actualizar
```

### Problema: Middleware loop infinito

**Solución:**
```bash
# Verificar que / y /auth están en PUBLIC_ROUTES
cat frontend/middleware.ts | grep PUBLIC_ROUTES
# Debe mostrar: const PUBLIC_ROUTES = ['/', '/auth'];
```

---

## 📊 CHECKLIST DE INSTALACIÓN

### Backend
- [ ] SlowAPI instalado
- [ ] SECRET_KEY generada y en .env
- [ ] CORS_ORIGINS configurado
- [ ] Directorio logs/ creado
- [ ] Servidor arranca sin errores
- [ ] Logs se generan en logs/

### Frontend
- [ ] Zod instalado
- [ ] .env.local creado con variables requeridas
- [ ] Build funciona sin errores
- [ ] Middleware redirige correctamente
- [ ] Error boundaries se muestran

### Tests
- [ ] CORS rechaza orígenes no permitidos
- [ ] Logs se escriben correctamente
- [ ] Rate limiting funciona (429 después de 100 req)
- [ ] Middleware protege /dashboard
- [ ] Variables de entorno validadas

---

## 🎯 SIGUIENTE PASO

Una vez completada la instalación, revisa:

1. **Backend:** http://localhost:8000/docs - Debe funcionar
2. **Frontend:** http://localhost:3000 - Debe cargar
3. **Logs:** `tail -f backend/logs/loki_*.log` - Debe mostrar actividad

---

## 📚 DOCUMENTACIÓN COMPLETA

Para más detalles, consulta:

- [RESUMEN_MEJORAS_IMPLEMENTADAS.md](./RESUMEN_MEJORAS_IMPLEMENTADAS.md) - Overview completo
- [MEJORAS_IMPLEMENTADAS_BACKEND.md](./MEJORAS_IMPLEMENTADAS_BACKEND.md) - Detalles backend
- [MEJORAS_IMPLEMENTADAS_FRONTEND.md](./MEJORAS_IMPLEMENTADAS_FRONTEND.md) - Detalles frontend

---

## 🆘 SOPORTE

Si encuentras problemas:

1. Verificar versiones:
   ```bash
   python --version  # 3.11+
   node --version    # 18+
   ```

2. Limpiar e reinstalar:
   ```bash
   # Backend
   pip uninstall slowapi
   pip install slowapi==0.1.9

   # Frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

3. Revisar logs de error en consola

---

**¡Listo! Tu aplicación ahora es segura y profesional.** 🎉
