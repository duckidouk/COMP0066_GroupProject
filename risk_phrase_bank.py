"""Phrase bank for the journal risk alert (used by risk_alert.py).

TWO TIERS
  BANK        ALERT tier: the entry is saved AND an urgent email goes to the MHWP and the admins.
  WATCH_BANK  WATCH tier: the entry is saved and the patient sees support contacts, but nobody is emailed.
              These phrases (hopelessness, feeling trapped, feeling like a burden) are warning signs
              but are common in ordinary low mood and exam stress, so emailing for them would flood
              the MHWPs and teach them to ignore alerts.

SOURCES (cite these in the report)
  1. Columbia Suicide Severity Rating Scale (C-SSRS), screening version, cssrs.columbia.edu.
     The ALERT groups follow its steps: wish to be dead, active thoughts, methods, intent or plan,
     preparatory acts, past attempts.
  2. Suicide Risk Lexicon v1.0, github.com/danielmlow/construct-tracker (Apache License 2.0), described in
     PMC13614521. Clinician rated "prototypical" phrases for passive ideation, active ideation and
     planning, lethal means, self injury, and other suicidal language were used as a checklist.
  3. Youth Suicide Lexicon, github.com/pab2163/youth_suicide_lexicon (MIT License), Bloom, Treves et al.
     (2025), PMC13669378. Used for slang, spelling variants and the idea of requiring a purpose phrase
     next to a means word ("pills ... to die").
  4. NIMH "Warning Signs of Suicide", nimh.nih.gov (talk about wanting to die, being a burden, feeling
     trapped or hopeless, having no reason to live).
  The patterns below are written by us as short regular expressions. We did not copy the lexicon files.
  We chose short, specific phrases and left out anything the authors' own papers show produces many
  false alarms (single words such as "cut", "gun", "pills", "kill me", "give up").

LIMITS (say these in the report)
  Keyword lists ignore context (negation, jokes, quotes, song lyrics). The youth lexicon paper reports
  precision of about 0.57, and only a small share of flagged entries were genuine first person current
  ideation. This bank is not clinically validated. Have a lecturer or tutor look at it.

FORMAT
  Each entry is (pattern, example). The pattern is a regular expression matched on whole words against
  text that has been cleaned: lower case, punctuation removed, apostrophes removed (don't -> dont),
  spaces collapsed. The example is a sentence that must match. The test file checks every example, so
  a pattern with a typo is caught at once. To add a phrase, add one (pattern, example) line to the right
  group and run test_risk_alert.py.
"""

# People words used for harm to others. A closed list avoids false alarms such as "hurt my back"
# or "kill my battery".
PEOPLE = (r"him|her|them|someone|somebody|everyone|people|you|my (mum|mom|dad|wife|husband|partner|boyfriend|"
          r"girlfriend|kids|children|son|daughter|brother|sister|boss|teacher|colleague|colleagues|family|"
          r"friend|friends|neighbour|neighbor|ex)")

BANK = {
    "harm to self": {
        "1 wish to be dead": [
            (r"wish(ed)? (i|that i) (was|were) dead", "I wish I was dead"),
            (r"wish i (wasnt|was not|werent|were not) alive", "I wish I wasn't alive"),
            (r"sleep and (never|not) wake up", "I just want to go to sleep and not wake up"),
            (r"(would|will) (not|never) wake up", "I wish I would not wake up"),
            (r"never wake up", "I hope I never wake up"),
            (r"dont want to wake up", "I don't want to wake up"),
            (r"(want to|going to|gonna) sleep forever", "I just want to sleep forever"),
            (r"wish i (had )?never (been born|woke up)", "I wish I had never been born"),
            (r"better off dead", "everyone would be better off dead"),
            (r"better off without me", "they are better off without me"),
            (r"want(ed)? to die", "I want to die"),
            (r"wanna die", "I wanna die"),
            (r"wish i (could|would) die", "I wish I could die"),
            (r"no reason to (live|go on)", "there is no reason to live"),
            (r"no point (in|to) (living|life|going on|carrying on)", "there is no point in living"),
            (r"nothing (left )?to live for", "I have nothing to live for"),
            (r"not worth living", "life is not worth living"),
            (r"(isnt|is not|aint) worth living", "my life isn't worth living"),
            (r"done with (my|this) life", "I am done with this life"),
            (r"(dont|do not) want to be here any ?more", "I don't want to be here anymore"),
            (r"(dont|do not) want to be here any ?more", "I do not want to be here any more"),
            (r"(dont|do not) want to exist", "I don't want to exist"),
            (r"wish i (didnt|did not) exist", "I wish I didn't exist"),
            (r"i (deserve to|should|ought to) die", "I deserve to die"),
            (r"(no one|nobody|noone) (will|would) miss me", "no one will miss me"),
            (r"(want|wanna|wish|hope)\b.{0,15}\bcease to exist", "I want to cease to exist"),
            (r"(check|checking) out (for good|forever)", "I am ready to check out for good"),
            (r"end(ing)? my (pain|suffering)", "I want to end my suffering"),
        ],
        "2 active thoughts, slang and spelling variants": [
            (r"kill(ing)? myself", "I keep thinking about killing myself"),
            (r"k[i1]ll(ing)? my(self|3lf|s3lf|se1f)", "k1ll my3lf"),
            (r"kms", "kms"),
            (r"end(ing)? my (own )?life", "I'm thinking about ending my life"),
            (r"tak(e|ing) my own life", "I might take my own life"),
            (r"suicide", "I keep thinking about suicide"),
            (r"suicidal", "feeling suicidal today"),
            (r"sucide|suiside|suicde", "thinking about sucide"),
            (r"[s5]u[i1]c[i1]d(e|al)", "5uic1de"),
            (r"end it all", "I just want to end it all"),
            (r"un ?aliv(e|ed|ing) (my ?self|me)", "I want to unalive myself"),
            (r"delete my ?self", "I want to delete myself"),
            (r"do(ing)? myself in", "I'm going to do myself in"),
        ],
        "3 thinking about methods": [
            (r"hang(ing)? myself", "I thought about hanging myself"),
            (r"shoot(ing)? myself", "I could shoot myself"),
            (r"eat(ing)? a (bullet|gun)", "I might eat a bullet"),
            (r"blow(ing)? my brains? out", "I want to blow my brains out"),
            (r"blow(ing)? myself up", "I could blow myself up"),
            (r"set(ting)? myself on fire|burn(ing)? myself alive", "I want to set myself on fire"),
            (r"electrocut(e|ing) myself", "I could electrocute myself"),
            (r"drown(ing)? myself", "I want to drown myself"),
            (r"drink(ing)? myself to death", "I am drinking myself to death"),
            (r"jump(ing)? (off|from) (a|the|my) (bridge|building|roof|cliff|balcony)", "I want to jump off the bridge"),
            (r"jump(ing)? in front of (a|the) (train|bus|car|lorry|truck)", "I want to jump in front of a train"),
            (r"slit(ting)? my wrists", "I thought about slitting my wrists"),
            (r"step(ping)? in front of (a|the) (train|bus|car|lorry)", "I could step in front of a train"),
            (r"cord around my neck", "I put a cord around my neck"),
            (r"noose", "I made a noose"),
            (r"(suicide|exit) bag", "I read about an exit bag"),
            (r"tak(e|ing) all (of )?my (pills|tablets|medication)", "I could take all my pills"),
            (r"swallow(ing)? all (of )?my (pills|tablets|medication)", "I want to swallow all my tablets"),
            (r"enough (pills|tablets) to (die|kill|end|do it)", "I have enough pills to die"),
            (r"how many (pills|tablets) (to|would|will|does it take to) (die|kill|overdose)", "how many pills to die"),
            (r"lethal dose", "what is a lethal dose"),
            (r"overdose", "I took an overdose"),
            (r"painless way to (die|go)", "I am looking for a painless way to die"),
            (r"(easy|easiest|quickest|fastest) way to (die|kill myself|end it)", "the easiest way to die"),
            (r"how (i|to) (could )?(kill myself|end my life|die)", "I looked up how to die"),
            # a means word followed shortly by a purpose phrase, so "pills" alone never triggers
            (r"(pills|tablets|rope|gun|bleach|knife|razor|medication)\b.{0,30}\b"
             r"(to die|to kill myself|to end it|to end my life|so i can die)", "I bought pills to die"),
        ],
        "4 intent or plan": [
            (r"i have a plan to (die|kill myself|end it|end my life)", "I have a plan to end my life"),
            (r"i know how i (will|am going to) (do it|die|kill myself)", "I know how I will do it"),
            (r"(going to|will) (do it|end it) (tonight|today|tomorrow)", "I am going to do it tonight"),
            (r"tonight is the night", "tonight is the night"),
            (r"this is my last (night|day|message|entry)", "this is my last entry"),
            (r"i wont be here (tomorrow|next week)", "I won't be here tomorrow"),
            (r"(wont|will not) be (here|around) (much )?longer", "I won't be around much longer"),
        ],
        "5 preparatory acts": [
            (r"suicide note", "I wrote a suicide note"),
            (r"goodbye (letter|note)", "I wrote a goodbye letter"),
            (r"giving away my (things|stuff|belongings|possessions)", "I am giving away my things"),
            (r"final goodbye", "this is my final goodbye"),
            (r"say (my )?goodbye to everyone", "I want to say goodbye to everyone"),
            (r"(collecting|saving up|stockpiling) (my )?(pills|tablets|medication)", "I have been saving up my pills"),
            (r"(got|bought|buying|getting) (a )?(gun|rope|razor) (to|so i can) (kill|end|hang|die)",
             "I bought a rope to hang myself"),
        ],
        "6 past attempts": [
            (r"tried to (kill myself|end my life|take my own life|die)", "I tried to end my life last year"),
            (r"attempted suicide", "I attempted suicide"),
            (r"suicide attempt", "after my suicide attempt"),
            (r"took too many (pills|tablets)", "I took too many pills"),
        ],
        "7 self harm": [
            (r"hurt(ing)? myself", "I want to hurt myself"),
            (r"harm(ing)? myself", "I am going to harm myself"),
            (r"self harm(ing|ed)?", "I started self harming again"),
            (r"cut(ting)? myself", "I cut myself"),
            (r"burn(ing|ed|t)? myself", "I burned myself"),
            (r"wound(ed|ing)? myself", "I wounded myself"),
            (r"carve my skin", "I want to carve my skin"),
            (r"nssi", "NSSI"),
        ],
    },
    "harm to others": {
        "threats and intent": [
            (r"(kill|killing|murder|murdering|shoot|shooting|stab|stabbing|strangle|strangling|unalive|unaliving) ("
             + PEOPLE + ")", "I want to kill him"),
            (r"(hurt|hurting|harm|harming|attack|attacking|beat up|beating up) (" + PEOPLE + "|others)",
             "I will hurt someone"),
            (r"want(ed)? to hurt (someone|somebody|people|others)", "I want to hurt people"),
            (r"shoot up (the|my) (school|office|class|work|college|university)", "I want to shoot up the school"),
            (r"bring(ing)? a (gun|knife|weapon) to (school|work|college|university)",
             "I am going to bring a knife to work"),
        ],
    },
}

# WATCH tier: support contacts for the patient, NO email. Same (pattern, example) format.
WATCH_BANK = {
    "hopelessness": [
        (r"hopeless", "I feel hopeless"),
        (r"no hope", "there is no hope"),
        (r"(theres|there is) no hope", "there's no hope"),
        (r"no future", "I have no future"),
        (r"nothing can help", "nothing can help me"),
        (r"beyond help", "I am beyond help"),
        (r"nothing (will|is going to) (ever )?(change|get better)", "nothing will ever get better"),
    ],
    "feeling trapped": [
        (r"no way out", "there is no way out"),
        (r"trapped", "I feel trapped"),
        (r"no escape", "there is no escape"),
        (r"cant (go on|cope|take it|take this|do this|live like this|live with this)( any ?more)?",
         "I can't take it anymore"),
    ],
    "feeling like a burden": [
        (r"(i am|im|i feel like|feel like) a burden", "I feel like a burden"),
        (r"burden (to|on) (everyone|others|my family|my friends|my parents)", "I am a burden to my family"),
        (r"sorry for existing", "I am sorry for existing"),
    ],
    "pain and meaning": [
        (r"i hate my life", "I hate my life"),
        (r"unbearable (pain|feeling)|(pain|feeling) is unbearable", "the pain is unbearable"),
        (r"nothing matters", "nothing matters"),
        (r"whats the point", "what's the point"),
    ],
}

# Sentences that must NOT raise an ALERT. The test file checks these too.
NOT_ALERT_EXAMPLES = [
    "I had a good day and went for a walk",
    "Work was hard but I am killing it at the gym",
    "The meeting killed my afternoon",
    "I want to kill the spider in my room",
    "My mood is low but I talked to a friend",
    "I am tired of this weather",
    "We watched a film about a shark attack",
    "I hurt my back lifting a box",
    "I need to kill my phone battery saver",
    "I jumped off the diving board and loved it",
    "My sister and I went for a run",
    "I feel hopeless about my exam but I will revise tonight",
    "We beat them at chess",
    "My sister will kill me if I am late",
    "I almost got hit by the train timetable change",
    "I deleted my life insurance form by mistake",
    "I bought pills for my cold from the chemist",
    "The knife and fork are in the drawer",
    "I should diet less",
    "The company will cease to exist if it loses the contract",
]
