// Configuración
const API_BASE_URL = 'http://localhost:8000/api/v1';
let currentUser = null;
let allHabits = new Set();

// Inicializar la aplicación
async function init() {
    try {
        // Crear o cargar usuario
        await loadOrCreateUser();
        
        // Cargar estadísticas
        await loadStats();
        
        // Auto-resize del textarea
        const textarea = document.getElementById('messageInput');
        textarea.addEventListener('input', autoResize);
        
        console.log('Aplicación inicializada correctamente');
    } catch (error) {
        console.error('Error al inicializar:', error);
        showError('No se pudo conectar con el servidor. Asegúrate de que esté corriendo en http://localhost:8000');
    }
}

// Cargar o crear usuario
async function loadOrCreateUser() {
    try {
        // Intentar obtener usuarios existentes
        const response = await fetch(`${API_BASE_URL}/usuarios/`);
        const usuarios = await response.json();
        
        if (usuarios && usuarios.length > 0) {
            // Usar el primer usuario (en producción, aquí habría login)
            currentUser = usuarios[0];
        } else {
            // Crear usuario de demostración
            const newUserResponse = await fetch(`${API_BASE_URL}/usuarios/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nombre: 'Diego',
                    telefono: '+541165992142',
                    timezone: 'America/Argentina/Buenos_Aires'
                })
            });
            
            if (newUserResponse.ok) {
                currentUser = await newUserResponse.json();
            } else {
                throw new Error('No se pudo crear el usuario');
            }
        }
        
        // Actualizar UI
        document.getElementById('userName').textContent = currentUser.nombre;
        
    } catch (error) {
        console.error('Error al cargar usuario:', error);
        throw error;
    }
}

// Cargar estadísticas
async function loadStats() {
    try {
        // Cargar historial de conversaciones
        const historyResponse = await fetch(`${API_BASE_URL}/chat/history/${currentUser.id}`);
        const historyData = await historyResponse.json();
        
        document.getElementById('totalConversations').textContent = 
            historyData.total_conversaciones || 0;
        
        // Extraer hábitos únicos del historial
        if (historyData.conversaciones) {
            historyData.conversaciones.forEach(conv => {
                if (conv.contexto && conv.contexto.habits_mentioned) {
                    conv.contexto.habits_mentioned.forEach(habit => allHabits.add(habit));
                }
            });
            updateHabitsList();
        }
        
        // Cargar estados de ánimo
        const moodsResponse = await fetch(`${API_BASE_URL}/usuarios/${currentUser.id}/estados_animo/`);
        const moods = await moodsResponse.json();
        
        document.getElementById('totalMoods').textContent = moods.length || 0;
        
        if (moods.length > 0) {
            document.getElementById('lastMood').textContent = `${moods[0].nivel}/10`;
        }
        
    } catch (error) {
        console.error('Error al cargar estadísticas:', error);
    }
}

// Actualizar lista de hábitos
function updateHabitsList() {
    const habitsList = document.getElementById('habitsList');
    
    if (allHabits.size === 0) {
        habitsList.innerHTML = '<p class="empty-state">Ningún hábito detectado aún</p>';
        return;
    }
    
    habitsList.innerHTML = Array.from(allHabits)
        .map(habit => `<span class="habit-tag">${habit}</span>`)
        .join('');
}

// Enviar mensaje
async function sendMessage(event) {
    event.preventDefault();
    
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Deshabilitar input
    input.disabled = true;
    document.getElementById('sendButton').disabled = true;
    
    // Mostrar mensaje del usuario
    addMessageToChat(message, 'user');
    
    // Limpiar input
    input.value = '';
    autoResize({ target: input });
    
    // Mostrar indicador de escritura
    document.getElementById('typingIndicator').style.display = 'flex';
    
    try {
        // Enviar a la API
        const response = await fetch(`${API_BASE_URL}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                usuario_id: currentUser.id,
                mensaje: message
            })
        });
        
        if (!response.ok) {
            throw new Error('Error al enviar el mensaje');
        }
        
        const data = await response.json();
        
        // Simular delay de escritura
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Ocultar indicador
        document.getElementById('typingIndicator').style.display = 'none';
        
        // Mostrar respuesta de Loki
        addMessageToChat(data.respuesta, 'loki', data.habitos_detectados);
        
        // Actualizar hábitos
        if (data.habitos_detectados && data.habitos_detectados.length > 0) {
            data.habitos_detectados.forEach(habit => allHabits.add(habit));
            updateHabitsList();
        }
        
        // Actualizar estadísticas
        await loadStats();
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('typingIndicator').style.display = 'none';
        addMessageToChat('Lo siento, hubo un error al procesar tu mensaje. Por favor, intenta de nuevo.', 'loki');
    } finally {
        // Rehabilitar input
        input.disabled = false;
        document.getElementById('sendButton').disabled = false;
        input.focus();
    }
}

// Agregar mensaje al chat
function addMessageToChat(message, sender, habits = []) {
    const messagesContainer = document.getElementById('chatMessages');
    
    const messageRow = document.createElement('div');
    messageRow.className = `message-row ${sender}`;
    
    const avatar = document.createElement('div');
    avatar.className = sender === 'loki' ? 'loki-avatar' : 'user-avatar';
    avatar.textContent = sender === 'loki' ? '🎭' : '👤';
    
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}-message`;
    
    const text = document.createElement('p');
    text.textContent = message;
    bubble.appendChild(text);
    
    // Agregar hábitos detectados si existen
    if (habits && habits.length > 0) {
        const habitsDiv = document.createElement('div');
        habitsDiv.className = 'habits-detected';
        habits.forEach(habit => {
            const badge = document.createElement('span');
            badge.className = 'habit-badge';
            badge.textContent = `✓ ${habit}`;
            habitsDiv.appendChild(badge);
        });
        bubble.appendChild(habitsDiv);
    }
    
    const timestamp = document.createElement('div');
    timestamp.className = 'message-timestamp';
    timestamp.textContent = new Date().toLocaleTimeString('es-AR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    bubble.appendChild(timestamp);
    
    messageRow.appendChild(avatar);
    messageRow.appendChild(bubble);
    
    messagesContainer.appendChild(messageRow);
    
    // Scroll al final
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Auto-resize del textarea
function autoResize(event) {
    const textarea = event.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// Manejar Enter para enviar
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        document.getElementById('chatForm').dispatchEvent(new Event('submit'));
    }
}

// Ver historial
async function viewHistory() {
    const modal = document.getElementById('historyModal');
    const content = document.getElementById('historyContent');
    
    content.innerHTML = '<p>Cargando...</p>';
    modal.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/chat/history/${currentUser.id}?limit=50`);
        const data = await response.json();
        
        if (data.conversaciones.length === 0) {
            content.innerHTML = '<p class="empty-state">No hay conversaciones aún</p>';
            return;
        }
        
        content.innerHTML = data.conversaciones.map(conv => `
            <div class="history-item">
                <div class="history-timestamp">
                    ${new Date(conv.timestamp).toLocaleString('es-AR')}
                </div>
                <div class="history-message">
                    <strong>Tú:</strong> ${conv.mensaje}
                </div>
                <div class="history-message">
                    <strong>Loki:</strong> ${conv.respuesta}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        content.innerHTML = '<p class="empty-state">Error al cargar el historial</p>';
        console.error('Error:', error);
    }
}

// Ver estados de ánimo
async function viewMoods() {
    const modal = document.getElementById('moodsModal');
    const content = document.getElementById('moodsContent');
    
    content.innerHTML = '<p>Cargando...</p>';
    modal.classList.add('show');
    
    try {
        const response = await fetch(`${API_BASE_URL}/usuarios/${currentUser.id}/estados_animo/`);
        const moods = await response.json();
        
        if (moods.length === 0) {
            content.innerHTML = '<p class="empty-state">No hay estados de ánimo registrados aún</p>';
            return;
        }
        
        content.innerHTML = moods.map(mood => `
            <div class="mood-item">
                <div class="mood-level">${mood.nivel}/10</div>
                <div class="mood-info">
                    <div class="history-timestamp">
                        ${new Date(mood.timestamp).toLocaleString('es-AR')}
                    </div>
                    ${mood.notas_texto ? `<div class="mood-note">${mood.notas_texto}</div>` : ''}
                </div>
                <div>${getMoodEmoji(mood.nivel)}</div>
            </div>
        `).join('');
        
    } catch (error) {
        content.innerHTML = '<p class="empty-state">Error al cargar los estados de ánimo</p>';
        console.error('Error:', error);
    }
}

// Obtener emoji según nivel de ánimo
function getMoodEmoji(level) {
    if (level >= 9) return '😄';
    if (level >= 7) return '😊';
    if (level >= 5) return '😐';
    if (level >= 3) return '😔';
    return '😢';
}

// Cerrar modal
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('show');
}

// Cerrar modal al hacer click fuera
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('show');
    }
}

// Mostrar error
function showError(message) {
    const messagesContainer = document.getElementById('chatMessages');
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = 'padding: 1rem; background: #fee; border: 2px solid #f88; border-radius: 8px; margin: 1rem; color: #c00;';
    errorDiv.textContent = `⚠️ ${message}`;
    messagesContainer.appendChild(errorDiv);
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
