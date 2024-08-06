document.addEventListener('DOMContentLoaded', function() {
    // Função para verificar se todos os campos estão preenchidos
    function checkInputs(form, inputs, submitButton, errorMessages) {
        let allFilled = true;
        inputs.forEach((field, index) => {
            if (!field.value.trim()) {
                allFilled = false;
                if (errorMessages[index]) {
                    errorMessages[index].style.display = 'block';
                }
            } else {
                if (errorMessages[index]) {
                    errorMessages[index].style.display = 'none';
                }
            }
        });
        if (allFilled) {
            submitButton.disabled = false;
            submitButton.classList.add('enabled');
        } else {
            submitButton.disabled = true;
            submitButton.classList.remove('enabled');
        }
        return allFilled;
    }

    // Configurar verificação de inputs e envio com Enter para um formulário específico
    function setupForm(formId, formErrorId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const submitButton = form.querySelector('button[type="submit"]');
        const inputs = form.querySelectorAll('input, textarea, select');
        const errorMessages = form.querySelectorAll('.error-message');
        const formError = document.getElementById(formErrorId);

        // Adiciona o evento 'input' a todos os campos do formulário
        inputs.forEach(input => {
            input.addEventListener('input', () => checkInputs(form, inputs, submitButton, errorMessages));
        });

        // Adiciona validação antes do envio do formulário
        form.addEventListener('submit', function(event) {
            if (!checkInputs(form, inputs, submitButton, errorMessages)) {
                event.preventDefault();
                if (formError) {
                    formError.textContent = 'Por favor, preencha todos os campos obrigatórios.';
                }
            }
        });

        // Permitir enviar o formulário com a tecla "Enter"
        form.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !submitButton.disabled) {
                e.preventDefault(); // Impede o comportamento padrão de envio do formulário
                form.submit();
            }
        });
    }

    // Configurar os formulários desejados
    setupForm('support-form', 'form-error');
    setupForm('continue-form', 'form-error'); // Adiciona esta linha para configurar o continue-form

    function submitFeedback(feedbackType) {
        const feedbackInput = document.getElementById('feedback');
        if (feedbackInput) {
            feedbackInput.value = feedbackType;
        }

        const formData = {
            feedback: feedbackType
        };

        fetch('/submit-feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Feedback enviado com sucesso!');
            } else {
                alert('Erro ao enviar feedback: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao enviar feedback.');
        });
    }

    window.submitFeedback = submitFeedback;

    window.toggleDetails = function() {
        var details = document.getElementById('details');
        if (details) {
            if (details.style.display === 'none') {
                details.style.display = 'block';
            } else {
                details.style.display = 'none';
            }
        }
    };

    // Código específico para o botão e menu de navegação
    const showFormButton = document.getElementById('show-form-button');
    const backButton = document.getElementById('back-button');
    const contentDiv = document.getElementById('content');
    const formContainer = document.getElementById('form-container');
    const originalContent = contentDiv.innerHTML;
    const menuToggle = document.getElementById('menu-toggle');
    const navList = document.getElementById('nav-list');

    if (showFormButton && contentDiv && formContainer) {
        showFormButton.addEventListener('click', function() {
            contentDiv.innerHTML = formContainer.innerHTML;
            showFormButton.style.display = 'none';
            backButton.style.display = 'block';
        });

        backButton.addEventListener('click', function() {
            contentDiv.innerHTML = originalContent;
            showFormButton.style.display = 'block';
            backButton.style.display = 'none';
        });
    }

    if (menuToggle && navList) {
        menuToggle.addEventListener('click', function() {
            navList.classList.toggle('active');
        });
    }
});
