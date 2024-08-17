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
    setupForm('continue-form', 'form-error');

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
    const originalContent = contentDiv ? contentDiv.innerHTML : '';

    if (showFormButton && contentDiv && formContainer) {
        showFormButton.addEventListener('click', function() {
            if (contentDiv && formContainer) {
                contentDiv.innerHTML = formContainer.innerHTML;
                showFormButton.style.display = 'none';
                backButton.style.display = 'block';
            }
        });

        backButton.addEventListener('click', function() {
            if (contentDiv) {
                contentDiv.innerHTML = originalContent;
                showFormButton.style.display = 'block';
                backButton.style.display = 'none';
            }
        });
    }

    if (menuToggle && navList) {
        menuToggle.addEventListener('click', function() {
            navList.classList.toggle('active');
        });
    }

    // Removido código duplicado para geolocalização, mantido apenas no JS para consistência
document.getElementById('location-form').addEventListener('submit', async function(event) {
    event.preventDefault();  // Previne o envio imediato do formulário

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            const userLocation = `${position.coords.latitude}, ${position.coords.longitude}`;
            document.getElementById('user-location').value = userLocation;

            try {
                const response = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(userLocation)}&key=YOUR_GOOGLE_PLACES_API_KEY`);
                const data = await response.json();

                if (data.status === 'OK' && data.results.length > 0) {
                    const location = data.results[0].geometry.location;

                    const latInput = document.createElement('input');
                    latInput.type = 'hidden';
                    latInput.name = 'latitude';
                    latInput.value = location.lat;

                    const lngInput = document.createElement('input');
                    lngInput.type = 'hidden';
                    lngInput.name = 'longitude';
                    lngInput.value = location.lng;

                    // Adiciona os inputs ocultos ao formulário
                    event.target.appendChild(latInput);
                    event.target.appendChild(lngInput);

                    // Agora envia o formulário com as coordenadas
                    event.target.submit();
                } else {
                    alert('Não foi possível determinar a localização. Por favor, verifique o endereço.');
                }
            } catch (error) {
                console.error('Erro ao obter a geolocalização:', error);
                alert('Ocorreu um erro ao tentar determinar sua localização.');
            }
        }, (error) => {
            alert('Erro ao obter localização. Por favor, insira sua localização manualmente.');
            event.target.submit();  // Envia o formulário mesmo com erro
        });
    } else {
        alert('Geolocalização não é suportada pelo seu navegador. Por favor, insira sua localização manualmente.');
        event.target.submit();  // Envia o formulário mesmo sem geolocalização
    }
});

    // Assegurar que links "Como Chegar" abram em nova aba de forma segura
    document.querySelectorAll('a[target="_blank"]').forEach(link => {
        link.setAttribute('rel', 'noopener noreferrer');
    });

    // Adição da funcionalidade de autocompletação
    // Recebe os termos do backend
    const terms = {{ terms | tojson | safe }};

    // Seleciona o campo de entrada e a lista de autocompletação
    const searchInput = document.getElementById('search-input');
    const autocompleteList = document.getElementById('autocomplete-list');

    searchInput.addEventListener('input', function() {
        const input = this.value.toLowerCase();
        autocompleteList.innerHTML = ''; // Limpa a lista de sugestões
        
        if (!input) return;
        
        // Filtra os termos que começam com o que foi digitado
        const suggestions = terms.filter(term => term.startsWith(input));

        // Cria os itens da lista de autocompletação
        suggestions.forEach(suggestion => {
            const item = document.createElement('li');
            item.textContent = suggestion;
            item.addEventListener('click', function() {
                searchInput.value = suggestion; // Preenche o campo de entrada com a sugestão
                autocompleteList.innerHTML = ''; // Limpa a lista
            });
            autocompleteList.appendChild(item);
        });
    });

    // Função para lidar com a resposta da busca
    function handleSearchResponse(response) {
        if (response.success) {
            // Exibir os resultados, manipulação de DOM, etc.
        } else {
            // Exibir mensagem de erro com sugestões, se disponíveis
            if (response.suggestions && response.suggestions.length > 0) {
                alert(`Erro: Tipo de profissional não reconhecido. Talvez você tenha querido dizer: ${response.suggestions.join(', ')}`);
            } else {
                alert('Erro ao buscar profissionais. Verifique sua conexão e tente novamente.');
            }
        }
    }

    // Validação e sugestão de termos no campo de busca do formulário
    const validTerms = ["psicólogo", "terapeuta", "advogado", "consultoria financeira", "ajuda legal", "médico"]; // Exemplo de termos válidos

    const professionalTypeInput = document.getElementById('professional-type');
    const autocompleteList = document.getElementById('autocomplete-list');

    professionalTypeInput.addEventListener('input', function() {
        const input = this.value.toLowerCase();
        autocompleteList.innerHTML = ''; // Limpa a lista de sugestões

        if (!input) return;

        // Filtra os termos válidos que começam com o que foi digitado
        const suggestions = validTerms.filter(term => term.startsWith(input));

        // Cria os itens da lista de autocompletação
        suggestions.forEach(suggestion => {
            const item = document.createElement('li');
            item.textContent = suggestion;
            item.addEventListener('click', function() {
                professionalTypeInput.value = suggestion; // Preenche o campo de entrada com a sugestão
                autocompleteList.innerHTML = ''; // Limpa a lista
            });
            autocompleteList.appendChild(item);
        });
    });

});
