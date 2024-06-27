// Função para capturar os dados do formulário e enviar para o backend usando AJAX
function submitForm() {
    const form = document.getElementById('emotion-form');
    const formData = new FormData(form);

    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });

    fetch('/process', {
        method: 'POST',
        body: JSON.stringify(data),
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
    if (startVoiceButton) {
        startVoiceButton.addEventListener('click', () => {
            alert('Iniciar diálogo por voz com a IA (Funcionalidade a ser implementada)');
        });
    }
});
