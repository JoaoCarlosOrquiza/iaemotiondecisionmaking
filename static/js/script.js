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
    if (startVoiceButton) {
        startVoiceButton.addEventListener('click', () => {
            alert('Iniciar diálogo por voz com a IA (Funcionalidade a ser implementada)');
        });
    }

    // Update satisfaction percentage
    function updateSatisfaction(percentage) {
        const satisfactionElement = document.getElementById('satisfaction');
        satisfactionElement.textContent = `Satisfação: ${percentage}%`;
    }

    // Simulate interaction and satisfaction update
    document.getElementById('interaction-form').addEventListener('submit', function(event) {
        event.preventDefault();
        // Simulate processing and update satisfaction
        let satisfaction = Math.floor(Math.random() * 100);
        updateSatisfaction(satisfaction);
    });
});
