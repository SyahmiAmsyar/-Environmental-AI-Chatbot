from flask import Flask, request, jsonify, render_template
import requests
import json
import re

app = Flask(__name__)

# --- Ollama API Configuration ---
OLLAMA_URL = "http://localhost:11434/api/generate"
# --------------------------------

@app.route("/")
def index():
    """Renders the main HTML chat interface."""
    return render_template("index.html")

def call_ollama_api(prompt):
    """
    Calls the local Ollama API and returns the response text.
    """
    payload = {
        "model": "deepseek-v3.1:671b-cloud",
        "prompt": prompt,
        "stream": True
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
        bot_reply = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                data = json.loads(line)
                bot_reply += data.get("response", "")
                if data.get("done", False):
                    break
        return {"text": bot_reply.strip()}
    except Exception as e:
        print(f"Error: {e}")
        return {"text": "Error: Could not reach the Ollama AI service."}

def detect_question_type(user_message):
    """
    Intelligently detects the type of question to determine response format.
    Enhanced with better pattern matching and context awareness.
    """
    message_lower = user_message.lower().strip()
    
    # Remove common question words for cleaner matching
    clean_message = re.sub(r'\b(what|how|why|when|where|who|can|could|would|should|do|does|is|are|the|a|an)\b', '', message_lower)
    clean_message = ' '.join(clean_message.split())  # Remove extra spaces
    
    print(f"Original: {user_message}")
    print(f"Cleaned: {clean_message}")
    
    # Score-based detection for better accuracy
    scores = {
        'tips': 0,
        'step_by_step': 0,
        'causes': 0,
        'prevention': 0,
        'comparison': 0,
        'effects': 0,
        'educational': 0,
        'actionable': 0
    }
    
    # === PATTERN MATCHING WITH SCORING ===
    
    # Tips and practical advice
    tips_patterns = [
        r'\btip', r'\badvice', r'\bpractical', r'\beasy ways', r'\bsimple ways',
        r'\bquick tips', r'\bhelpful tips', r'\beffective tips', r'\buseful tips',
        r'give me tips', r'provide tips', r'share tips', r'suggest tips'
    ]
    
    # Step-by-step guides
    step_patterns = [
        r'step by step', r'how do i', r'how to start', r'how to begin',
        r'guide to', r'process to', r'procedure for', r'steps for',
        r'how can i', r'how should i', r'walk me through', r'tutorial'
    ]
    
    # Causes & reasons
    causes_patterns = [
        r'^why', r'\bwhy ', r'causes of', r'reasons for', r'reasons behind',
        r'what causes', r'what leads to', r'what results in', r'how does happen',
        r'origin of', r'source of', r'root cause'
    ]
    
    # Prevention & solutions
    prevention_patterns = [
        r'how to prevent', r'how to reduce', r'how to stop', r'how to avoid',
        r'how to minimize', r'how to control', r'prevention of', r'solutions for',
        r'solutions to', r'ways to prevent', r'measures to prevent',
        r'how to deal with', r'how to address', r'how to solve'
    ]
    
    # Effects & impacts
    effects_patterns = [
        r'effects of', r'impact of', r'consequences of', r'results of',
        r'what happens when', r'what are the effects', r'how does affect',
        r'implications of', r'ramifications of'
    ]
    
    # Educational & definitions
    educational_patterns = [
        r'^what is', r'^define', r'^explain', r'meaning of',
        r'definition of', r'what does mean', r'tell me about',
        r'can you explain', r'could you define'
    ]
    
    # Specific actionable how-to
    actionable_patterns = [
        r'how to make', r'how to create', r'how to build', r'how to set up',
        r'how to implement', r'how to use', r'how to apply', r'how to do'
    ]
    
    # Calculate scores based on pattern matches
    for pattern in tips_patterns:
        if re.search(pattern, message_lower):
            scores['tips'] += 2
    
    for pattern in step_patterns:
        if re.search(pattern, message_lower):
            scores['step_by_step'] += 3
    
    for pattern in causes_patterns:
        if re.search(pattern, message_lower):
            scores['causes'] += 3
    
    for pattern in prevention_patterns:
        if re.search(pattern, message_lower):
            scores['prevention'] += 3
    
    for pattern in effects_patterns:
        if re.search(pattern, message_lower):
            scores['effects'] += 2
    
    for pattern in educational_patterns:
        if re.search(pattern, message_lower):
            scores['educational'] += 3
    
    for pattern in actionable_patterns:
        if re.search(pattern, message_lower):
            scores['actionable'] += 2
    
    # Special case: "how to" without prevention context → actionable
    if 'how to' in message_lower and scores['prevention'] == 0:
        scores['actionable'] += 2
    
    # Special case: Questions starting with "what is" are strongly educational
    if user_message.lower().startswith('what is'):
        scores['educational'] += 5
    
    # Special case: Questions starting with "why" are strongly causes
    if user_message.lower().startswith('why'):
        scores['causes'] += 5
    
    # Special case: Questions starting with "how to prevent" are strongly prevention
    if 'how to prevent' in message_lower:
        scores['prevention'] += 5
    
    # Find the highest scoring category
    max_score = max(scores.values())
    best_categories = [cat for cat, score in scores.items() if score == max_score]
    
    print(f"Detection scores: {scores}")
    print(f"Best categories: {best_categories}")
    
    # Priority resolution for ties
    priority_order = ['prevention', 'causes', 'step_by_step', 'actionable', 'tips', 'effects', 'educational']
    
    for category in priority_order:
        if category in best_categories:
            final_category = category
            break
    else:
        final_category = 'educational'  # Default fallback
    
    print(f"Final detected type: {final_category}")
    return final_category

def get_prompt_by_category(question_type, user_message):
    """
    Returns the appropriate prompt template based on detected question type.
    """
    
    if question_type == "tips":
        return f"""You are EcoGuard, an environmental expert. Provide PRACTICAL, ACTIONABLE tips.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

PRACTICAL TIPS:

1. [Specific, actionable tip with environmental benefit]
2. [Easy-to-implement practical suggestion]
3. [Cost-effective environmental action]
4. [Daily habit change with positive impact]
5. [Community-level environmental action]

CRITICAL RULES:
- Start with "PRACTICAL TIPS:" exactly as shown
- Use numbered list 1-5 ONLY
- Each tip must be practical and implementable
- Focus on environmental benefits
- No explanations after tips
- Maximum 15 words per tip
- Do NOT add concluding sentences
- Do NOT use bullet points, only numbers

Now answer the user's question in the exact format above:"""

    elif question_type == "step_by_step":
        return f"""You are EcoGuard, an environmental expert. Provide a CLEAR STEP-BY-STEP guide.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

STEP-BY-STEP GUIDE:

Step 1: [First essential action - gather materials/preparation]
Step 2: [Second action - initial setup/implementation]
Step 3: [Third action - main process/execution]
Step 4: [Fourth action - monitoring/adjustment]
Step 5: [Fifth action - completion/maintenance]

CRITICAL RULES:
- Start with "STEP-BY-STEP GUIDE:" exactly as shown
- Use "Step X:" format ONLY
- Each step should be sequential and actionable
- Include environmental considerations
- Do NOT add extra text or explanations
- Make steps practical and implementable

Now answer the user's question in the exact format above:"""

    elif question_type == "causes":
        return f"""You are EcoGuard, an environmental expert. Explain CAUSES and REASONS.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

PRIMARY CAUSES:

• [Main direct cause with environmental context]
• [Secondary contributing factor]
• [Underlying systemic cause]

IMMEDIATE TRIGGERS:

• [Recent/current triggering factors]
• [Human activity contributions]
• [Natural factor influences]

ENVIRONMENTAL MECHANISM:

[Brief explanation of how these causes create environmental impact]

CRITICAL RULES:
- Use EXACT section headers: PRIMARY CAUSES:, IMMEDIATE TRIGGERS:, ENVIRONMENTAL MECHANISM:
- Use bullet points (•) ONLY in first two sections
- Focus on environmental causation
- Explain the environmental mechanism clearly
- Do NOT add extra sections

Now answer the user's question in the exact format above:"""

    elif question_type == "prevention":
        return f"""You are EcoGuard, an environmental expert. Provide PREVENTION SOLUTIONS.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

PREVENTION METHODS:

1. [Proactive prevention strategy]
2. [Early intervention approach]
3. [Systemic solution implementation]
4. [Community-level prevention]
5. [Policy/regulation approach]

EFFECTIVENESS:

[Brief note on which methods are most effective and why]

CRITICAL RULES:
- Start with "PREVENTION METHODS:" exactly as shown
- Use numbered list 1-5 ONLY
- Focus on prevention rather than cure
- Include both individual and systemic solutions
- Do NOT add extra text after methods
- Keep effectiveness note concise

Now answer the user's question in the exact format above:"""

    elif question_type == "actionable":
        return f"""You are EcoGuard, an environmental expert. Provide ACTIONABLE IMPLEMENTATION.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

ACTIONABLE STEPS:

✅ [First concrete action to take]
✅ [Second specific implementation step]
✅ [Third practical execution step]
✅ [Fourth measurable action]
✅ [Fifth sustainable practice]

RESOURCES NEEDED:

• [Materials/tools required]
• [Time investment]
• [Skill level needed]

ENVIRONMENTAL BENEFIT:

[Specific environmental impact of implementation]

CRITICAL RULES:
- Start with "ACTIONABLE STEPS:" exactly as shown
- Use checkmarks (✅) for steps
- Include specific resource requirements
- Focus on concrete, measurable actions
- Specify environmental benefits clearly

Now answer the user's question in the exact format above:"""

    elif question_type == "effects":
        return f"""You are EcoGuard, an environmental expert. Explain EFFECTS and IMPACTS.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

IMMEDIATE EFFECTS:

• [Short-term environmental consequences]
• [Direct ecosystem impacts]
• [Initial human health effects]

LONG-TERM IMPACTS:

• [Sustainable development consequences]
• [Biodiversity implications]
• [Climate system changes]

ECOSYSTEM CONSEQUENCES:

[How effects cascade through environmental systems]

CRITICAL RULES:
- Use EXACT section headers: IMMEDIATE EFFECTS:, LONG-TERM IMPACTS:, ECOSYSTEM CONSEQUENCES:
- Use bullet points (•) ONLY in first two sections
- Distinguish between short and long-term effects
- Focus on environmental and ecosystem impacts
- Explain consequence chains clearly

Now answer the user's question in the exact format above:"""

    else:  # Educational format (DEFAULT)
        return f"""You are EcoGuard, an environmental expert. Provide COMPREHENSIVE EDUCATIONAL explanation.

QUESTION: {user_message}

RESPONSE FORMAT - FOLLOW EXACTLY:

🌱 CORE CONCEPT:
• [Fundamental definition]
• [Key characteristics]
• [Environmental significance]

🔹 KEY COMPONENTS:
• [Main elements/aspects]
• [Related environmental factors]
• [System interactions]

⚡ PRIMARY SOURCES:
• [Major contributing factors]
• [Human activity sources]
• [Natural sources]

⚠️ ENVIRONMENTAL IMPACTS:
• [Ecosystem effects]
• [Biodiversity consequences]
• [Climate implications]

💡 SUSTAINABLE SOLUTIONS:
• [Conservation approaches]
• [Mitigation strategies]
• [Adaptation methods]

CRITICAL RULES:
- Use EXACT section headers with emojis as shown
- Use bullet points (•) for ALL content
- 3 bullet points per section MAXIMUM
- Focus on environmental aspects throughout
- No markdown, bold, or extra formatting
- No introductory or concluding sentences
- Do NOT add any other sections

Now answer the user's question in the exact format above:"""

@app.route("/generate_content", methods=["POST"])
def generate_content():
    """
    Handles user queries, calls the Ollama API, and returns the response.
    """
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400

    data = request.get_json()
    user_message = data.get("message")

    if not user_message:
        return jsonify({"error": "Missing 'message' field"}), 400

    # Enhanced question type detection
    question_type = detect_question_type(user_message)
    
    # Get appropriate prompt template
    prompt = get_prompt_by_category(question_type, user_message)
    
    print(f"Question type: {question_type}")
    print(f"Sending prompt to Ollama...")
    
    response_data = call_ollama_api(prompt)
    
    # Enhanced post-processing
    if response_data["text"]:
        response_data["text"] = enhanced_formatting_enforcement(
            response_data["text"], 
            question_type, 
            user_message
        )
    
    print(f"Response generated successfully")
    return jsonify(response_data)

def enhanced_formatting_enforcement(text, question_type, user_message):
    """
    Enhanced formatting enforcement with better fallbacks.
    """
    text = text.strip()
    
    # Check if response follows basic structure
    if not text or len(text) < 20:
        return get_fallback_response(question_type, user_message)
    
    # For each question type, verify structure and provide fallback if needed
    structure_checks = {
        'tips': lambda t: 'PRACTICAL TIPS:' in t and any(str(i) in t for i in range(1, 6)),
        'step_by_step': lambda t: 'STEP-BY-STEP GUIDE:' in t and 'Step 1:' in t,
        'causes': lambda t: 'PRIMARY CAUSES:' in t and 'ENVIRONMENTAL MECHANISM:' in t,
        'prevention': lambda t: 'PREVENTION METHODS:' in t and any(str(i) in t for i in range(1, 6)),
        'educational': lambda t: '🌱 CORE CONCEPT:' in t and '💡 SUSTAINABLE SOLUTIONS:' in t,
        'actionable': lambda t: 'ACTIONABLE STEPS:' in t and '✅' in t,
        'effects': lambda t: 'IMMEDIATE EFFECTS:' in t and 'LONG-TERM IMPACTS:' in t,
    }
    
    if question_type in structure_checks and not structure_checks[question_type](text):
        print(f"Structure check failed for {question_type}, using fallback")
        return get_fallback_response(question_type, user_message)
    
    return text

def get_fallback_response(question_type, user_message):
    """
    Provides perfectly formatted fallback responses for each question type.
    """
    fallbacks = {
        'tips': f"""PRACTICAL TIPS:

1. Reduce energy consumption through efficient appliances
2. Choose sustainable transportation options when possible
3. Support local environmental conservation initiatives
4. Practice proper waste segregation and recycling
5. Educate community members about eco-friendly practices""",

        'educational': f"""🌱 CORE CONCEPT:
• {user_message} involves environmental systems and processes
• It affects ecosystem balance and sustainability
• Understanding it helps in conservation efforts

🔹 KEY COMPONENTS:
• Natural environmental factors
• Human activity influences
• Ecosystem interactions

⚡ PRIMARY SOURCES:
• Industrial and agricultural activities
• Resource consumption patterns
• Natural environmental processes

⚠️ ENVIRONMENTAL IMPACTS:
• Biodiversity and habitat changes
• Climate system alterations
• Resource availability shifts

💡 SUSTAINABLE SOLUTIONS:
• Conservation and protection measures
• Sustainable resource management
• Community awareness and action""",

        'prevention': f"""PREVENTION METHODS:

1. Implement early monitoring and detection systems
2. Develop sustainable infrastructure and planning
3. Promote environmental education and awareness
4. Support conservation policies and regulations
5. Practice responsible resource management

EFFECTIVENESS:

Early monitoring combined with community education provides the most sustainable prevention approach.""",

        'causes': f"""PRIMARY CAUSES:

• Industrial emissions and pollution sources
• Deforestation and land use changes
• Intensive agricultural practices

IMMEDIATE TRIGGERS:

• Recent climate pattern changes
• Increased resource consumption
• Urbanization and development pressures

ENVIRONMENTAL MECHANISM:

These factors disrupt natural balances, leading to ecosystem stress and environmental degradation through interconnected feedback loops.""",

        'actionable': f"""ACTIONABLE STEPS:

✅ Conduct an environmental impact assessment
✅ Implement sustainable resource management practices
✅ Engage community stakeholders in conservation efforts
✅ Monitor and adjust strategies based on results
✅ Document and share successful approaches

RESOURCES NEEDED:

• Environmental monitoring equipment
• Community engagement tools
• Sustainable management guidelines

ENVIRONMENTAL BENEFIT:

Reduced ecological footprint and enhanced ecosystem resilience through systematic conservation actions.""",

        'effects': f"""IMMEDIATE EFFECTS:

• Ecosystem disruption and habitat loss
• Air and water quality degradation
• Biodiversity reduction in affected areas

LONG-TERM IMPACTS:

• Climate system alterations and weather pattern changes
• Sustainable development challenges
• Resource scarcity and competition

ECOSYSTEM CONSEQUENCES:

Environmental impacts cascade through ecosystems, affecting species interdependence, nutrient cycles, and overall ecological balance.""",

        'step_by_step': f"""STEP-BY-STEP GUIDE:

Step 1: Assess current environmental conditions and impacts
Step 2: Research sustainable alternatives and best practices
Step 3: Develop an implementation plan with clear objectives
Step 4: Execute the plan with community involvement
Step 5: Monitor results and make continuous improvements"""
    }
    
    return fallbacks.get(question_type, fallbacks['educational'])

if __name__ == "__main__":
    print("Starting EcoGuard Flask server...")
    print("Make sure Ollama is running on http://localhost:11434")
    app.run(debug=True, host='127.0.0.1', port=5000)
