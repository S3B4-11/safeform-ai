"""SafeForm AI — interfaz Streamlit (Streamlit Community Cloud).

Misma logica de inferencia que la version Gradio: ambas importan safeform_core,
asi que no pueden divergir. Lo unico propio de este archivo es la interfaz.
"""
import tempfile
from pathlib import Path

import streamlit as st

from safeform_core import analizar, ejercicios_disponibles, etiqueta_es

st.set_page_config(page_title='SafeForm AI', page_icon='\U0001F3CB', layout='wide')


@st.cache_resource(show_spinner=False)
def _catalogo():
    ejercicios = ejercicios_disponibles()
    return {etiqueta_es(e): e for e in ejercicios}


CATALOGO = _catalogo()

st.title('SafeForm AI')
st.caption('Evaluacion biomecanica de ejercicios a partir de video. Identifica el error '
           'especifico, la correccion y su fundamento clinico.')

if not CATALOGO:
    st.error('No hay modelos disponibles en la carpeta modelos/. Revisa el despliegue.')
    st.stop()

columna_entrada, columna_resultado = st.columns([1, 1.3], gap='large')

with columna_entrada:
    etiqueta = st.selectbox('Ejercicio', list(CATALOGO.keys()))
    archivo = st.file_uploader('Video del ejercicio', type=['mp4', 'mov', 'avi', 'mkv'])
    evaluar = st.button('Evaluar', type='primary', use_container_width=True,
                        disabled=archivo is None)
    st.info('**Para mejores resultados:** cuerpo entero visible, camara fija, buena '
            'iluminacion, una sola persona en cuadro y una repeticion completa.')
    if archivo is not None:
        st.video(archivo)

with columna_resultado:
    if not evaluar:
        st.markdown('### Sube un video y presiona **Evaluar**.')
    else:
        sufijo = Path(archivo.name).suffix or '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as temporal:
            temporal.write(archivo.getbuffer())
            ruta_video = temporal.name

        with st.spinner('Analizando la ejecucion...'):
            texto, probabilidades, imagen_clave, video_anotado = analizar(ruta_video, etiqueta)

        if imagen_clave:
            st.image(imagen_clave,
                     caption='Instante mas critico — en rojo, la zona evaluada como incorrecta',
                     use_container_width=True)
        st.markdown(texto)

        if probabilidades:
            st.markdown('#### Probabilidad por clase')
            for nombre, valor in sorted(probabilidades.items(), key=lambda x: -x[1]):
                st.progress(min(max(float(valor), 0.0), 1.0), text=f'{nombre} — {valor:.1%}')

        if video_anotado:
            st.markdown('#### Analisis completo')
            st.video(video_anotado)
