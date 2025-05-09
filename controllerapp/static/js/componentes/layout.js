// Script para o layout principal

document.addEventListener("DOMContentLoaded", function () {
  // Inicialização dos Toasts para mensagens temporárias
  var toastElements = document.querySelectorAll('.toast');
  toastElements.forEach(function (toastEl) {
    var toast = new bootstrap.Toast(toastEl, {
      autohide: true,
      delay: 5000
    });
    toast.show();
  });
});