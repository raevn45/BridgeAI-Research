"""
BridgeAI Research — Passage Bank
Each passage has:
  - title
  - control_text     : the original, complex version (shown to control group,
                        and also fed into the AI simplifier for the
                        "simplified" phase both groups see)
  - treatment_text    : an alternate initial presentation shown to the
                        treatment group during the reading phase
  - quiz1_questions   : comprehension questions based on the RAW passage,
                        asked before simplification
  - quiz2_questions   : comprehension questions based on the SAME facts,
                        asked after the AI-simplified version is shown

Question format:
  {
    "question": "...",
    "options": ["...", "...", "...", "..."],
    "answer": <index of correct option in options>
  }
"""

PASSAGES = {

    # ==========================================================
    # MEDICINE
    # ==========================================================
    "medical": {
        "title": "Understanding Hypertension Management",
        "control_text": (
            "Essential hypertension, defined as persistently elevated "
            "systemic arterial blood pressure exceeding 130/80 mmHg in the "
            "absence of a secondary identifiable cause, is managed through "
            "a stepwise pharmacological approach. First-line agents "
            "typically include thiazide diuretics, ACE inhibitors, "
            "angiotensin receptor blockers, or calcium channel blockers, "
            "selected based on patient comorbidities such as diabetes "
            "mellitus or chronic kidney disease. Adherence to "
            "antihypertensive regimens is frequently compromised by "
            "asymptomatic disease presentation, leading to inadequate "
            "long-term cardiovascular risk reduction. Lifestyle "
            "modifications, including sodium restriction below 2,300 mg "
            "daily, regular aerobic exercise, and weight reduction, remain "
            "foundational adjuncts regardless of pharmacotherapy initiation."
        ),
        "treatment_text": (
            "Hypertension, or high blood pressure, is a long-term condition "
            "where the force of blood against artery walls stays too high. "
            "Doctors treat it in steps — usually starting with one "
            "medication, such as a diuretic or an ACE inhibitor, chosen "
            "based on the patient's other health conditions. A major "
            "challenge is that many patients feel no symptoms, so they "
            "often stop taking their medication, which increases their "
            "risk of heart attack and stroke over time. Alongside "
            "medication, doctors recommend lowering salt intake, exercising "
            "regularly, and losing excess weight."
        ),
        "quiz1_questions": [
            {
                "question": "According to the passage, what blood pressure reading defines essential hypertension?",
                "options": [
                    "Above 90/60 mmHg",
                    "Above 130/80 mmHg",
                    "Above 160/100 mmHg",
                    "Above 120/70 mmHg"
                ],
                "answer": 1
            },
            {
                "question": "Which factor most commonly undermines long-term adherence to antihypertensive treatment?",
                "options": [
                    "High cost of medication",
                    "Severe side effects",
                    "The disease often has no symptoms",
                    "Frequent doctor visits required"
                ],
                "answer": 2
            },
            {
                "question": "What daily sodium limit is mentioned as a lifestyle recommendation?",
                "options": [
                    "Below 1,000 mg",
                    "Below 2,300 mg",
                    "Below 3,500 mg",
                    "Below 5,000 mg"
                ],
                "answer": 1
            }
        ],
        "quiz2_questions": [
            {
                "question": "Based on the simplified explanation, why do many people stop taking their blood pressure medication?",
                "options": [
                    "It's too expensive",
                    "They feel no symptoms",
                    "It requires daily injections",
                    "It conflicts with other medications"
                ],
                "answer": 1
            },
            {
                "question": "Which of these is listed as a first-line medication type?",
                "options": [
                    "Antibiotic",
                    "Diuretic",
                    "Antihistamine",
                    "Insulin"
                ],
                "answer": 1
            },
            {
                "question": "Which lifestyle change is recommended alongside medication?",
                "options": [
                    "Increasing salt intake",
                    "Avoiding all exercise",
                    "Losing excess weight",
                    "Skipping meals"
                ],
                "answer": 2
            }
        ]
    },

    # ==========================================================
    # LEGAL
    # ==========================================================
    "legal": {
        "title": "Understanding Contractual Consideration",
        "control_text": (
            "Consideration constitutes an essential element in the "
            "formation of a legally enforceable contract, representing the "
            "bargained-for exchange of value between contracting parties. "
            "Absent valid consideration, an agreement is generally rendered "
            "a nudum pactum — a bare promise unenforceable at law, subject "
            "to limited exceptions such as promissory estoppel. "
            "Consideration need not be adequate in the sense of equivalent "
            "economic value, but it must be sufficient, meaning it holds "
            "some recognizable legal value, however nominal. Past "
            "consideration, meaning an act performed prior to the promise "
            "being made, is generally insufficient to support a binding "
            "contract, as the exchange must be contemporaneous with or "
            "subsequent to the promise itself."
        ),
        "treatment_text": (
            "For a contract to be legally binding, both sides usually have "
            "to give something of value — this is called 'consideration.' "
            "Without it, a promise is typically just a promise, not "
            "something a court will enforce, with a few exceptions. The "
            "value exchanged doesn't have to be equal or fair, just "
            "legally recognizable, even if it's small. One important rule: "
            "something you already did before a promise was made usually "
            "doesn't count as valid consideration — the exchange has to "
            "happen at the same time as, or after, the promise."
        ),
        "quiz1_questions": [
            {
                "question": "What is 'consideration' in contract law, according to the passage?",
                "options": [
                    "A judge's opinion on a case",
                    "The bargained-for exchange of value between parties",
                    "A written signature requirement",
                    "The time limit to file a lawsuit"
                ],
                "answer": 1
            },
            {
                "question": "What term describes a promise made without valid consideration?",
                "options": [
                    "Nudum pactum",
                    "Habeas corpus",
                    "Res judicata",
                    "Voir dire"
                ],
                "answer": 0
            },
            {
                "question": "Why is 'past consideration' generally insufficient to support a contract?",
                "options": [
                    "It must be in writing",
                    "It occurred before the promise was made",
                    "It requires a witness",
                    "It must involve money"
                ],
                "answer": 1
            }
        ],
        "quiz2_questions": [
            {
                "question": "Does consideration need to be an equal exchange of value?",
                "options": [
                    "Yes, both sides must give equal value",
                    "No, it just needs to be legally recognizable, even if small",
                    "Only in written contracts",
                    "Only in verbal contracts"
                ],
                "answer": 1
            },
            {
                "question": "What exception allows a promise to be enforced even without consideration?",
                "options": [
                    "Promissory estoppel",
                    "Double jeopardy",
                    "Statute of limitations",
                    "Eminent domain"
                ],
                "answer": 0
            },
            {
                "question": "When must the exchange happen relative to the promise for consideration to be valid?",
                "options": [
                    "Any time before the promise",
                    "At the same time as, or after, the promise",
                    "Exactly one year later",
                    "It doesn't matter when"
                ],
                "answer": 1
            }
        ]
    },

    # ==========================================================
    # ACADEMIC / EDUCATION
    # ==========================================================
    "academic": {
        "title": "Understanding Cognitive Load Theory",
        "control_text": (
            "Cognitive load theory posits that working memory possesses a "
            "finite capacity, and instructional design must account for "
            "three distinct categories of cognitive load: intrinsic, "
            "extraneous, and germane. Intrinsic load arises from the "
            "inherent complexity of the material relative to the learner's "
            "prior knowledge and cannot be eliminated, only managed through "
            "sequencing and scaffolding. Extraneous load stems from "
            "suboptimal instructional presentation and represents "
            "cognitive effort unrelated to schema construction, which "
            "effective design seeks to minimize. Germane load, by "
            "contrast, refers to the mental effort devoted to processing "
            "and organizing information into long-term memory schemas, and "
            "is actively encouraged. Poorly designed instructional "
            "materials that impose excessive extraneous load can overwhelm "
            "working memory capacity, thereby impeding schema acquisition "
            "regardless of the learner's aptitude."
        ),
        "treatment_text": (
            "Cognitive load theory is about how our short-term ('working') "
            "memory can only handle a limited amount of information at "
            "once. There are three kinds of mental effort involved in "
            "learning: effort caused by how hard the topic itself is "
            "(unavoidable), effort wasted on confusing or badly designed "
            "materials (which should be reduced), and effort spent "
            "actually organizing new information into long-term memory "
            "(which is good and should be encouraged). If teaching "
            "materials are poorly designed and create too much unnecessary "
            "mental effort, students can become overwhelmed and struggle "
            "to learn — even if they're capable."
        ),
        "quiz1_questions": [
            {
                "question": "According to the passage, working memory has what kind of capacity?",
                "options": [
                    "Unlimited capacity",
                    "A finite capacity",
                    "Capacity that grows with age only",
                    "Capacity unrelated to learning"
                ],
                "answer": 1
            },
            {
                "question": "Which type of cognitive load comes from poor instructional design?",
                "options": [
                    "Intrinsic load",
                    "Germane load",
                    "Extraneous load",
                    "Residual load"
                ],
                "answer": 2
            },
            {
                "question": "What is germane load associated with?",
                "options": [
                    "Wasted mental effort from confusing materials",
                    "Organizing information into long-term memory schemas",
                    "The natural difficulty of the topic",
                    "Physical fatigue during study"
                ],
                "answer": 1
            }
        ],
        "quiz2_questions": [
            {
                "question": "Which type of load should instructional designers try to minimize?",
                "options": [
                    "Intrinsic load",
                    "Extraneous load",
                    "Germane load",
                    "All three equally"
                ],
                "answer": 1
            },
            {
                "question": "What happens if teaching materials create too much unnecessary mental effort?",
                "options": [
                    "Learning speeds up",
                    "Students become overwhelmed and struggle to learn",
                    "Working memory capacity increases",
                    "Nothing changes"
                ],
                "answer": 1
            },
            {
                "question": "Which type of cognitive load is described as unavoidable?",
                "options": [
                    "Extraneous load",
                    "Germane load",
                    "Intrinsic load",
                    "Passive load"
                ],
                "answer": 2
            }
        ]
    },

    # ==========================================================
    # FINANCE
    # ==========================================================
    "financial": {
        "title": "Understanding Compound Interest and APY",
        "control_text": (
            "Compound interest refers to the accrual of interest on both "
            "the initial principal and the accumulated interest from "
            "preceding periods, resulting in exponential rather than "
            "linear growth of an investment or liability over time. The "
            "annual percentage yield (APY) reflects this compounding "
            "effect and is calculated using the formula APY = (1 + r/n)^n "
            "− 1, where r represents the nominal annual interest rate and "
            "n denotes the number of compounding periods per year. "
            "Consequently, two accounts with identical nominal interest "
            "rates but differing compounding frequencies — for instance, "
            "monthly versus daily — will yield divergent effective returns, "
            "with more frequent compounding intervals generally producing "
            "marginally higher yields due to the accelerated reinvestment "
            "of accrued interest."
        ),
        "treatment_text": (
            "Compound interest means you earn interest not just on the "
            "money you originally put in, but also on the interest that "
            "money has already earned — so your balance grows faster and "
            "faster over time instead of at a steady rate. The 'APY,' or "
            "annual percentage yield, is the number that shows your true "
            "yearly return once this compounding effect is included. "
            "Because of this, two savings accounts with the same stated "
            "interest rate can actually earn you different amounts of "
            "money, depending on how often the interest is added — an "
            "account that compounds daily will usually earn slightly more "
            "than one that compounds monthly."
        ),
        "quiz1_questions": [
            {
                "question": "What does compound interest accrue on, according to the passage?",
                "options": [
                    "Only the initial principal",
                    "Only previously earned interest",
                    "Both the principal and accumulated interest",
                    "Only government-set base rates"
                ],
                "answer": 2
            },
            {
                "question": "What does APY stand for?",
                "options": [
                    "Annual Payment Yield",
                    "Annual Percentage Yield",
                    "Average Principal Yield",
                    "Adjusted Percentage Yearly"
                ],
                "answer": 1
            },
            {
                "question": "What does 'n' represent in the APY formula given in the passage?",
                "options": [
                    "The nominal interest rate",
                    "The number of compounding periods per year",
                    "The total number of years",
                    "The initial deposit amount"
                ],
                "answer": 1
            }
        ],
        "quiz2_questions": [
            {
                "question": "Why can two accounts with the same stated interest rate earn different amounts?",
                "options": [
                    "They have different account holders",
                    "They compound interest at different frequencies",
                    "One account is taxed differently",
                    "They were opened in different years"
                ],
                "answer": 1
            },
            {
                "question": "Which compounding frequency generally earns slightly more, according to the passage?",
                "options": [
                    "Yearly over monthly",
                    "Monthly over daily",
                    "Daily over monthly",
                    "There is no difference"
                ],
                "answer": 2
            },
            {
                "question": "What does compound growth look like compared to simple linear growth?",
                "options": [
                    "Slower than linear growth",
                    "Identical to linear growth",
                    "Faster, exponential growth",
                    "It decreases over time"
                ],
                "answer": 2
            }
        ]
    },

    # ==========================================================
    # SCIENCE / TECHNOLOGY
    # ==========================================================
    "scientific": {
        "title": "Understanding CRISPR Gene Editing",
        "control_text": (
            "CRISPR-Cas9 is a genome-editing technology derived from a "
            "naturally occurring bacterial adaptive immune mechanism, "
            "wherein bacteria incorporate fragments of viral DNA into "
            "their own genome to recognize and cleave matching sequences "
            "upon future viral infection. In laboratory applications, a "
            "synthetic guide RNA is engineered to match a specific target "
            "sequence within a genome, directing the Cas9 endonuclease to "
            "induce a double-strand break at that precise location. The "
            "cell's endogenous DNA repair mechanisms — either non-homologous "
            "end joining, which is error-prone and often introduces "
            "insertions or deletions, or homology-directed repair, which "
            "can incorporate a supplied DNA template with high precision — "
            "then resolve the break, enabling targeted gene disruption or "
            "correction."
        ),
        "treatment_text": (
            "CRISPR-Cas9 is a gene-editing tool that scientists borrowed "
            "from bacteria, which naturally use a similar system to "
            "recognize and destroy viruses that attack them. In the lab, "
            "researchers design a small piece of guide RNA that matches a "
            "specific spot in a genome. This guide leads the Cas9 protein "
            "to that exact spot and cuts both strands of the DNA there. "
            "The cell then repairs the cut using one of two methods: a "
            "quick but sloppy method that often adds or removes small bits "
            "of DNA, or a more careful method that can use a provided DNA "
            "template to make a precise, intentional edit."
        ),
        "quiz1_questions": [
            {
                "question": "What natural system is CRISPR-Cas9 derived from?",
                "options": [
                    "A human enzyme pathway",
                    "A bacterial adaptive immune mechanism",
                    "A plant photosynthesis process",
                    "A synthetic laboratory invention with no natural origin"
                ],
                "answer": 1
            },
            {
                "question": "What is the role of the guide RNA in CRISPR-Cas9?",
                "options": [
                    "It repairs broken DNA",
                    "It directs Cas9 to a specific target sequence",
                    "It replicates the entire genome",
                    "It destroys the Cas9 protein"
                ],
                "answer": 1
            },
            {
                "question": "What does the Cas9 enzyme do once guided to the target sequence?",
                "options": [
                    "It copies the DNA sequence",
                    "It induces a double-strand break in the DNA",
                    "It converts RNA into DNA",
                    "It seals damaged cell membranes"
                ],
                "answer": 1
            }
        ],
        "quiz2_questions": [
            {
                "question": "What are the two DNA repair methods mentioned after a CRISPR cut?",
                "options": [
                    "Cloning and mutation",
                    "Non-homologous end joining and homology-directed repair",
                    "Transcription and translation",
                    "Replication and division"
                ],
                "answer": 1
            },
            {
                "question": "Which repair method is described as error-prone?",
                "options": [
                    "Homology-directed repair",
                    "Non-homologous end joining",
                    "Both are equally precise",
                    "Neither introduces errors"
                ],
                "answer": 1
            },
            {
                "question": "Which repair method can use a supplied DNA template for a precise edit?",
                "options": [
                    "Non-homologous end joining",
                    "Homology-directed repair",
                    "Random mutation",
                    "Viral integration"
                ],
                "answer": 1
            }
        ]
    },

}


def get_passage(passage_id):
    """Return the passage dict for a given id, defaulting to 'medical'."""
    return PASSAGES.get(passage_id, PASSAGES["medical"])