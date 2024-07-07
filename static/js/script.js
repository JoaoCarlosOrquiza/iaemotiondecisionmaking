document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        const submitButton = form.querySelector('button[type="submit"]');

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                let allFilled = true;
                inputs.forEach(field => {
                    if (!field.value.trim()) { // Use trim() para ignorar espaços em branco
                        allFilled = false;
                    }
                });
                if (allFilled) {
                    submitButton.disabled = false;
                    submitButton.classList.add('enabled');
                } else {
                    submitButton.disabled = true;
                    submitButton.classList.remove('enabled');
                }
            });
        });

        // Permitir enviar o formulário com a tecla "Enter"
        form.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !submitButton.disabled) {
                form.submit();
            }
        });
    });

    // Script para obter a localização do usuário
    const locationForm = document.getElementById('location-form');
    if (locationForm) {
        locationForm.addEventListener('submit', function(event) {
            event.preventDefault();
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(function(position) {
                    document.getElementById('user-location').value = position.coords.latitude + "," + position.coords.longitude;
                    event.target.submit();
                }, function(error) {
                    alert('Erro ao obter localização. Por favor, insira sua localização manualmente.');
                });
            } else {
                alert('Geolocalização não é suportada pelo seu navegador. Por favor, insira sua localização manualmente.');
            }
        });
    }

    // Função para enviar feedback via AJAX
    window.submitFeedback = function(feedback) {
        document.getElementById('feedback').value = feedback;
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "/feedback", true);
        xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    alert("Obrigado pelo seu feedback!");
                } else {
                    alert("Houve um problema ao enviar seu feedback. Por favor, tente novamente.");
                }
            }
        };
        xhr.send("feedback=" + feedback);
    };
});
