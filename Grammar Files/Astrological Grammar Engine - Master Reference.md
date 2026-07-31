# **Astrological Grammar Engine: Master Reference**

## **1\. Core Philosophy**

We are not defining astrological terms. We are defining astrological grammar. The software must understand the parsing of a sentence (Activator \+ Aspect \+ Target \+ House) to calculate a temporary timing force, a geometric relationship, a natal function, and a life domain, which are then translated into plain-language advice.

## **2\. Component Definitions (Bodies & Points)**

We need an entry for every body or point the software can name.

### **Luminaries & Inner Planets (Fast Timers)**

**Sun**

> * **Category:** Luminary / Activator  
> * **Core meaning:** visibility, vitality, will, attention, identity, conscious focus  
> * **As activator:** brings clarity, emphasis, illumination, visibility  
> * **As natal target:** describes the native's core identity and life-force pattern  
> * **Common prose verbs:** clarifies, highlights, names, exposes, energizes

**Moon**

> * **Category:** Luminary / Fast Timer  
> * **Core meaning:** body, mood, instinct, daily rhythm, emotional weather  
> * **As activator:** marks short-lived timing cues, body-mood shifts, immediate needs  
> * **As natal target:** describes emotional patterning, needs, belonging, response  
> * **Common prose verbs:** sensitizes, cues, stirs, reflects, fluctuates

**Mercury**

> * **Category:** Inner Planet / Fast Timer  
> * **Core meaning:** mind, data, communication, logistics, translation  
> * **As activator:** triggers news, messages, mental shifts, logistical changes  
> * **As natal target:** describes mental wiring, learning style, communication habits  
> * **Common prose verbs:** analyzes, connects, translates, verbalizes, sorts

**Venus**

> * **Category:** Inner Planet / Fast Timer  
> * **Core meaning:** connection, values, aesthetics, pleasure, attraction, resource  
> * **As activator:** sweetens, attracts, harmonizes, highlights social/financial dynamics  
> * **As natal target:** describes relational patterning, receptivity, aesthetic and material values  
> * **Common prose verbs:** harmonizes, attracts, values, softens, connects

**Mars**

> * **Category:** Inner Planet / Fast-to-Medium Timer  
> * **Core meaning:** drive, severance, action, conflict, boundary-setting, heat  
> * **As activator:** energizes, provokes, agitates, demands immediate action  
> * **As natal target:** describes assertion style, anger, ambition, defense mechanisms  
> * **Common prose verbs:** ignites, pushes, severs, defends, motivates

### **Social Planets (Medium Timers)**

**Jupiter**

> * **Category:** Social Planet / Medium Timer  
> * **Core meaning:** expansion, belief, coherence, luck, synthesis, excess  
> * **As activator:** broadens, elevates, offers opportunity, occasionally over-promises  
> * **As natal target:** describes areas of natural faith, growth potential, and philosophical framework  
> * **Common prose verbs:** expands, uplifts, magnifies, philosophizes, overstates

**Saturn**

> * **Category:** Social Planet / Medium Timer  
> * **Core meaning:** limits, structure, time, gravity, authority, maturation, delay  
> * **As activator:** restricts, structures, tests, demands accountability or patience  
> * **As natal target:** describes internalized rules, fears, mastery paths, and responsibilities  
> * **Common prose verbs:** structures, limits, grounds, delays, matures

### **Outer Planets (Slow Timers / Transpersonal)**

**Uranus**

> * **Category:** Outer Planet / Slow Timer  
> * **Core meaning:** disruption, liberation, shock, innovation, awakening, decentralization  
> * **As activator:** surprises, disrupts, breaks patterns, electrifies, distances  
> * **As natal target:** describes where the native rebels, innovates, or experiences sudden shifts  
> * **Common prose verbs:** disrupts, awakens, electrifies, liberates, shocks

**Neptune**

> * **Category:** Outer Planet / Slow Timer  
> * **Core meaning:** illusion, spirituality, dissolution, compassion, fog, interconnectedness  
> * **As activator:** softens, confuses, inspires, drains boundaries, enchants  
> * **As natal target:** describes areas of idealism, escapism, spiritual sensitivity, and projection  
> * **Common prose verbs:** dissolves, inspires, obscures, sensitizes, floods

**Pluto**

> * **Category:** Outer Planet / Slow Timer  
> * **Core meaning:** transformation, power, underworld, purgation, obsession, regeneration  
> * **As activator:** purges, empowers, triggers power dynamics, excavates hidden material  
> * **As natal target:** describes psychological depths, trauma responses, and areas of profound regeneration  
> * **Common prose verbs:** transforms, excavates, purges, empowers, obsesses

### **Structural & Sensitive Points**

**Chiron**

> * **Category:** Asteroid / Sensitive Point  
> * **Core meaning:** the wound, the medicine, vulnerability, mentorship, chronic sensitivity  
> * **As activator:** triggers old hurts, offers profound healing or teaching moments  
> * **As natal target:** describes the core unfixable vulnerability that becomes a source of wisdom  
> * **Common prose verbs:** triggers, heals, mentors, exposes (tenderly), integrates

**North Node (True/Mean)**

> * **Category:** Eclipse Axis / Karmic Point  
> * **Core meaning:** hunger, growth trajectory, unfamiliar territory, increase  
> * **As activator:** pulls the native forward, increases desire, brings fated encounters  
> * **As natal target:** describes the uncomfortable but necessary life direction  
> * **Common prose verbs:** amplifies, hungers, pulls, directs, increases

**South Node (True/Mean)**

> * **Category:** Eclipse Axis / Karmic Point  
> * **Core meaning:** release, comfort zone, past habits, decrease, spiritualization  
> * **As activator:** triggers letting go, drains energy from physical pursuits, brings past echoes  
> * **As natal target:** describes innate talents that must not become traps; the comfort zone  
> * **Common prose verbs:** releases, drains, familiarizes, empties, surrenders

**Ascendant (1st House Cusp)**

> * **Category:** Angle / Personal Point  
> * **Core meaning:** the physical body, the helm, the steering wheel, the immediate environment  
> * **As target only:** When hit by an activator, changes directly impact physical vitality, appearance, or the fundamental direction of the life.

**Midheaven (MC / 10th House Cusp)**

> * **Category:** Angle / Public Point  
> * **Core meaning:** reputation, visibility, life direction, public role, authority  
> * **As target only:** When hit by an activator, changes impact career, public standing, and how the native is seen by the collective.

**Part of Fortune (Lot)**

> * **Category:** Calculated Lot  
> * **Core meaning:** material thriving, bodily alignment, synthesizing Sun/Moon/Rising  
> * **As target only:** When hit, activates themes of resource, serendipity, and physical well-being.

## **3\. Aspect Glossary**

Each aspect needs a technical definition and a plain-language behavior. The key distinction: "challenging" does not mean bad; it means "requires adjustment, attention, or participation."

| Aspect | Degrees | Basic Meaning | Software Tone |
| :---- | :---- | :---- | :---- |
| **Conjunction** | 0° | Fusion, activation, intensification | "This is directly lit up. The energies are blended." |
| **Sextile** | 60° | Opportunity, cooperation, usable opening | Flowing / constructive / requires a tap to activate |
| **Square** | 90° | Friction, pressure, action demand | Challenging / developmental / requires effort |
| **Trine** | 120° | Ease, talent, support, flow | Flowing / stabilizing / happens automatically |
| **Opposition** | 180° | Polarity, relationship, externalization | Challenging or clarifying / playing out via "the other" |
| **Quincunx** | 150° | Adjustment, mismatch, recalibration | Awkward / corrective / requires a pivot |
| **Semisquare** | 45° | Minor friction, irritation, tension cue | Subtle challenging cue / inner itch |
| **Sesquiquadrate** | 135° | Accumulated friction, pressure-release | Challenging cue / externalized irritation |
| **Semisextile** | 30° | Resource gathering, minor support | Subtle flowing cue / peripheral assistance |

## **4\. House Glossary**

A stable phrase bank for the domains of life.

| House | Core Domain | Screenshot-Style Phrasing |
| :---- | :---- | :---- |
| **1st** | body, identity, appearance, self-direction | body, identity, first impression, how you enter the room |
| **2nd** | money, values, possessions, stability | resources, self-worth, material support, livelihood |
| **3rd** | communication, siblings, local area, learning | speech, study, messages, daily routines, nearby movement |
| **4th** | home, family, roots, private life | home, belonging, ancestry, inner foundation, private retreat |
| **5th** | creativity, pleasure, romance, children, play | creativity, pleasure, romance, courage to be seen, joy |
| **6th** | work, health, routines, service | habits, labor, bodily maintenance, daily systems, chores |
| **7th** | partnership, contracts, open others | relationships, agreements, mirrors, negotiation, committed partners |
| **8th** | intimacy, debt, shared resources, change | entanglement, trust, inheritance, deep exchange, shared finances |
| **9th** | belief, travel, publishing, higher study | worldview, faith, teaching, long-range meaning, exploration |
| **10th** | career, reputation, authority, public role | career, reputation, responsibility, leadership, life calling |
| **11th** | friends, networks, hopes, collectives | community, allies, audiences, future plans, groups |
| **12th** | solitude, endings, hidden matters, retreat | rest, solitude, endings, mental health, what needs quiet processing |

## **5\. Combination Layer**

This is the grammar engine at work.

### **A. Activator \+ Aspect**

> * **Mars \+ Square**  
  * **Meaning:** Action or conflict meeting friction; an obstacle demands energy.  
  * **Tone:** Push through, but watch for unnecessary aggression.  
> * **Venus \+ Trine**  
  * **Meaning:** Connection and pleasure flowing easily.  
  * **Tone:** Receive the support; lean into the harmony.  
> * **Uranus \+ Opposition**  
  * **Meaning:** Sudden disruption or need for freedom coming from an external source or partner.  
  * **Tone:** Stay flexible; do not rigidly fight the change.

### **B. Aspect \+ Target**

> * **Square \+ Moon**  
  * **Meaning:** Friction around emotional safety, physical needs, or domestic life.  
> * **Trine \+ Mars**  
  * **Meaning:** Smooth, unhindered access to drive, courage, and boundary-setting.  
> * **Conjunction \+ North Node**  
  * **Meaning:** A direct push toward the unfamiliar growth trajectory; feels fated.

### **C. Target \+ House**

> * **Uranus in the 4th**  
  * **Meaning:** Disruption, innovation, or a need for extreme freedom in the home, family, or living situation.  
> * **Venus in the 8th**  
  * **Meaning:** Relational values heavily tied to deep trust, financial entanglement, and psychological intimacy.  
> * **Mars in the 2nd**  
  * **Meaning:** Drive, ambition, and potential conflict surrounding personal resources, money, and self-worth.

### **D. Full Event Pattern (The Master Formula)**

\[Activator\] \[Aspect\] your \[Natal Target\] in the \[House\]  
**Example 1: Mars Square your Mercury in the 7th house**

> * **Mars:** Drive, heat, action, conflict  
> * **Square:** Friction, pressure, action demand  
> * **Mercury:** Mind, communication, logistics  
> * **7th house:** Partnership, negotiation, agreements  
> * **Combined Meaning:** A fast-moving transit brings heat and pressure (Mars Square) to how you communicate and process data (Mercury) within your closest relationships or contracts (7th house).  
> * **Advice Translation:** You might feel an urgent need to argue a point or push a negotiation forward. Use the mental sharpness, but be aware that your words have more heat than usual. Pause before sending the text.

**Example 2: Jupiter Trine your Venus in the 2nd house**

> * **Jupiter:** Expansion, luck, synthesis  
> * **Trine:** Ease, flow, support  
> * **Venus:** Values, resources, attraction  
> * **2nd house:** Money, material stability, self-worth  
> * **Combined Meaning:** A medium-term period of expansive support (Jupiter Trine) naturally elevates your ability to attract resources, money, and pleasurable stability (Venus in the 2nd).  
> * **Advice Translation:** Financial or material opportunities are flowing easily right now. Because trines are passive, you have to actively reach out to capture this luck. Ask for the raise, raise your rates, or invest in something that brings you tangible joy.

## **6\. Practical Database/Spreadsheet Columns**

To translate this into actual code, you need a highly structured database (like PostgreSQL, Airtable, or a JSON configuration).

### **Glossary Table (Base Definitions)**

| Column Name | Example Value (Row 1: Saturn) | Example Value (Row 2: Quincunx) |
| :---- | :---- | :---- |
| **term\_id** | pl\_saturn | asp\_quincunx |
| **term\_type** | planet | aspect |
| **display\_name** | Saturn | Quincunx |
| **canonical\_name** | saturn | quincunx |
| **aliases** | \["Cronus", "Lord of Karma"\] | \["Inconjunct"\] |
| **technical\_def** | Slow moving social planet; ringed gas giant. | 150 degree angle; 5 signs apart. |
| **plain\_lang\_def** | The principle of limits, time, and maturity. | An awkward angle requiring adjustment. |
| **keywords** | \["structure", "limits", "time", "maturity"\] | \["adjustment", "recalibration", "mismatch"\] |
| **valence\_default** | heavy / demanding | awkward |
| **prose\_verbs** | \["structures", "limits", "grounds", "tests"\] | \["adjusts", "pivots", "recalibrates"\] |
| **prose\_warnings** | Do not use words like "doom", "failure", "bad". | Do not treat as a crisis, just an itch. |

### **Grammar Generation Engine (The Logic Layer)**

When the code detects a transit, it runs a script that pieces together the strings based on weights.  
`{`  
  `"combo_id": "tran_mars_sq_mercury_7H",`  
  `"activator": "pl_mars",`  
  `"aspect": "asp_square",`  
  `"target": "pl_mercury",`  
  `"house": "h_07",`  
  `"valence": "volatile",`  
  `"weight": "high (because inner planet to inner planet on an angle is noticeable)",`  
  `"core_interpretation": "{activator.prose_verbs[0]} meets {aspect.plain_lang_def} regarding your {target.plain_lang_def} in the area of {house.plain_lang_def}.",`  
  `"short_timing_sentence": "Expect fast-paced or heated communication in your partnerships today.",`  
  `"risk_of_overstatement": "Low - this is a fast transit, it will pass in 2-3 days, so keep the tone immediate and highly actionable."`  
`}`

# **Astrological Grammar Engine: Astrocartography Supplement v0.1**

## **1\. Supplement Purpose**

Astrocartography is the location layer of the grammar engine.  
Where the core engine asks:  
*What is being activated, by what kind of relationship, in what natal function, and in what life domain?*  
The astrocartography layer asks:  
*What part of the natal chart becomes louder, more visible, more embodied, or more situationally unavoidable in a specific place?*  
This supplement defines the grammar required for Place Resonance, Between Places, and future map-based products.  
It does not treat a location as universally “good” or “bad.” A place is interpreted as a symbolic environment that changes which parts of the natal chart become easier to access, harder to ignore, more public, more private, more relational, or more embodied.

## **2\. Core Astrocartography Formula**

**Master Formula** \[Place\] emphasizes \[Planet/Point\] through \[Angle\] within \[Distance Band\], modified by \[Natal Condition\] and \[Relocated House Shift\].  
**Plain-Language Version** In this location, your \[Planet\] becomes more \[Angle Behavior\], especially through themes of \[Relocated House / Life Area\].  
**Example:** Seattle places Venus near the Midheaven.

> * **Grammar expansion:** Seattle emphasizes Venus through the MC angle within a close distance band, modified by natal Venus condition and its relocated house placement.  
> * **Plain-language translation:** In Seattle, Venus becomes more publicly visible. Connection, aesthetics, pleasure, social ease, and values are more likely to be seen by others or woven into career/reputation themes. This is not automatically easy, but it makes Venus harder to hide.

## **3\. New Component: Place**

A **Place** is not interpreted as a personality. It is a geographic context that changes the chart’s interface with lived experience.  
**Place Data Fields**  
`{`  
  `"place_name": "Seattle",`  
  `"region": "Washington",`  
  `"country": "United States",`  
  `"latitude": 47.6062,`  
  `"longitude": -122.3321,`  
  `"timezone": "America/Los_Angeles",`  
  `"calculation_type": "relocated_chart + angularity_scan"`  
`}`

**Place Prose Role** A place can:

> * Amplify a natal planet or point  
> * Shift a planet into a different house emphasis  
> * Bring an angle into contact with a natal planet  
> * Create stronger public/private/relational/body emphasis  
> * Alter the lived “texture” of the natal chart without replacing the natal chart

**Suggested Prose Verbs:** emphasizes, amplifies, localizes, externalizes, embodies, publicizes, privatizes, redirects, concentrates, intensifies, exposes, grounds

## **4\. New Component: Angles as Location Interfaces**

The existing reference defines the Ascendant as the body, helm, steering wheel, and immediate environment, and the Midheaven as reputation, visibility, public role, and authority. Astrocartography expands all four angles into locational interfaces.

### **Ascendant / AC**

> * **Core locational meaning:** Body, identity, appearance, arrival, first impression, self-direction.  
> * **When a planet is emphasized on the AC:** The planet becomes embodied. Other people may experience it as part of the native’s presence, style, physical rhythm, and immediate way of entering life.  
> * **Prose verbs:** embodies, personalizes, makes visible through the body, brings into first impression, steers through  
> * **Formula:** \[Planet\] on the Ascendant \= the person wears \[Planet\] more visibly in that place.

### **Descendant / DC**

> * **Core locational meaning:** Partnership, other people, mirrors, contracts, relational projection, interpersonal encounter.  
> * **When a planet is emphasized on the DC:** The planet tends to arrive through other people, partners, clients, rivals, collaborators, or relational mirrors.  
> * **Prose verbs:** externalizes, mirrors, attracts through others, negotiates, confronts through relationship  
> * **Formula:** \[Planet\] on the Descendant \= the person meets \[Planet\] through others in that place.

### **Midheaven / MC**

> * **Core locational meaning:** Visibility, career, reputation, authority, public role, life direction.  
> * **When a planet is emphasized on the MC:** The planet becomes public-facing. It may affect career, reputation, recognition, ambition, leadership, or how the person is seen by the collective.  
> * **Prose verbs:** publicizes, elevates, professionalizes, exposes, makes visible, calls forward  
> * **Formula:** \[Planet\] on the Midheaven \= the person is seen through \[Planet\] in that place.

### **Imum Coeli / IC**

> * **Core locational meaning:** Home, roots, privacy, family, belonging, emotional foundation, retreat.  
> * **When a planet is emphasized on the IC:** The planet becomes private, ancestral, domestic, psychological, or foundational. It may describe what the place awakens underneath the visible life.  
> * **Prose verbs:** roots, internalizes, privatizes, returns to origin, settles, haunts, shelters  
> * **Formula:** \[Planet\] on the IC \= the person lives \[Planet\] at the root level in that place.

## **5\. Distance Bands**

Distance is one of the most important interpretive controls. The engine should avoid treating a far-off line as equally strong as a close line.  
**Suggested v0.1 Bands**  
`{`  
  `"exact": {`  
    `"range_miles": "0-25",`  
    `"strength": "dominant",`  
    `"language": "This is a defining location signature."`  
  `},`  
  `"close": {`  
    `"range_miles": "26-100",`  
    `"strength": "strong",`  
    `"language": "This is a clear and noticeable location signature."`  
  `},`  
  `"active": {`  
    `"range_miles": "101-250",`  
    `"strength": "moderate",`  
    `"language": "This influence is present, but not the whole story."`  
  `},`  
  `"background": {`  
    `"range_miles": "251-500",`  
    `"strength": "subtle",`  
    `"language": "This may color the location, but should not dominate interpretation."`  
  `},`  
  `"out_of_band": {`  
    `"range_miles": "501+",`  
    `"strength": "weak",`  
    `"language": "Do not treat this as a major line influence unless supported by other factors."`  
  `}`  
`}`

**Tone Rule** The closer the line, the more direct the language may be.

> * **Exact:** “This place strongly emphasizes…”  
> * **Close:** “This place clearly emphasizes…”  
> * **Active:** “This place may emphasize…”  
> * **Background:** “This place lightly colors…”

## **6\. Planet-on-Angle Grammar**

Each planet keeps its core meaning from the master grammar, but the angle changes how it behaves.

### **Sun Lines**

> * **Sun \+ AC:** Identity becomes more embodied. The person may feel more visible, self-directed, or personally present. *(This location asks you to take up space as yourself.)*  
> * **Sun \+ DC:** Identity is clarified through relationship. Other people reflect the person back to themselves. *(This location teaches selfhood through mirrors, partners, clients, and open others.)*  
> * **Sun \+ MC:** Public visibility, reputation, leadership, recognition. *(This location makes it harder to hide. It favors being seen, named, recognized, or professionally centered.)*  
> * **Sun \+ IC:** Private identity, family, roots, inner life. *(This location brings the question of belonging back to the center.)*

### **Moon Lines**

> * **Moon \+ AC:** Body, mood, instinct, sensitivity, daily rhythm become immediate. *(This place makes your emotional and bodily responses louder.)*  
> * **Moon \+ DC:** Emotional needs are met or triggered through others. *(This place makes relationships emotionally instructive, sometimes nurturing and sometimes reactive.)*  
> * **Moon \+ MC:** Care, responsiveness, public sensitivity, visibility through emotional labor. *(This place may make you publicly known for care, sensitivity, family themes, or emotional availability.)*  
> * **Moon \+ IC:** Home, belonging, ancestry, retreat, private emotional life. *(This place strongly activates the need for home, safety, and emotional rootedness.)*

### **Mercury Lines**

> * **Mercury \+ AC:** Mental agility, speaking, learning, movement, identity through language. *(This place makes you more mentally visible and verbally immediate.)*  
> * **Mercury \+ DC:** Contracts, conversations, clients, negotiation, social data. *(This place brings people who make you think, talk, explain, negotiate, and translate.)*  
> * **Mercury \+ MC:** Writing, teaching, commerce, messaging, public communication. *(This place favors being known for your mind, voice, analysis, or communication.)*  
> * **Mercury \+ IC:** Private study, writing from retreat, family communication, mental roots. *(This place turns the mind inward and may make home or ancestry something to analyze, write, or name.)*

### **Venus Lines**

> * **Venus \+ AC:** Beauty, pleasure, charm, receptivity, embodied attraction. *(This place makes Venus more visible through your body, style, ease, and relational presence.)*  
> * **Venus \+ DC:** Partnership, attraction, social ease, relational magnetism. *(This place tends to bring Venus through other people: affection, attraction, diplomacy, or value-based relationship.)*  
> * **Venus \+ MC:** Public appeal, aesthetics, art, reputation, social grace, values in career. *(This place can make your Venus visible to the public. It is useful for art, beauty, social connection, branding, and value-centered work.)*  
> * **Venus \+ IC:** Comfort, sweetness, beauty in the home, private pleasure, belonging. *(This place asks whether your private life can become softer, more beautiful, and more worth inhabiting.)*

### **Mars Lines**

> * **Mars \+ AC:** Drive, heat, assertion, conflict, courage in the body. *(This place increases urgency, physical drive, and the need to act directly.)*  
> * **Mars \+ DC:** Conflict, attraction, competition, sexual charge, confrontation through others. *(This place brings Mars through other people. It can be motivating, provocative, confrontational, or highly charged.)*  
> * **Mars \+ MC:** Ambition, leadership, competition, visible effort, professional heat. *(This place pushes career movement, but it may also increase conflict with authority or pressure to prove yourself.)*  
> * **Mars \+ IC:** Domestic conflict, renovation, survival heat, anger at the root. *(This place can stir private anger, restlessness, or the need to defend your home and foundations.)*

### **Jupiter Lines**

> * **Jupiter \+ AC:** Growth, confidence, visibility, appetite, expansion of identity. *(This place makes the self feel larger, more possible, and more willing to take up space.)*  
> * **Jupiter \+ DC:** Benefactors, teachers, allies, generous partners, relational expansion. *(This place brings growth through other people, but it can also attract over-promising or inflated expectations.)*  
> * **Jupiter \+ MC:** Career growth, recognition, teaching, publishing, public opportunity. *(This place supports professional expansion, visibility, and larger-scale ambition.)*  
> * **Jupiter \+ IC:** Belonging, spacious home, family growth, inner faith. *(This place can make the private life feel larger, more generous, or more philosophically rooted.)*

### **Saturn Lines**

> * **Saturn \+ AC:** Discipline, heaviness, maturity, bodily seriousness, self-definition through limits. *(This place makes life feel more serious and self-responsible. It can build strength, but rarely feels light.)*  
> * **Saturn \+ DC:** Duty, commitment, isolation, age gaps, formal relationships, relational testing. *(This place brings Saturn through others: commitments, boundaries, obligations, or loneliness that teaches discernment.)*  
> * **Saturn \+ MC:** Career responsibility, authority, slow achievement, reputation pressure. *(This place is demanding but potentially durable. It favors mastery, structure, and long-term public credibility.)*  
> * **Saturn \+ IC:** Ancestry, family burden, emotional austerity, private responsibility. *(This place can feel heavy at the root. It may ask for maturity around home, family, history, or private grief.)*

### **Uranus Lines**

> * **Uranus \+ AC:** Freedom, disruption, reinvention, nervous energy, unusual identity expression. *(This place electrifies the self. It may support reinvention, but it can also feel unstable or overstimulating.)*  
> * **Uranus \+ DC:** Unpredictable relationships, freedom needs, unconventional partners. *(This place brings surprises through others. Relationships may be exciting, unstable, liberating, or difficult to pin down.)*  
> * **Uranus \+ MC:** Public disruption, innovation, unconventional career, sudden visibility shifts. *(This place can awaken a more radical public role, especially in technology, innovation, activism, or outsider visibility.)*  
> * **Uranus \+ IC:** Unsettled home, unconventional family patterns, private liberation. *(This place may make it hard to settle conventionally, but it can free the person from inherited expectations.)*

### **Neptune Lines**

> * **Neptune \+ AC:** Sensitivity, mystique, porous identity, spiritualized presence. *(This place softens the self. It can be inspiring, artistic, and spiritually open, but may blur identity or drain clarity.)*  
> * **Neptune \+ DC:** Projection, idealization, spiritual connection, unclear partners. *(This place brings Neptune through others. It can feel magical or compassionate, but boundaries must be watched carefully.)*  
> * **Neptune \+ MC:** Artistic visibility, spiritual/public calling, glamour, confusion around career. *(This place can make the public image more inspired or elusive. It may support art and spiritual work, but not always practical clarity.)*  
> * **Neptune \+ IC:** Retreat, dreams, ancestral fog, spiritual home, emotional permeability. *(This place can feel like a dream at the root. It may be healing for retreat, but difficult for grounded domestic clarity.)*

### **Pluto Lines**

> * **Pluto \+ AC:** Intensity, transformation, power, survival, profound self-confrontation. *(This place intensifies the self. It can be empowering, but it rarely feels casual.)*  
> * **Pluto \+ DC:** Power dynamics, obsession, transformative relationships, shadow projection. *(This place brings Pluto through others. Relationships may become catalytic, consuming, exposing, or deeply transformative.)*  
> * **Pluto \+ MC:** Public power, ambition, high-stakes career transformation, reputation intensity. *(This place can intensify public life. It may support profound ambition or influence, but also exposes power dynamics.)*  
> * **Pluto \+ IC:** Ancestral excavation, private transformation, family shadow, psychological depth. *(This place works below the surface. It may bring buried emotional or family material into unavoidable awareness.)*

## **7\. Relocated House Shift Grammar**

A relocated chart changes house emphasis. This does not erase the natal chart. It shows where natal functions become more situationally active in a specific location.  
**Formula** Natal \[Planet\] moves from natal \[House A\] emphasis into relocated \[House B\] emphasis.  
**Plain-Language Version** In this place, your \[Planet\] expresses less through \[Natal House A\] by default and becomes more active through \[Relocated House B\] situations.  
**Example: Natal Venus in the 12th relocates to the 10th.**

> * **Interpretation:** A private, hidden, retreat-oriented Venus becomes more public-facing in this location. Art, beauty, pleasure, values, and relationship themes may be less hidden here and more connected to visibility, reputation, or vocation.

**Required Safety Note**

> * **Do not phrase this as:** *Your Venus becomes a 10th-house Venus.*  
> * **Use:** *In this location, Venus expresses through 10th-house circumstances more strongly.*

## **8\. Evidence Hierarchy**

The report should not treat every factor equally.  
**Highest Priority Evidence**

> 1. Close angularity: planet within tight distance band of AC/DC/MC/IC line  
> 2. Exact relocated angle contacts  
> 3. Relocated house shifts involving Sun, Moon, chart ruler, Venus, Mars, Saturn, Jupiter  
> 4. Repeated themes across multiple factors  
> 5. Natal condition of the emphasized planet

**Medium Priority Evidence** 6\. Moderate-distance angularity 7\. Supporting relocated house emphasis 8\. Benefic/malefic balance by angular contact 9\. Natal aspect patterns activated by location emphasis  
**Lower Priority Evidence** 10\. Far-distance lines 11\. Minor bodies unless extremely prominent 12\. Speculative symbolic layering not supported by calculated factors

## **9\. Scoring Model v0.1**

The score should not create a universal “best place.” It should create category-specific resonance.  
**Category Scores**  
`{`  
  `"visibility": "career, reputation, being seen, public role",`  
  `"belonging": "home, roots, emotional safety, private restoration",`  
  `"relationship": "partners, clients, collaborators, mirrors",`  
  `"embodiment": "body, identity, vitality, daily self-direction",`  
  `"ease": "supportive flow, social softness, pleasure, spaciousness",`  
  `"pressure": "challenge, intensity, work, confrontation, maturity",`  
  `"creative_signal": "art, expression, romance, inspiration, play",`  
  `"spiritual_signal": "retreat, intuition, dissolution, liminality"`  
`}`

**Example Scoring Logic**  
`{`  
  `"venus_mc_close": {`  
    `"visibility": 4,`  
    `"ease": 3,`  
    `"creative_signal": 4,`  
    `"relationship": 2`  
  `},`  
  `"saturn_ic_exact": {`  
    `"belonging": -2,`  
    `"pressure": 5,`  
    `"embodiment": -1,`  
    `"long_term_stability": 3`  
  `},`  
  `"mars_dc_active": {`  
    `"relationship": 3,`  
    `"pressure": 4,`  
    `"embodiment": 2`  
  `}`  
`}`

**Tone Rule** A high pressure score does not mean “bad.” It means the place demands more adaptation, stamina, boundaries, or maturity.

## **10\. Place Resonance Report Sections**

**1\. Location Snapshot**

> * **Purpose:** Orient the reader.  
> * **Includes:** Selected location, Distance from birth place/current location (if relevant), Calculation system, Top 3–5 signatures, Overall resonance summary.

**2\. Main Place Signature**

> * **Purpose:** Identify the strongest message.  
> * **Formula:** The dominant signature in \[Place\] is \[Planet\] \+ \[Angle\], supported by \[Relocated House\].

**3\. What This Place Amplifies**

> * **Purpose:** Explain what becomes louder.  
> * **Use direct language:** *This place emphasizes... This place makes it harder to ignore... This place repeatedly points toward...*

**4\. What This Place Asks From You**

> * **Purpose:** Practical guidance.  
> * **Use resolute but non-fatalistic language:** *This place asks for... This place will not work well if... This place becomes more supportive when...*

**5\. Gifts / Supports**

> * **Purpose:** Name what is genuinely helpful.  
> * **Formula:** *The support here is... This location can help you access... The easiest doorway is...*

**6\. Friction / Cost**

> * **Purpose:** Name the strain without euphemism.  
> * **Formula:** *The cost of this place is... The pressure point is... This location may become difficult when...*

**7\. Best Uses**

> * **Purpose:** Commercial and practical clarity.  
> * **Good for:** Career visibility, retreat, dating, study, healing, creative work, rebuilding, short visit, long-term relocation.

**8\. Not Ideal For**

> * **Purpose:** Specific guidance.  
> * **Less ideal for:** Rest, anonymity, financial stability, emotional softness, romantic consistency, public ambition.

**9\. Technical Appendix**

> * **Purpose:** Auditability.  
> * **Includes:** Relocated chart angles, Nearest planetary lines, Distance to lines, Orb/distance band, Relocated house changes, Natal condition notes, Calculation caveats, Birth time sensitivity.

## **11\. Between Places Grammar**

The comparison product should avoid declaring one location universally superior.  
**Formula**

> * \[Place A\] is stronger for \[Category X\].  
> * \[Place B\] is stronger for \[Category Y\].  
> * \[Place C\] is more demanding but more transformative.

**Category Winner Language**

> * Best for visibility:  
> * Best for restoration:  
> * Best for relationship:  
> * Best for creative risk:  
> * Most demanding:  
> * Most stabilizing:  
> * Most unlike natal baseline:  
> * Most familiar:  
> * Best short-term catalyst:  
> * Best long-term container:

**Example:** Seattle is the stronger visibility location. Spokane is the stronger restoration location. Alton is the more demanding containment location, especially if the goal is movement, social renewal, or sensory spaciousness.

## **12\. Safety and Uncertainty Language**

Astrocartography should be useful without becoming coercive.  
**Required Language Principles**

> * **Use:**  
  * *This place emphasizes...*  
  * *This location may support...*  
  * *This signature suggests...*  
  * *This becomes more likely when...*  
  * *This is stronger if the birth time is accurate...*  
> * **Avoid:**  
  * *You must move here.*  
  * *This place will ruin your life.*  
  * *This place guarantees love.*  
  * *This is your destined city.*  
  * *You cannot succeed here.*

**Strong but Ethical Phrasing (The system can say):**

> * *This is not a neutral location for you.*  
> * *This place appears more demanding than restorative.*  
> * *This location is better used as a catalyst than a refuge.*  
> * *This place supports visibility more than privacy.*  
> * *This place may be socially active but emotionally expensive.*

*(This gives the report teeth without pretending to be fate.)*

## **13\. Developer Data Model**

**Location Result Object**  
`{`  
  `"location_id": "seattle_wa_us",`  
  `"display_name": "Seattle, Washington, United States",`  
  `"coordinates": {`  
    `"lat": 47.6062,`  
    `"lon": -122.3321`  
  `},`  
  `"relocated_angles": {`  
    `"asc": 0.0,`  
    `"mc": 0.0,`  
    `"dc": 180.0,`  
    `"ic": 180.0`  
  `},`  
  `"nearest_lines": [`  
    `{`  
      `"planet": "venus",`  
      `"angle": "mc",`  
      `"distance_miles": 42,`  
      `"distance_band": "close",`  
      `"strength": "strong"`  
    `}`  
  `],`  
  `"relocated_house_positions": [`  
    `{`  
      `"body": "venus",`  
      `"natal_house": 12,`  
      `"relocated_house": 10,`  
      `"change_type": "private_to_public"`  
    `}`  
  `],`  
  `"dominant_categories": [`  
    `"visibility",`  
    `"creative_signal",`  
    `"relationship"`  
  `],`  
  `"pressure_categories": [`  
    `"public_exposure",`  
    `"relational_expectation"`  
  `]`  
`}`

## **14\. Content Block Schema**

`{`  
  `"block_id": "astro_venus_mc_close",`  
  `"planet": "venus",`  
  `"angle": "mc",`  
  `"distance_band": "close",`  
  `"category_weights": {`  
    `"visibility": 4,`  
    `"ease": 3,`  
    `"creative_signal": 4,`  
    `"relationship": 2`  
  `},`  
  `"core_interpretation": "This location makes Venus public-facing. Beauty, connection, values, pleasure, aesthetics, and social ease are more likely to become visible through reputation, work, or public presence.",`  
  `"gift": "This can support art, branding, social recognition, relational ease, and being received more warmly by others.",`  
  `"friction": "The pressure is that private desires may become public, and approval can become more seductive than genuine alignment.",`  
  `"advice": "Use this place to let your values be seen. Do not over-adapt your beauty, charm, or relational gifts for approval."`  
`}`

## **15\. Final Interpretive Rule**

A location should be interpreted through repeated evidence.

> * One Venus line does not mean “love city.”  
> * One Saturn line does not mean “bad city.”  
> * One Pluto line does not mean “danger.”

**The report should ask:**

> * What repeats?  
> * What is closest?  
> * What is angular?  
> * What changes house emphasis?  
> * What matches or contradicts the natal baseline?  
> * What category does this place clearly serve?  
> * What does this place cost?

The best astrocartography report is not the one that says “move here.”  
**It is the one that says:**

> * This is what the place appears to activate.  
> * This is what it is good for.  
> * This is what it will likely ask from you.  
> * This is how to use it wisely.