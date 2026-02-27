// Arquivo: dashboard_controller.js
// Funções para atualizar o dashboard de forma assíncrona

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

// Função para verificar o status de todos os dispositivos
async function checkAllDevices() {
    const arCards = document.querySelectorAll('.ar-card');
    
    arCards.forEach(async (card) => {
        const arId = card.getAttribute('data-ar-id');
        if (arId) {
            await updateDeviceStatus(arId);
        }
    });
    
    showNotification('Status de todos os dispositivos atualizado');
}

// Função para verificar o status de um dispositivo específico
async function updateDeviceStatus(arId) {
    try {
        const response = await fetch(`/painelar/ar/${arId}/status/ajax/`);
        const result = await response.json();
        
        if (result.success) {
            updateCardInterface(arId, result.data);
        } else {
            // Dispositivo está offline
            updateCardInterface(arId, { online: false });
        }
        
        return result;
    } catch (error) {
        console.error('Erro ao verificar status do dispositivo:', error);
        return { success: false, message: 'Erro de conexão' };
    }
}

// Função para atualizar a interface do card com os novos dados
function updateCardInterface(arId, data) {
    const card = document.querySelector(`.ar-card[data-ar-id="${arId}"]`);
    if (!card) return;
    
    // Atualiza o status online/offline
    const statusBadge = card.querySelector('.badge');
    if (statusBadge) {
        if (data.online) {
            statusBadge.classList.remove('badge-offline');
            statusBadge.classList.add('badge-online');
            statusBadge.textContent = 'Online';
        } else {
            statusBadge.classList.remove('badge-online');
            statusBadge.classList.add('badge-offline');
            statusBadge.textContent = 'Offline';
        }
    }
    
    // Atualiza a temperatura
    if (data.temperatura !== undefined) {
        const tempElement = card.querySelector('.temperatura-display');
        if (tempElement) {
            tempElement.textContent = `${data.temperatura}°C`;
        }
    }
    
    // Atualiza a temperatura ambiente se disponível
    if (data.temperatura_ambiente !== undefined) {
        const ambientTempElement = card.querySelector('.temperatura-ambiente');
        if (ambientTempElement) {
            ambientTempElement.textContent = `${data.temperatura_ambiente}°C`;
        }
    }
    
    // Atualiza o modo
    if (data.modo_display !== undefined) {
        const modeElement = card.querySelector('.modo-display');
        if (modeElement) {
            modeElement.textContent = data.modo_display;
        }
    }
    
    // Atualiza o estado (ligado/desligado)
    if (data.estado !== undefined) {
        const stateElement = card.querySelector('.estado-display');
        if (stateElement) {
            stateElement.textContent = data.estado ? 'Ligado' : 'Desligado';
            
            if (data.estado) {
                stateElement.classList.remove('text-secondary');
                stateElement.classList.add('text-success');
            } else {
                stateElement.classList.remove('text-success');
                stateElement.classList.add('text-secondary');
            }
            
            // Atualiza o ícone
            const stateIcon = card.querySelector('.estado-icon');
            if (stateIcon) {
                if (data.estado) {
                    stateIcon.className = 'fas fa-power-off text-success estado-icon ms-1';
                } else {
                    stateIcon.className = 'fas fa-power-off text-danger estado-icon ms-1';
                }
            }
            
            // Atualiza o botão de ligar/desligar
            const powerButton = stateElement.parentElement.querySelector('button');
            if (powerButton) {
                if (data.estado) {
                    powerButton.textContent = 'Desligar';
                    powerButton.classList.remove('btn-success');
                    powerButton.classList.add('btn-danger');
                    powerButton.setAttribute('onclick', `toggleDevicePower(${data.id}, true)`);
                } else {
                    powerButton.textContent = 'Ligar';
                    powerButton.classList.remove('btn-danger');
                    powerButton.classList.add('btn-success');
                    powerButton.setAttribute('onclick', `toggleDevicePower(${data.id}, false)`);
                }
                
                // Habilita ou desabilita o botão com base no status online
                if (data.online) {
                    powerButton.removeAttribute('disabled');
                } else {
                    powerButton.setAttribute('disabled', 'disabled');
                }
            }
        }
    }
    
    // Atualiza o consumo
    if (data.consumo_atual !== undefined) {
        const consumoElement = card.querySelector('.consumo-display');
        if (consumoElement) {
            if (data.estado && data.online) {
                consumoElement.textContent = `${parseFloat(data.consumo_atual).toFixed(2)} kW/h`;
            } else {
                consumoElement.textContent = '0.00 kW/h';
            }
        }
    }
    
    // Atualiza a última verificação
    if (data.ultimo_ping) {
        const lastCheck = card.querySelector('.last-check');
        if (lastCheck) {
            lastCheck.textContent = data.ultimo_ping;
        }
    } else {
        const now = new Date();
        const timeStr = now.toLocaleTimeString();
        const lastCheck = card.querySelector('.last-check');
        if (lastCheck) {
            lastCheck.textContent = timeStr;
        }
    }
}

// Inicia a verificação periódica do status dos dispositivos
function initDashboardRefresh(interval = 30000) {
    // Atualiza imediatamente na primeira carga
    setTimeout(() => {
        checkAllDevices();
    }, 2000);
    
    // Configura atualização periódica
    setInterval(() => {
        checkAllDevices();
    }, interval);
    
    // Verifica se algum dispositivo novo foi conectado
    checkForNewDevices();
}

// Função para verificar se algum dispositivo novo foi conectado
async function checkForNewDevices() {
    try {
        const response = await fetch('/painelar/api/status/');
        const data = await response.json();
        
        // Se houve sucesso e tem novos dispositivos
        if (data.status === 'success' && data.new_devices && data.new_devices.length > 0) {
            const deviceNames = data.new_devices.map(d => d.nome).join(', ');
            showNotification(`Novos dispositivos conectados: ${deviceNames}. Atualizando...`, 'info');
            
            // Atualiza a página após um breve delay para mostrar os novos dispositivos
            setTimeout(() => {
                window.location.reload();
            }, 3000);
        }
    } catch (error) {
        console.error('Erro ao verificar novos dispositivos:', error);
    }
    
    // Verifica a cada 60 segundos
    setTimeout(checkForNewDevices, 60000);
}

// Função para ligar/desligar o ar a partir do dashboard
async function toggleDevicePower(arId, currentState) {
    try {
        const action = currentState ? 'desligar' : 'ligar';
        const url = `/painelar/ar/${arId}/${action}/ajax/`;
        
        // Primeira tentativa - mostrar feedback visual de que o comando está sendo processado
        const card = document.querySelector(`.ar-card[data-ar-id="${arId}"]`);
        if (card) {
            const powerButton = card.querySelector('.estado-display').parentElement.querySelector('button');
            if (powerButton) {
                // Desabilita o botão enquanto o comando está sendo processado
                const originalText = powerButton.textContent;
                powerButton.disabled = true;
                powerButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processando...';
                
                // Adiciona classe de processamento ao card
                card.classList.add('processing');
            }
        }
        
        // Envia o comando com retry
        let attempts = 0;
        let result = null;
        
        while (attempts < 3 && !result) {
            try {
                result = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    }
                }).then(r => {
                    if (!r.ok) {
                        throw new Error(`Erro ${r.status}: ${r.statusText}`);
                    }
                    return r.json();
                });
            } catch (error) {
                console.warn(`Tentativa ${attempts + 1} falhou: ${error.message}`);
                attempts++;
                
                if (attempts < 3) {
                    // Aguarda um tempo antes de tentar novamente (300ms, 600ms)
                    await new Promise(resolve => setTimeout(resolve, 300 * attempts));
                }
            }
        }
        
        // Restaura o estado do botão
        if (card) {
            const powerButton = card.querySelector('.estado-display').parentElement.querySelector('button');
            if (powerButton) {
                powerButton.disabled = false;
                powerButton.textContent = currentState ? 'Desligar' : 'Ligar';
                card.classList.remove('processing');
            }
        }
        
        if (result && result.success) {
            showNotification(result.message);
            updateCardInterface(arId, result.data);
        } else {
            showNotification(result?.message || 'Falha ao processar o comando. Tente novamente.', 'danger');
        }
    } catch (error) {
        console.error('Erro ao alterar estado do dispositivo:', error);
        showNotification('Erro ao processar requisição: ' + error.message, 'danger');
        
        // Restaura o estado do botão em caso de erro
        const card = document.querySelector(`.ar-card[data-ar-id="${arId}"]`);
        if (card) {
            const powerButton = card.querySelector('.estado-display').parentElement.querySelector('button');
            if (powerButton) {
                powerButton.disabled = false;
                powerButton.textContent = currentState ? 'Desligar' : 'Ligar';
                card.classList.remove('processing');
            }
        }
    }
}

// Função para obter o token CSRF
function getCsrfToken() {
    const name = 'csrftoken';
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith(name))
        ?.split('=')[1];
    return cookieValue;
}
