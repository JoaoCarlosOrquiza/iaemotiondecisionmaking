document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('emotion-form');
    const submitButton = document.getElementById('submit-button');
    const inputs = form.querySelectorAll('input, textarea');

    inputs.forEach(input => {
        input.addEventListener('input', () => {
            let allFilled = true;
            inputs.forEach(field => {
                if (!field.value) {
                    allFilled = false;
                }
            });
            submitButton.disabled = !allFilled;
        });
    });

    // Placeholder for voice dialog functionality
    const startVoiceButton = document.getElementById('start-voice');
    startVoiceButton.addEventListener('click', () => {
        alert('Iniciar diálogo por voz com a IA (Funcionalidade a ser implementada)');
    });
});
