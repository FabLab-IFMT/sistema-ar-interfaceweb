// Script personalizado para o administrador do Django

document.addEventListener('DOMContentLoaded', function() {
    // Remover qualquer seletor de tema existente para evitar conflitos
    const existingThemeToggles = document.querySelectorAll('#theme-toggle, .theme-toggle');
    existingThemeToggles.forEach(toggle => toggle.remove());
    
    // Sistema de tema claro/escuro/sistema - VERSÃO UNIFICADA
    function setupThemeSystem() {
        // Remover seletores de tema existentes antes de criar um novo
        const existingSelectors = document.querySelectorAll('.theme-selector');
        existingSelectors.forEach(selector => selector.remove());
        
        // Criar o seletor de tema
        createThemeSelector();
        
        // Aplicar o tema salvo ou padrão
        applyTheme();
        
        // Monitorar alterações no modo de cores do sistema
        if (window.matchMedia) {
            const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
            const handleColorSchemeChange = e => {
                // Somente aplicar se estiver no modo "sistema"
                if (localStorage.getItem('adminTheme') === 'system') {
                    setThemeClass(e.matches ? 'dark' : 'light');
                }
            };
            
            // Limpar listeners existentes para evitar duplicações
            if (window.themeMediaQueryListener) {
                if (colorSchemeQuery.removeEventListener) {
                    colorSchemeQuery.removeEventListener('change', window.themeMediaQueryListener);
                } else if (colorSchemeQuery.removeListener) {
                    colorSchemeQuery.removeListener(window.themeMediaQueryListener);
                }
            }
            
            // Armazenar o listener para referência futura
            window.themeMediaQueryListener = handleColorSchemeChange;
            
            // Usar o método correto de acordo com o navegador
            if (colorSchemeQuery.addEventListener) {
                colorSchemeQuery.addEventListener('change', handleColorSchemeChange);
            } else if (colorSchemeQuery.addListener) {
                colorSchemeQuery.addListener(handleColorSchemeChange);
            }
        }
    }
    
    // Criar seletor de tema
    function createThemeSelector() {
        // Criar container
        const themeSelector = document.createElement('div');
        themeSelector.id = 'theme-selector';
        themeSelector.className = 'theme-selector';
        themeSelector.innerHTML = `
            <span class="theme-label">Tema:</span>
            <div class="theme-buttons">
                <button class="theme-button" data-theme="light" title="Tema claro">
                    <i class="fas fa-sun"></i>
                </button>
                <button class="theme-button" data-theme="dark" title="Tema escuro">
                    <i class="fas fa-moon"></i>
                </button>
                <button class="theme-button" data-theme="system" title="Tema do sistema">
                    <i class="fas fa-desktop"></i>
                </button>
            </div>
        `;
        
        // Estilizar o seletor
        if (!document.getElementById('theme-selector-styles')) {
            const style = document.createElement('style');
            style.id = 'theme-selector-styles';
            style.textContent = `
                .theme-selector {
                    display: flex;
                    align-items: center;
                    margin-left: 15px;
                    background-color: rgba(255,255,255,0.1);
                    border-radius: 30px;
                    padding: 5px 10px;
                }
                
                .theme-label {
                    margin-right: 10px;
                    font-size: 12px;
                    color: white;
                    opacity: 0.9;
                }
                
                .theme-buttons {
                    display: flex;
                    gap: 5px;
                }
                
                .theme-button {
                    background: transparent;
                    border: none;
                    color: white;
                    opacity: 0.7;
                    cursor: pointer;
                    border-radius: 50%;
                    width: 26px;
                    height: 26px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }
                
                .theme-button:hover {
                    opacity: 1;
                    background-color: rgba(255,255,255,0.1);
                }
                
                .theme-button.active {
                    opacity: 1;
                    background-color: rgba(255,255,255,0.2);
                    box-shadow: 0 0 0 2px rgba(255,255,255,0.5);
                }
                
                @media (max-width: 767px) {
                    .theme-selector {
                        margin-top: 10px;
                        margin-left: 0;
                    }
                }
                
                /* Estilos para Dark Mode - CORRIGIDO PARA APLICAÇÃO COMPLETA */
                body.dark-mode {
                    --primary: #3584e4;
                    --primary-light: #5096ed; 
                    --secondary: #5096ed;
                    --accent: #f8e45c;
                    --body-bg: #1c1c1c;
                    --body-fg: #e0e0e0;
                    --header-bg: #121212;
                    --card-bg: #242424;
                    --card-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
                    --border-color: #404040;
                    --input-bg: #303030;
                    --input-color: #e0e0e0;
                    --table-header-bg: #242424;
                    background-color: #1c1c1c;
                    color: #e0e0e0;
                }
                
                body.dark-mode #header {
                    background: linear-gradient(135deg, #1a5fb4, #3584e4);
                }
                
                body.dark-mode .module h2, 
                body.dark-mode .module caption {
                    background: linear-gradient(45deg, #1a5fb4, #3584e4);
                }
                
                body.dark-mode a:link, 
                body.dark-mode a:visited {
                    color: #5096ed;
                }
                
                body.dark-mode a:hover, 
                body.dark-mode a:focus {
                    color: #78b0f2;
                }
                
                body.dark-mode .breadcrumbs, 
                body.dark-mode .module, 
                body.dark-mode .dashboard .app-list, 
                body.dark-mode .form-row, 
                body.dark-mode .submit-row,
                body.dark-mode #changelist-filter {
                    background-color: #242424;
                }
                
                body.dark-mode input, 
                body.dark-mode textarea, 
                body.dark-mode select {
                    background-color: #303030;
                    border-color: #404040;
                    color: #e0e0e0;
                }
                
                body.light-mode {
                    --primary: #1a5fb4;
                    --primary-light: #3584e4;
                    --secondary: #2a76dd;
                    --accent: #f5c211;
                    --body-bg: #f6f9fc;
                    --body-fg: #333333;
                    --header-bg: var(--primary);
                    --card-bg: #ffffff;
                    --card-shadow: 0 4px 10px rgba(26, 95, 180, 0.1);
                    --border-color: #e2e8f0;
                    --input-bg: #ffffff;
                    --input-color: #333333;
                    --table-header-bg: #f8fafc;
                    background-color: #f6f9fc;
                    color: #333333;
                }
                
                /* Correções para calendário e widgets de data no modo escuro */
                body.dark-mode .calendarbox, 
                body.dark-mode .clockbox,
                body.dark-mode .calendar {
                    background-color: #242424;
                    border-color: #404040;
                }
                
                body.dark-mode .calendar caption {
                    background: #1a5fb4;
                }
                
                body.dark-mode .calendar td {
                    background-color: #242424;
                    color: #e0e0e0;
                }
                
                body.dark-mode .calendar td.selected a {
                    background-color: #3584e4;
                    color: white;
                }
                
                body.dark-mode .paginator {
                    background-color: #242424;
                    color: #e0e0e0;
                }
                
                /* Correção para elementos que mudam de cor quando o mouse passa em cima */
                body.dark-mode tbody tr:hover td, 
                body.dark-mode tbody tr:hover th {
                    background-color: #2b2b2b;
                }
            `;
            document.head.appendChild(style);
        }
        
        // Adicionar ao DOM
        const userTools = document.getElementById('user-tools');
        if (userTools) {
            userTools.appendChild(themeSelector);
            
            // Adicionar event listeners
            const buttons = themeSelector.querySelectorAll('.theme-button');
            buttons.forEach(button => {
                button.addEventListener('click', function() {
                    const theme = this.dataset.theme;
                    localStorage.setItem('adminTheme', theme);
                    
                    // Remover tema atual do localStorage anterior (compatibilidade)
                    localStorage.removeItem('theme');
                    
                    // Aplicar o tema
                    applyTheme();
                    
                    // Atualizar botões ativos
                    buttons.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                });
            });
        }
    }
    
    // Aplicar o tema baseado na preferência salva
    function applyTheme() {
        // Primeiro verifica se existe configuração antiga para compatibilidade
        const oldTheme = localStorage.getItem('theme');
        if (oldTheme && !localStorage.getItem('adminTheme')) {
            // Migra a configuração antiga para a nova
            if (oldTheme === 'dark') {
                localStorage.setItem('adminTheme', 'dark');
            } else if (oldTheme === 'light') {
                localStorage.setItem('adminTheme', 'light');
            } else {
                localStorage.setItem('adminTheme', 'system');
            }
            // Limpa a configuração antiga
            localStorage.removeItem('theme');
        }
        
        const savedTheme = localStorage.getItem('adminTheme') || 'system';
        const buttons = document.querySelectorAll('.theme-button');
        
        // Ativar o botão correto
        buttons.forEach(button => {
            button.classList.toggle('active', button.dataset.theme === savedTheme);
        });
        
        // Aplicar o tema
        if (savedTheme === 'system') {
            // Seguir preferência do sistema
            const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
            setThemeClass(prefersDark ? 'dark' : 'light');
        } else {
            // Usar tema escolhido
            setThemeClass(savedTheme);
        }
    }
    
    // Definir classe de tema no body - IMPLEMENTAÇÃO ROBUSTA
    function setThemeClass(theme) {
        // Remover todas as classes de tema primeiro
        document.body.classList.remove('dark-mode', 'light-mode', 'dark-theme', 'light-theme');
        
        // Adicionar a classe de tema apropriada (incluindo classes de compatibilidade)
        document.body.classList.add(theme + '-mode');
        document.body.classList.add(theme + '-theme'); // Para compatibilidade com outros scripts
        
        // Definir valor do data-theme para compatibilidade com CSS/JS antigos
        document.body.dataset.theme = theme;
        
        // Atualizar o html também para permitir seletores :root[data-theme="dark"]
        document.documentElement.dataset.theme = theme;
        
        // Ajustes específicos para cada tema
        if (theme === 'dark') {
            applyDarkModeAdjustments();
        } else {
            removeDarkModeAdjustments(); // Importante para remover ajustes do modo escuro
        }
        
        // Disparar evento para notificar outros scripts da mudança de tema
        const event = new CustomEvent('themeChanged', { detail: { theme } });
        document.dispatchEvent(event);
    }
    
    // Ajustes específicos para o modo escuro
    function applyDarkModeAdjustments() {
        // Corrigir ícones e imagens no modo escuro
        document.querySelectorAll('.datetimeshortcuts a img, .inline-deletelink img, .toggle-handler img').forEach(img => {
            img.style.filter = 'invert(1)';
        });
        
        // Corrigir contraste em elementos específicos 
        document.querySelectorAll('.paginator a, .paginator .this-page').forEach(el => {
            el.style.border = '1px solid #555';
        });
        
        // Ajustar cores em outros elementos que possam precisar
        document.querySelectorAll('input, select, textarea').forEach(input => {
            input.style.borderColor = '#404040';
            input.style.backgroundColor = input.type === 'text' || input.tagName === 'SELECT' || input.tagName === 'TEXTAREA' ? '#303030' : '';
            input.style.color = input.type === 'text' || input.tagName === 'SELECT' || input.tagName === 'TEXTAREA' ? '#e0e0e0' : '';
        });
        
        // Corrigir data widgets
        document.querySelectorAll('.calendarbox, .clockbox').forEach(box => {
            box.style.backgroundColor = '#242424';
            box.style.borderColor = '#404040';
        });
        
        // Força atualização do CSS de modo escuro
        document.querySelectorAll('link[href*="themes.css"]').forEach(link => {
            const href = link.getAttribute('href');
            const timestamp = Date.now();
            link.setAttribute('href', href.split('?')[0] + '?' + timestamp);
        });
    }
    
    // Remover ajustes do modo escuro
    function removeDarkModeAdjustments() {
        document.querySelectorAll('.datetimeshortcuts a img, .inline-deletelink img, .toggle-handler img').forEach(img => {
            img.style.filter = '';
        });
        
        document.querySelectorAll('.paginator a, .paginator .this-page').forEach(el => {
            el.style.border = '';
        });
        
        document.querySelectorAll('input, select, textarea').forEach(input => {
            input.style.borderColor = '';
            input.style.backgroundColor = '';
            input.style.color = '';
        });
        
        document.querySelectorAll('.calendarbox, .clockbox').forEach(box => {
            box.style.backgroundColor = '';
            box.style.borderColor = '';
        });
    }
    
    // Função para adicionar ícones às mensagens do admin
    function addIconsToMessages() {
        const messages = document.querySelectorAll('.messagelist li');
        
        messages.forEach(message => {
            let icon = '';
            
            if (message.classList.contains('success')) {
                icon = '<i class="fas fa-check-circle" style="margin-right: 10px;"></i>';
            } else if (message.classList.contains('error')) {
                icon = '<i class="fas fa-times-circle" style="margin-right: 10px;"></i>';
            } else if (message.classList.contains('warning')) {
                icon = '<i class="fas fa-exclamation-triangle" style="margin-right: 10px;"></i>';
            } else if (message.classList.contains('info')) {
                icon = '<i class="fas fa-info-circle" style="margin-right: 10px;"></i>';
            }
            
            if (icon && !message.innerHTML.includes('fa-')) {
                message.innerHTML = icon + message.innerHTML;
            }
        });
    }
    
    // Função para adicionar animação aos itens de lista
    function animateListItems() {
        const listItems = document.querySelectorAll('#changelist-form .row1, #changelist-form .row2');
        
        listItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(10px)';
            item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, 50 * index);
        });
    }

    // Melhorar a experiência de visualização de imagens
    function enhanceImagePreview() {
        document.querySelectorAll('.field-image img, .field-imagem img, .field-imagem_do_material img, .file-upload img').forEach(img => {
            // Evitar aplicar transformações duplicadas
            if (img.dataset.enhanced) return;
            img.dataset.enhanced = true;
            
            img.style.maxHeight = '150px';
            img.style.borderRadius = '8px';
            img.style.cursor = 'pointer';
            img.style.transition = 'transform 0.3s';
            
            img.addEventListener('click', function() {
                // Criar modal para visualização da imagem
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100%';
                modal.style.height = '100%';
                modal.style.backgroundColor = 'rgba(0,0,0,0.9)';
                modal.style.display = 'flex';
                modal.style.alignItems = 'center';
                modal.style.justifyContent = 'center';
                modal.style.zIndex = '9999';
                
                const modalImg = document.createElement('img');
                modalImg.src = this.src;
                modalImg.style.maxWidth = '90%';
                modalImg.style.maxHeight = '90%';
                modalImg.style.borderRadius = '8px';
                modalImg.style.boxShadow = '0 4px 20px rgba(0,0,0,0.5)';
                
                // Botão para fechar o modal
                const closeBtn = document.createElement('button');
                closeBtn.innerHTML = '&times;';
                closeBtn.style.position = 'absolute';
                closeBtn.style.top = '20px';
                closeBtn.style.right = '20px';
                closeBtn.style.background = 'rgba(255,255,255,0.2)';
                closeBtn.style.border = 'none';
                closeBtn.style.color = 'white';
                closeBtn.style.fontSize = '24px';
                closeBtn.style.width = '40px';
                closeBtn.style.height = '40px';
                closeBtn.style.borderRadius = '50%';
                closeBtn.style.cursor = 'pointer';
                
                modal.appendChild(modalImg);
                modal.appendChild(closeBtn);
                document.body.appendChild(modal);
                
                const closeModal = () => modal.remove();
                modal.addEventListener('click', e => {
                    if (e.target === modal) closeModal();
                });
                closeBtn.addEventListener('click', closeModal);
            });
        });
    }
    
    // Adicionar classes de status para badges
    function addStatusBadges() {
        document.querySelectorAll('td.field-status, td.field-situacao').forEach(cell => {
            if (cell.querySelector('.status-badge')) return; // Evitar duplicação
            
            const status = cell.textContent.trim().toLowerCase();
            const badgeClass = status.includes('ativ') ? 'status-active' : 
                              status.includes('desativ') ? 'status-inactive' : 
                              status.includes('pend') ? 'status-pending' : '';
            
            if (badgeClass) {
                cell.innerHTML = `<span class="status-badge ${badgeClass}">${cell.textContent.trim()}</span>`;
            }
        });
    }
    
    // Converter checkboxes boolean para switch visual
    document.querySelectorAll('td.field-ativo, td.field-disponivel, td.field-destaque, td.field-publicado, td.field-mostrar_na_home').forEach(cell => {
        const img = cell.querySelector('img');
        if (img) {
            const isChecked = img.alt.toLowerCase().includes('true');
            cell.innerHTML = `
                <div style="text-align: center">
                    <label class="switch-button">
                        <input type="checkbox" disabled ${isChecked ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
            `;
        }
    });
    
    // Adicionar feedback visual quando uma linha é clicada
    document.querySelectorAll('tbody tr').forEach(row => {
        row.addEventListener('click', function(e) {
            // Não disparar quando clica em links ou checkboxes
            if (e.target.tagName === 'A' || e.target.tagName === 'INPUT') return;
            
            this.style.backgroundColor = '#e0f2fe';
            setTimeout(() => {
                this.style.backgroundColor = '';
            }, 200);
        });
    });

    // Corrigir problemas de layout específicos
    function fixLayoutIssues() {
        // Corrigir espaçamento de elementos
        document.querySelectorAll('.form-row').forEach(row => {
            row.style.margin = '0';
        });
        
        // Corrigir inputs inline
        document.querySelectorAll('.vDateField, .vTimeField').forEach(field => {
            field.style.width = 'auto';
            field.style.minWidth = '100px';
        });
        
        // Garantir que o cabeçalho tenha z-index suficiente
        const header = document.getElementById('header');
        if (header) header.style.zIndex = '1000';
        
        // Corrigir problema com os botões de seletor
        document.querySelectorAll('.selector-add, .selector-remove').forEach(button => {
            if (button.style.backgroundImage) {
                // Remover estilo inline que causa problemas no modo escuro
                button.style.backgroundImage = 'none';
                button.innerHTML = button.classList.contains('selector-add') ? '→' : '←';
                button.style.fontSize = '18px';
                button.style.fontWeight = 'bold';
            }
        });
    }
    
    // Corrigir ícones na página de calendário
    function fixCalendarIcons() {
        document.querySelectorAll('.calendarnav-previous, .calendarnav-next').forEach(link => {
            const img = link.querySelector('img');
            if (img) {
                const icon = document.createElement('span');
                icon.innerHTML = link.classList.contains('calendarnav-previous') ? '&larr;' : '&rarr;';
                icon.style.fontSize = '18px';
                link.replaceChild(icon, img);
            }
        });
    }
    
    // Executar principais funções - ORDEM CORRIGIDA E UNIFICADA
    setupThemeSystem(); // Primeiro configurar o tema
    
    // Depois aplicar outras melhorias
    addIconsToMessages();
    animateListItems();
    enhanceImagePreview();
    addStatusBadges();
    fixLayoutIssues();
    fixCalendarIcons();
    
    // Adicionar mais funcionalidades conforme necessário

    // Adicionar efeitos de visualização de imagem mais divertidos
    document.querySelectorAll('.field-image img, .field-imagem_do_material img, .field-imagem img, .file-upload img').forEach(img => {
        // Adicionar borda arredondada e efeitos às imagens
        img.style.borderRadius = '12px';
        img.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
        img.style.transition = 'all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
        
        // Efeito de hover
        img.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.05) rotate(2deg)';
            this.style.boxShadow = '0 15px 25px rgba(0,0,0,0.15)';
        });
        
        img.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0)';
            this.style.boxShadow = '0 10px 20px rgba(0,0,0,0.1)';
        });
        
        // Modal de visualização animado
        img.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.zIndex = '9999';
            modal.style.opacity = '0';
            modal.style.transition = 'opacity 0.3s';
            
            const modalImg = document.createElement('img');
            modalImg.src = this.src;
            modalImg.style.maxWidth = '90%';
            modalImg.style.maxHeight = '90%';
            modalImg.style.borderRadius = '12px';
            modalImg.style.boxShadow = '0 20px 40px rgba(0,0,0,0.4)';
            modalImg.style.transform = 'scale(0.8) rotate(-3deg)';
            modalImg.style.transition = 'transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
            
            // Adicionar botão para baixar a imagem
            const downloadBtn = document.createElement('a');
            downloadBtn.href = this.src;
            downloadBtn.download = 'imagem';
            downloadBtn.style.position = 'absolute';
            downloadBtn.style.bottom = '30px';
            downloadBtn.style.padding = '10px 20px';
            downloadBtn.style.backgroundColor = '#7c3aed';
            downloadBtn.style.color = 'white';
            downloadBtn.style.borderRadius = '30px';
            downloadBtn.style.textDecoration = 'none';
            downloadBtn.style.fontWeight = 'bold';
            downloadBtn.style.boxShadow = '0 4px 10px rgba(0,0,0,0.2)';
            downloadBtn.style.transition = 'all 0.3s';
            downloadBtn.textContent = '⬇️ Baixar Imagem';
            downloadBtn.style.opacity = '0';
            downloadBtn.style.transform = 'translateY(20px)';
            
            downloadBtn.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#6d28d9';
                this.style.transform = 'translateY(-3px)';
            });
            
            downloadBtn.addEventListener('mouseleave', function() {
                this.style.backgroundColor = '#7c3aed';
                this.style.transform = 'translateY(0)';
            });
            
            modal.appendChild(modalImg);
            modal.appendChild(downloadBtn);
            document.body.appendChild(modal);
            
            // Animar entrada
            setTimeout(() => {
                modal.style.opacity = '1';
                modalImg.style.transform = 'scale(1) rotate(0)';
                setTimeout(() => {
                    downloadBtn.style.opacity = '1';
                    downloadBtn.style.transform = 'translateY(0)';
                }, 300);
            }, 10);
            
            // Fechar modal ao clicar
            modal.addEventListener('click', (e) => {
                if (e.target !== downloadBtn) {
                    modalImg.style.transform = 'scale(0.8) rotate(3deg)';
                    downloadBtn.style.opacity = '0';
                    downloadBtn.style.transform = 'translateY(20px)';
                    modal.style.opacity = '0';
                    setTimeout(() => {
                        modal.remove();
                    }, 300);
                }
            });
        });
    });
    
    // Easter egg - mostrar um emoji na tela quando digitamos "fablab"
    let secretCode = '';
    document.addEventListener('keydown', function(e) {
        secretCode += e.key.toLowerCase();
        secretCode = secretCode.slice(-6); // Manter apenas os últimos 6 caracteres
        
        if (secretCode === 'fablab') {
            const emoji = document.createElement('div');
            emoji.textContent = '🚀';
            emoji.style.position = 'fixed';
            emoji.style.fontSize = '100px';
            emoji.style.top = '50%';
            emoji.style.left = '50%';
            emoji.style.transform = 'translate(-50%, -50%)';
            emoji.style.zIndex = '9999';
            document.body.appendChild(emoji);
            
            setTimeout(() => emoji.remove(), 1000);
        }
    });
    
    // Animação para botões de filtro laterais - torná-los mais divertidos
    document.querySelectorAll('#changelist-filter li').forEach((item, index) => {
        item.style.transition = 'all 0.3s';
        item.style.transformOrigin = 'left';
        item.style.transitionDelay = (index * 0.05) + 's';
        
        item.addEventListener('mouseenter', function() {
            this.style.transform = 'translateX(5px) scale(1.02)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.transform = 'translateX(0) scale(1)';
        });
    });
    
    // Adicionar efeito de digitação para títulos de cabeçalho de seções
    document.querySelectorAll('fieldset h2, .module h2').forEach(h2 => {
        const originalText = h2.textContent;
        h2.textContent = '';
        
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                typeEffect(h2, originalText);
                observer.disconnect();
            }
        }, {threshold: 0.5});
        
        observer.observe(h2);
    });
    
    function typeEffect(element, text) {
        let i = 0;
        const timer = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(timer);
            }
        }, 50);
    }
    
    // Adicionar "curtida" para itens da lista
    document.querySelectorAll('#changelist tbody tr').forEach(row => {
        const firstCell = row.querySelector('td:not(.action-checkbox)');
        if (firstCell) {
            const likeBtn = document.createElement('span');
            likeBtn.innerHTML = '❤️';
            likeBtn.style.marginRight = '8px';
            likeBtn.style.cursor = 'pointer';
            likeBtn.style.opacity = '0.2';
            likeBtn.style.transition = 'all 0.3s';
            likeBtn.style.fontSize = '14px';
            
            let liked = false;
            likeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                liked = !liked;
                if (liked) {
                    likeBtn.style.opacity = '1';
                    likeBtn.style.transform = 'scale(1.3)';
                    const hearts = createHeartBurst(likeBtn);
                    setTimeout(() => {
                        likeBtn.style.transform = 'scale(1)';
                    }, 300);
                } else {
                    likeBtn.style.opacity = '0.2';
                }
            });
            
            // Inserir antes do primeiro conteúdo
            if (firstCell.firstChild) {
                firstCell.insertBefore(likeBtn, firstCell.firstChild);
            } else {
                firstCell.appendChild(likeBtn);
            }
        }
    });
    
    function createHeartBurst(element) {
        const rect = element.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        
        for (let i = 0; i < 5; i++) {
            const heart = document.createElement('div');
            heart.innerHTML = '❤️';
            heart.style.position = 'fixed';
            heart.style.left = centerX + 'px';
            heart.style.top = centerY + 'px';
            heart.style.transform = 'translate(-50%, -50%) scale(0.5)';
            heart.style.opacity = '0.8';
            heart.style.zIndex = '9999';
            heart.style.pointerEvents = 'none';
            document.body.appendChild(heart);
            
            const angle = Math.random() * Math.PI * 2;
            const distance = 20 + Math.random() * 30;
            const destX = centerX + Math.cos(angle) * distance;
            const destY = centerY + Math.sin(angle) * distance;
            
            const animation = heart.animate([
                { transform: 'translate(-50%, -50%) scale(0.5)', opacity: 0.8 },
                { transform: `translate(${destX - centerX}px, ${destY - centerY - 20}px) scale(0.2)`, opacity: 0 }
            ], {
                duration: 700 + Math.random() * 300,
                easing: 'cubic-bezier(0.175, 0.885, 0.32, 1.275)'
            });
            
            animation.onfinish = () => heart.remove();
        }
    }

    // Correção para ícones FontAwesome
    function fixFontAwesomeIcons() {
        document.querySelectorAll('.fa, .fas, .far, .fal, .fab').forEach(icon => {
            // Garantir que os ícones FontAwesome estão com as classes corretas
            if (icon.classList.contains('fa')) {
                icon.classList.add('fas');
            }
        });
    }
    
    // Melhorar a visualização de imagens
    document.querySelectorAll('.field-image img, .file-upload img').forEach(img => {
        img.style.maxHeight = '150px';
        img.style.borderRadius = '4px';
        img.style.transition = 'transform 0.2s';
        
        img.addEventListener('click', function() {
            const modal = document.createElement('div');
            modal.style.position = 'fixed';
            modal.style.top = '0';
            modal.style.left = '0';
            modal.style.width = '100%';
            modal.style.height = '100%';
            modal.style.backgroundColor = 'rgba(0,0,0,0.8)';
            modal.style.display = 'flex';
            modal.style.alignItems = 'center';
            modal.style.justifyContent = 'center';
            modal.style.zIndex = '9999';
            
            const modalImg = document.createElement('img');
            modalImg.src = this.src;
            modalImg.style.maxWidth = '90%';
            modalImg.style.maxHeight = '90%';
            modalImg.style.borderRadius = '4px';
            
            modal.appendChild(modalImg);
            document.body.appendChild(modal);
            
            modal.addEventListener('click', () => {
                modal.remove();
            });
        });
    });
    
    // Executar correções
    fixFontAwesomeIcons();
});
