# 🏗️ ProdObra - Control de Productividad en Obras de Construcción

## Descripción

**ProdObra** es una aplicación web completa diseñada específicamente para el control de productividad en proyectos de construcción. Permite a los capataces registrar en tiempo real (desde su celular) las actividades ejecutadas, el personal asignado y el metrado logrado, generando automáticamente los **ratios de productividad** (horas-hombre por unidad de metrado).

La aplicación está pensada para usarse en campo con celulares Android/iOS a través del navegador, sin necesidad de instalar nada adicional.

---

## ✅ Características Principales

### Para Capataces (acceso móvil)
- Registro rápido de actividades con:
  - Selección de actividad del catálogo
  - Cantidad de personal (obreros)
  - Hora de inicio y fin (o uso de cronómetro en vivo)
  - Metrado ejecutado
- Cálculo automático de:
  - **Horas-Hombre** = Duración × Personal
  - **Ratio** = Horas-Hombre ÷ Metrado  (hh/unidad)
  - **Rendimiento** = Metrado ÷ Horas-Hombre  (unidad/hh)
- Historial de sus propios registros
- Dashboard personal con métricas del día
- Análisis de productividad por actividad

### Para Administrador
- Gestión completa de capataces (crear, ver, desactivar)
- Catálogo editable de actividades (con unidad de medida y ratio objetivo)
- Reportes generales con filtros por fecha, capataz y actividad
- Gráficos comparativos de ratios
- Exportación de datos a CSV
- Vista consolidada de todo el proyecto

### Seguridad y Usabilidad
- Sistema de login con roles (Admin / Capataz)
- Diseño responsive (funciona bien en celulares)
- Base de datos SQLite persistente
- Fácil de desplegar en la nube (gratis) o en una laptop de obra

---

## 🚀 Cómo Ejecutar la Aplicación (Local)

### Requisitos
- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Pasos de instalación

1. **Descarga los archivos**:
   - `prod_obra_app.py`
   - (Opcional) Este README

2. **Instala las dependencias**:
   ```bash
   pip install streamlit pandas plotly
   ```

3. **Ejecuta la aplicación**:
   ```bash
   streamlit run prod_obra_app.py
   ```

4. La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## 📱 Uso en Celulares (Recomendado para Capataces)

1. Ejecuta la aplicación en una laptop o PC que esté en la obra (o en la nube).
2. Los capataces acceden desde el navegador de su celular (Chrome recomendado).
3. **Recomendación**: Agregar la página a la pantalla de inicio del celular para que funcione como una "app".
4. Funciona incluso con conexión 4G/5G o WiFi de obra.

---

## 🌐 Despliegue Gratis en la Nube (Recomendado)

La forma más fácil y profesional de usar ProdObra es desplegarla gratis en **Streamlit Community Cloud**:

1. Crea una cuenta gratuita en [GitHub](https://github.com) (si no tienes).
2. Crea un nuevo repositorio y sube los archivos:
   - `prod_obra_app.py`
   - `requirements.txt` (crea este archivo con el contenido de abajo)
3. Ve a [share.streamlit.io](https://share.streamlit.io)
4. Conecta tu cuenta de GitHub y selecciona el repositorio.
5. ¡Listo! Tendrás una URL pública tipo `https://tu-app.streamlit.app` que puedes compartir con los capataces.

### Contenido del archivo `requirements.txt`:
```
streamlit
pandas
plotly
```

---

## 👥 Credenciales de Prueba (Demo)

Al iniciar la aplicación por primera vez se crean automáticamente estos usuarios:

| Rol          | Usuario        | Contraseña   | Nombre completo                     |
|--------------|----------------|--------------|-------------------------------------|
| Administrador| `admin`        | `admin123`   | Administrador General               |
| Capataz      | `juan.perez`   | `capataz123` | Juan Pérez - Capataz Estructuras    |
| Capataz      | `carlos.lopez` | `capataz123` | Carlos López - Capataz Acabados     |
| Capataz      | `maria.garcia` | `capataz123` | María García - Capataz MEP          |

> **Importante**: Cambia estas contraseñas en un entorno real.

---

## 📊 Lógica de Cálculo de Ratios

El sistema calcula automáticamente:

```
Horas-Hombre = (Hora Fin - Hora Inicio) × Cantidad de Personal

Ratio (hh/unidad) = Horas-Hombre ÷ Metrado Ejecutado

Rendimiento (unidad/hh) = Metrado Ejecutado ÷ Horas-Hombre
```

**Interpretación**:
- **Ratio más bajo** = Mayor productividad (se consumen menos horas-hombre por unidad ejecutada).
- **Rendimiento más alto** = Mejor productividad.

---

## 🗄️ Base de Datos

La aplicación usa **SQLite** (`productividad_obra.db`). 
- Se crea automáticamente en la primera ejecución.
- Es un archivo único que puedes respaldar fácilmente.
- Puedes abrirlo con herramientas como DB Browser for SQLite si necesitas consultar datos directamente.

---

## 🔧 Personalización para tu Obra (Torre Rosales)

Puedes fácilmente:
- Cambiar el nombre del proyecto en el código (línea ~280 y ~340).
- Agregar más actividades específicas de tu proyecto desde el panel de Administrador.
- Modificar los ratios objetivo según tus estándares internos.
- Agregar más campos (sector, nivel, cuadrilla, etc.) si lo necesitas (puedo ayudarte a extenderlo).

---

## 📌 Próximas Mejoras Posibles (si lo deseas)

- Modo offline completo (PWA) con sincronización posterior.
- Fotos adjuntas a cada registro (evidencia fotográfica).
- Integración con WhatsApp o Telegram para notificaciones.
- Exportación directa a Excel con formato profesional.
- Dashboard en tiempo real para el Residente de Obra.
- Módulo de "Tolerancia Cero" / seguridad cruzado con productividad.

---

## 🆘 Soporte

Esta aplicación fue creada específicamente para tu flujo de trabajo como Residente de Obra en el proyecto **Torre Rosales**.

Si necesitas:
- Agregar más campos o reportes específicos
- Cambiar colores o logo de la empresa
- Integrar con Google Sheets / Drive
- Versión más avanzada (con backend separado)

Solo dime y la ajusto o extiendo según tus necesidades.

---

**Desarrollado con ❤️ para la gestión eficiente de obras en Perú.**

*Versión 1.0 - Junio 2026*