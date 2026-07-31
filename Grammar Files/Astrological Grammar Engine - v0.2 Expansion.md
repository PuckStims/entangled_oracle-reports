# **Astrological Grammar Engine: v0.2 Expansion Supplement**

## **1\. Expansion Philosophy**

This supplement builds upon the v0.1 Master Reference by introducing a **Condition Layer** (retrogrades, dignities), expanding the **Geometric Vocabulary** (harmonics, declinations), and adding missing **Thematic Actors** (asteroids, specific lots).  
Sourcing standard:

> * **Asteroids & Harmonics:** NCGR curriculum and modern empirical standards.  
> * **Dignities, Lots, & Cazimi:** Hellenistic/Traditional standards (Ptolemy, Valens).  
> * **Parans:** Jim Lewis's foundational Astrocartography guidelines.

## **2\. Component Additions (Bodies & Points)**

### **The Major Asteroids (Specific Function Timers)**

**Ceres**

> * **Category:** Asteroid / Medium Timer  
> * **Core meaning:** Nurturing, food, agriculture, cycles of loss and return, bodily sustenance.  
> * **As activator:** Highlights themes of caretaking, physical nourishment, or letting go.  
> * **As natal target:** Describes how the native gives and receives care, and manages grief/return.  
> * **Common prose verbs:** nurtures, sustains, harvests, cycles, grieves, feeds.

**Pallas (Athena)**

> * **Category:** Asteroid / Medium Timer  
> * **Core meaning:** Strategic intelligence, pattern recognition, weaving, political wisdom.  
> * **As activator:** Triggers a need for strategy, planning, or seeing the "big picture."  
> * **As natal target:** Describes the intellectual approach to problem-solving and systemic thinking.  
> * **Common prose verbs:** strategizes, recognizes, maps, solves, coordinates.

**Juno**

> * **Category:** Asteroid / Medium Timer  
> * **Core meaning:** Commitment, marriage, contractual equity, loyalty, power dynamics in partnership.  
> * **As activator:** Activates themes of fairness, commitment, or grievances in deep partnerships.  
> * **As natal target:** Describes the non-negotiable requirements for long-term relational equity.  
> * **Common prose verbs:** commits, binds, balances, expects, renegotiates.

**Vesta**

> * **Category:** Asteroid / Medium Timer  
> * **Core meaning:** Devotion, focus, the sacred flame, sublimation of energy, solitary work.  
> * **As activator:** Demands absolute focus, drawing energy inward toward a specific task or devotion.  
> * **As natal target:** Describes where the native finds sacred focus, often requiring temporary withdrawal.  
> * **Common prose verbs:** devotes, focuses, consecrates, withdraws, dedicates.

### **Calculated Lots (Arabic Parts)**

**Lot of Spirit (Pars Solis)**

> * **Category:** Calculated Lot  
> * **Core meaning:** Career initiative, voluntary action, what the native *does* with their will.  
> * **As target only:** When hit, activates themes of profound career moves, reputation, and intentional life choices.  
> * *Note: Operates as the active counterpart to the receptive Part of Fortune.*

**Lot of Eros**

> * **Category:** Calculated Lot  
> * **Core meaning:** Creative appetite, romantic drive, what the native desires deeply.  
> * **As target only:** When hit, awakens intense creative urges, romantic pursuits, or obsessive fascinations.

### **Angles as Natal Targets (Completing the Cross)**

**Descendant (DC / 7th House Cusp)**

> * **Category:** Angle / Relational Point  
> * **Core meaning:** The mirror, the partner, the shadow, contracts.  
> * **As target only:** When hit by an activator, changes directly manifest through the arrival of a partner, client, or open enemy.

**Imum Coeli (IC / 4th House Cusp)**

> * **Category:** Angle / Foundational Point  
> * **Core meaning:** The root, ancestry, home, private emotional baseline.  
> * **As target only:** When hit by an activator, changes impact the literal home, family dynamics, or deep psychological foundations.

## **3\. Aspect Glossary Expansion (Harmonics & Declinations)**

| Aspect | Degrees | Basic Meaning | Software Tone |
| :---- | :---- | :---- | :---- |
| **Quintile** | 72° | Specialized talent, creative drive, mental focus | Flowing / highly creative / requires mental play |
| **Biquintile** | 144° | Intense creative expression, non-linear problem solving | Flowing / obsessive creativity / externalized talent |
| **Parallel** | N/A (Declination) | Two bodies at the same degree North/South. Acts as a fused union. | Deeply fused / underlying unification (treat as Conjunction) |
| **Contraparallel** | N/A (Declination) | Two bodies at equal opposite North/South. Acts as a mirror tension. | Challenging / underlying tension (treat as Opposition) |

## **4\. The Condition Layer (State Modifiers)**

The engine must now evaluate the *state* of the activator or target. Condition acts as an adjective modifying the core verb.  
**1\. Retrograde Motion (Rx)**

> * **Core meaning:** Reversal, inward turn, review, delay, past returning.  
> * **Grammar rule:** If the Activator is Rx, the prose verb must change from an external action to an internal/historical one.  
> * *Example:* Mars direct \= "pushes forward." Mars Rx \= "reassesses drive" or "returns to an old conflict."

**2\. Cazimi (In the Heart of the Sun)**

> * **Core meaning:** Supreme clarity, illumination, absolute strength.  
> * **Grammar rule:** If a planet is within 1° of the Sun, apply a "cazimi\_multiplier". It replaces standard transit language with "moment of supreme clarity," "revelation," or "absolute empowerment" regarding the planet's domain.

**3\. Essential Dignity (Domicile vs. Detriment/Fall)**

> * **Core meaning:** The planet's comfort level and resource access.  
> * **Grammar rule:** \* If **Domicile/Exaltation**: The planet acts cleanly and predictably. (e.g., Mars in Aries square Venus: "You clearly assert your relational boundaries.")  
  * If **Detriment/Fall**: The planet acts indirectly, compensating or struggling. (e.g., Mars in Cancer square Venus: "Emotional defensiveness or passive aggression causes friction in relationships.")

## **5\. Astrocartography Expansion: Parans (Latitude Crossings)**

Parans occur when two planets cross paths at a specific geographic latitude. Their influence spans the entire circumference of the globe at that specific latitude line (usually given a 1° orb North/South).  
**Paran Formula:** \[Place\] activates a \[Planet 1\] / \[Planet 2\] Paran at this latitude.  
**Plain-Language Version:** Regardless of east/west movement, living at this latitude permanently blends the energy of \[Planet 1\] and \[Planet 2\] in your daily life.  
**Example: Jupiter/Saturn Paran**

> * **Grammar expansion:** Seattle sits on a Jupiter/Saturn Paran latitude.  
> * **Plain-language translation:** At this latitude, expansion (Jupiter) and limitation (Saturn) are permanently fused. You will likely experience a rhythm of disciplined growth, where every step forward requires careful structuring. Success here is durable, but rarely overnight.

## **6\. Updated Developer Data Model (incorporating v0.2)**

When the code detects a transit, it now checks for condition\_modifiers.  
`{`  
  `"combo_id": "tran_mars_rx_sq_venus_7H_detriment",`  
  `"activator": "pl_mars",`  
  `"activator_state": "retrograde",`  
  `"aspect": "asp_square",`  
  `"target": "pl_venus",`  
  `"target_state": "detriment",`  
  `"house": "h_07",`  
  `"valence": "complex_challenging",`  
  `"weight": "high",`  
  `"core_interpretation": "A delayed or returning physical drive (Mars Rx) creates friction (Square) with your compromised relational values (Venus Detriment) in the area of partnerships (7th House).",`  
  `"short_timing_sentence": "An old frustration regarding a partnership may resurface today, requiring you to address a boundary you previously avoided.",`  
  `"risk_of_overstatement": "Medium - Ensure the tone reflects internal review rather than a new external disaster."`  
`}`  
