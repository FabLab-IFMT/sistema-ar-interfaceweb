// Arquivo: ar_controller.js
// Funções JavaScript para controlar o ar condicionado de forma assíncrona

// Função para mostrar notificações
function showNotification(message, type = 'success') {
    // Cria um elemento de toast para exibir a mensagem
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Fechar"></button>
            </div>
        </div>
    `;
    
    // Adiciona o toast ao container
    const toastContainer = document.getElementById('toast-container');
    toastContainer.innerHTML += toastHtml;
    
    // Inicializa e mostra o toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Remove o toast do DOM após ser escondido
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Função genérica para enviar comandos AJAX
async function sendCommand(url, method = 'POST', data = {}) {
    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        const options = {
            method: method,
            headers: {
                'X-CSRFToken': csrftoken,
                'Content-Type': 'application/json'
            }
        };
        
        if (method !== 'GET' && Object.keys(data).length > 0) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`Erro na requisição: ${response.status} - ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Erro ao enviar comando:', error);
        showNotification('Erro ao processar requisição: ' + error.message, 'danger');
        throw error;
    }
}

// Função para ligar ou desligar o ar
async function togglePower(arId, action) {
    const url = `/painelar/ar/${arId}/${action}/ajax/`;
    const result = await sendCommand(url);
    
    if (result.success) {
        showNotification(result.message);
        // Atualiza a interface sem recarregar
        updateInterface(result.data);
    } else {
        showNotification(result.message, 'danger');
    }
}

// Função para ajustar temperatura
async function adjustTemperature(arId, temperature) {
    const url = `/painelar/ar/${arId}/temperatura/ajax/`;
    const result = await sendCommand(url, 'POST', {temperatura: temperature});
    
    if (result.success) {
        showNotification(result.message);
        // Atualiza a temperatura na interface
        document.querySelectorAll('.temperature-display').forEach(el => {
            el.textContent = `${result.data.temperatura}°C`;
        });
    } else {
        showNotification(result.message, 'danger');
    }
}

// Função para ajustar modo
async function adjustMode(arId, mode) {
    const url = `/painelar/ar/${arId}/modo/ajax/`;
    const result = await sendCommand(url, 'POST', {modo: mode});
    
    if (result.success) {
        showNotification(result.message);
        // Atualiza os botões de modo
        document.querySelectorAll('.ar-mode-btn').forEach(el => {
            el.classList.remove('active-mode-btn');
            if (el.getAttribute('data-mode') === mode) {
                el.classList.add('active-mode-btn');
            }
        });
    } else {
        showNotification(result.message, 'danger');
    }
}

// Função para ajustar velocidade
async function adjustSpeed(arId, speed) {
    const url = `/painelar/ar/${arId}/velocidade/ajax/`;
    const result = await sendCommand(url, 'POST', {velocidade: speed});
    
    if (result.success) {
        showNotification(result.message);
        // Atualiza os botões de velocidade
        document.querySelectorAll('.ar-speed-btn').forEach(el => {
            el.classList.remove('active-mode-btn');
            if (el.getAttribute('data-speed') === speed.toString()) {
                el.classList.add('active-mode-btn');
            }
        });
    } else {
        showNotification(result.message, 'danger');
    }
}

// Função para alternar swing
async function toggleSwing(arId) {
    const url = `/painelar/ar/${arId}/swing/ajax/`;
    const result = await sendCommand(url);
    
    if (result.success) {
        showNotification(result.message);
        // Atualiza o botão swing
        const swingBtn = document.getElementById('swing-btn');
        if (swingBtn) {
            if (result.data.swing) {
                swingBtn.classList.add('active-mode-btn');
            } else {
                swingBtn.classList.remove('active-mode-btn');
            }
        }
    } else {
        showNotification(result.message, 'danger');
    }
}

// Função para verificar status do ar condicionado
async function checkStatus(arId) {
    try {
        const url = `/painelar/ar/${arId}/status/ajax/`;
        const result = await sendCommand(url, 'GET');
        
        if (result.success) {
            // Atualiza a interface com os dados recebidos
            updateInterface(result.data);
            showNotification('Status atualizado com sucesso!');
        } else {
            showNotification('Falha ao verificar status: ' + result.message, 'warning');
            // Se o servidor informou que está offline, atualiza a interface
            if (result.data && result.data.online === false) {
                updateInterface({ online: false });
            }
        }
    } catch (error) {
        console.error('Erro ao verificar status:', error);
        // Se não conseguiu conectar, provavelmente o servidor está inacessível
        showNotification('Erro ao conectar com o servidor. Verifique sua conexão.', 'danger');
        // Atualiza a interface para mostrar offline
        updateInterface({ online: false });
    }
}

// Função para atualizar toda a interface com novos dados
function updateInterface(data) {
    // Atualiza status online/offline
    const isOnline = data.online;
    const offlineOverlay = document.querySelector('.offline-overlay');
    const statusBadge = document.querySelector('.badge');
    
    if (isOnline) {
        if (offlineOverlay) offlineOverlay.style.display = 'none';
        if (statusBadge) {
            statusBadge.classList.remove('badge-offline');
            statusBadge.classList.add('badge-online');
            statusBadge.textContent = 'Online';
        }
    } else {
        if (offlineOverlay) offlineOverlay.style.display = 'flex';
        if (statusBadge) {
            statusBadge.classList.remove('badge-online');
            statusBadge.classList.add('badge-offline');
            statusBadge.textContent = 'Offline';
        }
        
        // Se estiver offline, recarrega a página após 2 segundos
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    }
    
    // Atualiza temperatura
    if (data.temperatura !== undefined) {
        document.querySelectorAll('.temperature-display').forEach(el => {
            el.textContent = `${data.temperatura}°C`;
        });
    }
    
    // Atualiza temperatura ambiente
    if (data.temperatura_ambiente !== undefined) {
        const ambientTemp = document.querySelector('.ambient-temp .h4');
        if (ambientTemp) {
            ambientTemp.textContent = `${data.temperatura_ambiente}°C`;
        }
    }
    
    // Atualiza estado (ligado/desligado)
    if (data.estado !== undefined) {
        const powerControls = document.querySelector('.power-controls');
        if (powerControls) {
            if (data.estado) {
                // Ar está ligado, mostra controles
                document.querySelectorAll('.ar-controls').forEach(el => {
                    el.style.display = 'block';
                });
                
                // Atualiza botão de power
                const powerBtn = document.getElementById('power-btn');
                if (powerBtn) {
                    powerBtn.setAttribute('onclick', `togglePower(${data.id}, 'desligar')`);
                    powerBtn.innerHTML = '<i class="fas fa-power-off me-2"></i> Desligar';
                    powerBtn.classList.remove('btn-ar-success');
                    powerBtn.classList.add('btn-ar-danger');
                }
            } else {
                // Ar está desligado, esconde controles
                document.querySelectorAll('.ar-controls').forEach(el => {
                    el.style.display = 'none';
                });
                
                // Atualiza botão de power
                const powerBtn = document.getElementById('power-btn');
                if (powerBtn) {
                    powerBtn.setAttribute('onclick', `togglePower(${data.id}, 'ligar')`);
                    powerBtn.innerHTML = '<i class="fas fa-power-off me-2"></i> Ligar';
                    powerBtn.classList.remove('btn-ar-danger');
                    powerBtn.classList.add('btn-ar-success');
                }
            }
        }
    }
    
    // Atualiza timestamp
    if (data.ultimo_ping) {
        const lastUpdate = document.querySelector('.last-update');
        if (lastUpdate) {
            lastUpdate.textContent = data.ultimo_ping;
        }
    }
}

// Inicializa a verificação periódica de status
function initStatusCheck(arId, interval = 10000) {
    // Verificar status imediatamente
    checkStatus(arId);
    
    // Depois configurar verificação periódica
    const refreshTimer = setInterval(() => {
        checkStatus(arId);
    }, interval);
    
    // Armazenar o timer na window para poder cancelar depois
    window.statusRefreshTimer = refreshTimer;
    
    // Adicionar detecção de alterações feitas por outros usuários
    listenForExternalChanges(arId);
}

// Função para detectar alterações feitas por outros usuários
function listenForExternalChanges(arId) {
    // Definir um timestamp da última atualização
    window.lastUpdateTimestamp = Date.now();
    
    // Verificar se houve mudanças no banco de dados a cada 5 segundos
    setInterval(async () => {
        try {
            const url = `/painelar/ar/${arId}/status/ajax/?timestamp=${window.lastUpdateTimestamp}`;
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success && result.changed) {
                // Houve mudanças desde a última verificação
                updateInterface(result.data);
                showNotification('Configurações atualizadas por outro usuário!', 'info');
                window.lastUpdateTimestamp = Date.now();
            }
        } catch (error) {
            console.error('Erro ao verificar alterações externas:', error);
        }
    }, 5000);
}

// Função para lidar com erros de rede ou servidor
function handleConnectionError(error) {
    console.error('Erro de conexão:', error);
    showNotification(
        'Erro de conexão com o servidor. Verifique sua internet ou o status do servidor.',
        'danger'
    );
    
    // Marca a interface como offline após erro de conexão
    updateInterface({ online: false });
}
