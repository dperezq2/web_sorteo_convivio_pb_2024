from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session  # Importamos la extensión
import os
from werkzeug.utils import secure_filename
from utils.data_loader import load_participants
from utils.raffle_logic import perform_raffle

app = Flask(__name__)

# Configurar el almacenamiento de sesiones en el servidor
app.config['SESSION_TYPE'] = 'filesystem'  # O 'redis', 'sqlalchemy', etc.
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = './.flask_session'  # Carpeta para almacenar las sesiones

app.secret_key = os.urandom(24)  # Necesario para las sesiones
Session(app)  # Inicializar Flask-Session

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB máximo

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Manejo de subida de archivo
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Cargar participantes
            participants = load_participants(filepath)
            
            # Realizar sorteo
            winner = perform_raffle(participants)
            
            # Guardar el ganador y otros datos en la sesión
            session['winner'] = winner
            session['total_participants'] = len(participants)
            session['participants'] = participants  # Guardamos la lista de participantes
            
            # Redirigir a la página de resultados
            return redirect(url_for('result'))
    
    return render_template('index.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    winner = session.get('winner')
    participants = session.get('participants')
    total_participants = session.get('total_participants')

    if not winner or not total_participants:
        return redirect(url_for('index'))  # Si no hay datos, redirige al index

    # Si la solicitud es POST, realizar un nuevo sorteo excluyendo al ganador
    if request.method == 'POST':
        if participants:
            # Excluir al ganador de la lista de participantes
            participants = [p for p in participants if p['CUE'] != winner['CUE']]
            
            # Actualizar el total de participantes después de excluir al ganador
            total_participants = len(participants)
            
            # Realizar el sorteo nuevamente
            winner = perform_raffle(participants)
            session['winner'] = winner
            session['participants'] = participants  # Guardar los participantes actualizados
            session['total_participants'] = total_participants  # Actualizar el total de participantes
            
            # Redirigir a la misma página para mostrar el nuevo ganador y el contador actualizado
            return redirect(url_for('result'))

    # Extraer la información del ganador
    winner_name = winner.get('Empleado', 'No disponible')
    winner_photo = winner.get('PathFotografia', '')
    
    return render_template('result.html', winner_name=winner_name, winner_photo=winner_photo, total_participants=total_participants)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)