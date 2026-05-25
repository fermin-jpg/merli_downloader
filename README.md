# 🚀 Merlí - Descargador Autónomo de Episodios v1.0.0

Este software es de OpenSource sin ánimo de lucro.

---

He desarrollado este gestor de descargas gráfico en Python de código abierto para automatizar y ordenar la descarga y preservación de las temporadas 1, 2 y 3 de la aclamada serie "Merlí" desde el portal oficial de 3Cat.

---

## 📖 Manual de Instrucciones de Uso
He diseñado la interfaz de la aplicación para que sea súper intuitiva y autónoma:

* Inicia el run.bat
  
* Carga Inicial: Al abrir la aplicación por primera vez, se conectará a internet en segundo plano para raspar los metadatos de los capítulos directamente de 3Cat. Una vez obtenidos, se guardarán en un caché local (episodes_cache.json). En ejecuciones posteriores, la carga será instantánea usando dicho caché.
  
* Visualizar Episodios: La tabla izquierda lista todos los capítulos ordenados con su código identificador (S01E01, S01E02...), su título limpio, su estado actual y el progreso.

### Iniciar las Descargas:
Haz clic en 🚀 INICIAR. El descargador comenzará automáticamente a procesar el primer capítulo con estado Pendiente o Fallido. Una vez completado un episodio con éxito, actualizará su estado a ✅ Completado y pasará de inmediato al siguiente de forma secuencial y autónoma.

### Pausar/Detener:
Si deseas pausar las descargas, haz clic en 🛑 DETENER. La aplicación esperará a que termine de manera segura la descarga en curso o cancelará la conexión de forma segura para no corromper archivos parciales.


## 🛠️ Requisitos e Instalación
Para que puedas ejecutar mi script en tu máquina, necesitas contar con Python instalado y algunas librerías básicas.

### Requisitos Previos
Python 3.8 o superior (Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación).

### Instalación de Dependencias
Abre una terminal (PowerShell, Command Prompt o terminal de Linux/macOS) en el directorio del proyecto e instala las dependencias ejecutando el comando: pip install requests beautifulsoup4 yt-dlp

---

## Ejecución

* En Windows (Recomendado): Simplemente haz doble clic en el archivo lanzador que creé: run.bat. Este iniciará la consola, llamará al script de Python y mantendrá la ventana abierta si ocurre algún error.
* Desde Terminal: Ejecuta el comando "python downloader.py" en el directorio del proyecto.

---



### Acciones Adicionales:
* 📁 Abrir Carpeta Videos: Abre directamente en el explorador de tu sistema el directorio donde se están guardando los videos (por defecto, la carpeta nativa Videos de tu usuario en Windows: C:\Users\<Usuario>\Videos).
* 🔄 Buscar Episodios Web: Si la serie recibe actualizaciones en la web de 3Cat o deseas forzar una actualización del catálogo, este botón limpiará la caché y volverá a realizar el raspado en tiempo real.

---

## ⚙️ Funcionamiento Técnico Interno (Arquitectura)
He sido ayudado con una IA.
