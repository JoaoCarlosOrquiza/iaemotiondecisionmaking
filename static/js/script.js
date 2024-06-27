// script.js

// Função para capturar os dados do formulário e enviar para o backend usando AJAX
function submitForm() {
    const form = document.getElementById('emotion-form');
    const formData = new FormData(form);

    fetch('/process', {
        method: 'POST',
        body: JSON.stringify(Object.fromEntries(formData)),
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('response').innerHTML = data.answer;
    })
    .catch(error => console.error('Error:', error));
}

// Outras funcionalidades já existentes no script.js
// (adicione aqui as outras funções e lógicas que já estão no seu script.js)

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('emotion-form');
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        submitForm();
    });

    const submitButton = document.getElementById('submit-button');
    const inputs = form.querySelectorAll('input, textarea, select');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            let allFilled = true;
            inputs.forEach(field => {
                if (!field.value) {
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

    // Placeholder for voice dialog functionality
    const startVoiceButton = document.getElementById('start-voice');
    startVoiceButton.addEventListener('click', () => {
        alert('Iniciar diálogo por voz com a IA (Funcionalidade a ser implementada)');
    });
});
