from sqlalchemy.orm import Session

from app.models import Quiz, Challenge


QUIZ_QUESTIONS = [
    {
        "question": "Which is the most eco-friendly way to celebrate Diwali?",
        "options": [
            "Bursting loud crackers",
            "Using LED lights and diyas",
            "Burning plastic decorations",
            "Using excessive electricity"
        ],
        "correct_answer": 1,
        "explanation": "LED lights consume less electricity, while traditional diyas offer a more sustainable celebration when used responsibly.",
        "category": "Sustainable Celebration"
    },
    {
        "question": "What is a major environmental impact of firecrackers?",
        "options": [
            "Improved air quality",
            "Reduced noise pollution",
            "Air and noise pollution",
            "Increased oxygen levels"
        ],
        "correct_answer": 2,
        "explanation": "Firecrackers release pollutants and create high noise levels that can affect people, animals and the environment.",
        "category": "Pollution Awareness"
    },
    {
        "question": "Which material is better for eco-friendly decorations?",
        "options": [
            "Single-use plastic",
            "Thermocol",
            "Natural flowers and leaves",
            "Plastic glitter"
        ],
        "correct_answer": 2,
        "explanation": "Natural decorations can reduce plastic waste and are often biodegradable.",
        "category": "Green Decorations"
    },
    {
        "question": "How should used flower decorations be disposed of?",
        "options": [
            "Burn them",
            "Mix them with plastic waste",
            "Compost them",
            "Throw them into rivers"
        ],
        "correct_answer": 2,
        "explanation": "Organic flowers can be composted and converted into nutrient-rich material.",
        "category": "Waste Management"
    },
    {
        "question": "Which lighting option generally consumes less electricity?",
        "options": [
            "LED bulbs",
            "Traditional high-power bulbs",
            "Halogen lamps",
            "Incandescent bulbs"
        ],
        "correct_answer": 0,
        "explanation": "LED bulbs are generally more energy-efficient than traditional incandescent bulbs.",
        "category": "Energy Conservation"
    },
    {
        "question": "What should you do with recyclable packaging after Diwali shopping?",
        "options": [
            "Burn it",
            "Separate and recycle it",
            "Throw it into drains",
            "Mix it with food waste"
        ],
        "correct_answer": 1,
        "explanation": "Separating recyclable packaging makes proper recycling easier.",
        "category": "Waste Management"
    },
    {
        "question": "Which is a better alternative to plastic gift wrapping?",
        "options": [
            "Plastic sheets",
            "Non-recyclable foil",
            "Reusable cloth wrapping",
            "Thermocol sheets"
        ],
        "correct_answer": 2,
        "explanation": "Reusable cloth wrapping reduces single-use packaging waste.",
        "category": "Sustainable Gifting"
    },
    {
        "question": "Why should we avoid bursting crackers near animals?",
        "options": [
            "Animals enjoy loud sounds",
            "Noise can frighten and stress animals",
            "It improves animal health",
            "It helps animals sleep"
        ],
        "correct_answer": 1,
        "explanation": "Loud noises can cause fear, stress and disorientation in animals.",
        "category": "Animal Welfare"
    },
    {
        "question": "What is the best way to reduce electricity consumption during Diwali?",
        "options": [
            "Keep all lights on all day",
            "Use energy-efficient lighting and switch it off when not needed",
            "Use more electrical appliances",
            "Leave decorations running overnight unnecessarily"
        ],
        "correct_answer": 1,
        "explanation": "Efficient lighting and responsible usage help conserve electricity.",
        "category": "Energy Conservation"
    },
    {
        "question": "Which action helps make Diwali celebrations more sustainable?",
        "options": [
            "Using disposable plastic plates",
            "Throwing waste in open spaces",
            "Choosing reusable utensils and decorations",
            "Burning household waste"
        ],
        "correct_answer": 2,
        "explanation": "Reusable products reduce waste and help protect the environment.",
        "category": "Sustainable Celebration"
    }
]
CHALLENGES = [
    {
        "title": "Plant a Tree",
        "description": "Plant a sapling and contribute to a greener environment.",
        "points": 20
    },
    {
        "title": "Say No to Crackers",
        "description": "Celebrate an eco-friendly Diwali without firecrackers.",
        "points": 15
    },
    {
        "title": "Use LED Lights",
        "description": "Decorate your home using energy-efficient LED lights.",
        "points": 10
    },
    {
        "title": "Avoid Plastic Decorations",
        "description": "Choose reusable or natural decorations instead of single-use plastic.",
        "points": 15
    },
    {
        "title": "Spread Eco Awareness",
        "description": "Encourage friends and family to celebrate a sustainable Diwali.",
        "points": 10
    }
]

def seed_challenges(db: Session):
    existing_count = db.query(Challenge).count()

    if existing_count > 0:
        return

    challenges = [
        Challenge(**challenge)
        for challenge in CHALLENGES
    ]

    db.add_all(challenges)
    db.commit()

def seed_quiz_questions(db: Session):
    existing_count = db.query(Quiz).count()

    if existing_count > 0:
        return

    questions = [
        Quiz(**question)
        for question in QUIZ_QUESTIONS
    ]



    db.add_all(questions)
    db.commit()