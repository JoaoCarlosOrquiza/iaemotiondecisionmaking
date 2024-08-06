import logging
import re
from langdetect import detect  # Biblioteca para detecção de linguagem

# Lista expandida de palavras-chave sensíveis
sensitive_keywords = [
    "suicídio", "morte", "depressão", "abuso", "assédio", "violência",
    "auto-mutilação", "abuso sexual", "estupro", "tristeza extrema",
    "desespero", "ansiedade severa", "pânico", "crise emocional",
    "bullying", "transtorno de estresse pós-traumático", "PTSD",
    "transtorno alimentar", "anorexia", "bulimia", "autoestima baixa",
    "insônia", "solidão", "perda", "luto", "trauma", "isolamento",
    "abandono", "culpa", "vergonha", "autolesão", "drogas", "alcoolismo",
    "dependência", "vulnerabilidade", "medo extremo", "raiva intensa",
    "confusão mental", "desconexão", "apatia", "cansaço extremo",
    "dificuldade de concentração", "irritabilidade extrema", "insegurança",
    "tristeza prolongada", "desmotivação", "falta de propósito",
    "conflito interno", "problemas familiares", "problemas de relacionamento",
    "pressão social", "exigências acadêmicas", "pressão no trabalho"
]

support_resources = {
    "suicídio": "Ligue para o CVV (Centro de Valorização da Vida) no número 188.",
    "depressão": "Considere procurar um psicólogo ou psiquiatra. Você pode encontrar profissionais na plataforma de busca de saúde mental.",
    "violência": "Entre em contato com a Central de Atendimento à Mulher no número 180.",
    # Adicione recursos adicionais conforme necessário
}

def detect_sensitive_situations(situation_description):
    """
    Detecta palavras-chave sensíveis na descrição da situação fornecida.
    
    Args:
        situation_description (str): Descrição da situação fornecida pelo usuário.
    
    Returns:
        bool: Verdadeiro se palavras-chave sensíveis forem detectadas, falso caso contrário.
    """
    situation_description = situation_description.lower()  # Convert to lowercase for case-insensitive matching
    for keyword in sensitive_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', situation_description):
            return True
    return False

def get_local_resources(detected_keywords):
    """
    Obtém recursos locais baseados nas palavras-chave detectadas.
    
    Args:
        detected_keywords (list): Lista de palavras-chave detectadas na descrição da situação.
    
    Returns:
        list: Lista de recursos locais correspondentes às palavras-chave detectadas.
    """
    resources = []
    for keyword in detected_keywords:
        if keyword in support_resources:
            resources.append(support_resources[keyword])
    return resources

def generate_prompt(situation_description, feelings, support_reason, ia_action, user_age=None, gender_identity=None, user_region=None, user_language=None, interaction_number=1):
    """
    Gera um prompt para a IA baseado na descrição da situação e outros detalhes fornecidos.
    
    Args:
        situation_description (str): Descrição da situação fornecida pelo usuário.
        feelings (str): Sentimentos gerados pela situação.
        support_reason (str): Razão pela qual o usuário está buscando apoio.
        ia_action (str): Ação da IA solicitada pelo usuário.
        user_age (int, optional): Idade do usuário.
        gender_identity (str, optional): Identidade de gênero do usuário.
        user_region (str, optional): Região do usuário.
        user_language (str, optional): Língua do usuário.
        interaction_number (int, optional): Número da interação atual.
    
    Returns:
        str: O prompt gerado para a IA.
    """
    detected_keywords = [keyword for keyword in sensitive_keywords if re.search(r'\b' + re.escape(keyword) + r'\b', situation_description.lower())]
    
    if detected_keywords:
        resources = get_local_resources(detected_keywords)
        return (
            f"Entendo que você está passando por um momento muito difícil e sinto muito por você estar se sentindo assim. "
            f"Neste momento, é importante priorizar sua segurança e bem-estar. "
            f"Se você estiver em perigo imediato ou tendo pensamentos de suicídio, por favor, ligue para o CVV (Centro de Valorização da Vida) no número 188 ou procure ajuda médica imediatamente. "
            f"Aqui estão alguns recursos próximos a você que podem ajudar: {', '.join(resources)}.\n"
            f"Você mencionou que sente pânico ao se aproximar de pessoas, o que tem dificultado sua capacidade de conseguir um emprego formal e viver de maneira isolada. "
            f"Também mencionou sentimentos de inutilidade e pensamentos sobre a morte.\n"
            f"Situação: {situation_description}\n"
            f"Emoções: {feelings}\n"
            f"Razão do apoio: {support_reason}\n"
            f"Ação da IA: {ia_action}\n"
            f"Idade: {user_age}\n"
            f"Gênero: {gender_identity}\n"
            f"Região: {user_region}\n"
            f"Língua: {user_language}\n"
            f"Interação: {interaction_number}\n"
            f"Use Teoria e Técnicas da TCC, ACT, Psicanálise e Terapia Comportamental, e forneça decisões práticas, traduza para o dia a dia do usuário, apresente exemplos mais que as respectivas técnicas, de forma eficazes e suficientes para a situação descrita pelo usuário, utilizando uma abordagem didática.\n"
            f"Na primeira interação, priorize segurança, proteção e uma direção clara para a tomada de decisão.\n"
            f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
            f"Importante: Evite fornecer informações que não sejam baseadas em fatos ou que não tenham sido solicitadas diretamente.\n"
            f"Não invente detalhes ou forneça orientações específicas não solicitadas.\n"
            f"Mantenha suas respostas dentro dos tópicos de emoções, sentimentos, finanças e jurídico/leis conforme descrito.\n"
            f"Isso é para evitar 'alucinações', que são informações factualmente incorretas ou irrelevantes.\n"
            f"Você deve se comportar de maneira humilde e empática, reconhecendo que os humanos, com quem interage, estão buscando ajuda porque enfrentam dificuldades na tomada de decisão.\n"
            f"Evite fornecer informações ou orientações não solicitadas e, em vez disso, concentre-se em pedir esclarecimentos ou mais detalhes sobre a situação do usuário quando necessário.\n"
            f"Desta forma, você favorece a tomada de decisão do usuário, comportando-se de maneira semelhante a um humano, com sensibilidade e compreensão das limitações humanas.\n"
            f"Sempre termine suas respostas perguntando ao usuário se era isso que ele esperava e estimulando-o a interagir mais, proporcionando feedback que ajude você a melhorar.\n"
            f"Se possível, forneça exemplos práticos e contextualizados do dia a dia das relações humanas para ilustrar suas orientações.\n"
            f"Antes de enviar sua resposta, revise-a para garantir que está alinhada com as necessidades e expectativas do usuário. Pergunte a si mesmo: 'Esta resposta é útil e relevante? Posso melhorá-la de alguma forma?'\n"
        )
    else:
        return (
            f"Descrição: {situation_description}\n"
            f"Emoções: {feelings}\n"
            f"Razão do apoio: {support_reason}\n"
            f"Ação da IA: {ia_action}\n"
            f"Idade: {user_age}\n"
            f"Gênero: {gender_identity}\n"
            f"Região: {user_region}\n"
            f"Língua: {user_language}\n"
            f"Interação: {interaction_number}\n"
            f"Use Teoria e Técnicas da TCC, ACT, Psicanálise e Terapia Comportamental, e forneça decisões práticas, traduza para o dia a dia do usuário, apresente exemplos mais que as respectivas técnicas, de forma eficazes e suficientes para a situação descrita pelo usuário, utilizando uma abordagem didática.\n"
            f"Na primeira interação, priorize segurança, proteção e uma direção clara para a tomada de decisão.\n"
            f"Sempre considere as necessidades do usuário como a maior prioridade.\n"
            f"Importante: Evite fornecer informações que não sejam baseadas em fatos ou que não tenham sido solicitadas diretamente.\n"
            f"Não invente detalhes ou forneça orientações específicas não solicitadas.\n"
            f"Mantenha suas respostas dentro dos tópicos de emoções, sentimentos, finanças e jurídico/leis conforme descrito.\n"
            f"Isso é para evitar 'alucinações', que são informações factualmente incorretas ou irrelevantes.\n"
            f"Você deve se comportar de maneira humilde e empática, reconhecendo que os humanos, com quem interage, estão buscando ajuda porque enfrentam dificuldades na tomada de decisão.\n"
            f"Evite fornecer informações ou orientações não solicitadas e, em vez disso, concentre-se em pedir esclarecimentos ou mais detalhes sobre a situação do usuário quando necessário.\n"
            f"Desta forma, você favorece a tomada de decisão do usuário, comportando-se de maneira semelhante a um humano, com sensibilidade e compreensão das limitações humanas.\n"
            f"Sempre termine suas respostas perguntando ao usuário se era isso que ele esperava e estimulando-o a interagir mais, proporcionando feedback que ajude você a melhorar.\n"
            f"Se possível, forneça exemplos práticos e contextualizados do dia a dia das relações humanas para ilustrar suas orientações.\n"
            f"Antes de enviar sua resposta, revise-a para garantir que está alinhada com as necessidades e expectativas do usuário. Pergunte a si mesmo: 'Esta resposta é útil e relevante? Posso melhorá-la de alguma forma?'\n"
        )
