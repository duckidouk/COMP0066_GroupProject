'''
Run this program to insert the emotions,resources and resource_emotions table into the database.
Chose these 25 resources from the most popular ones on the website.
Have manually checked that these resources are all working.
Emotions are manually linked to resources.
'''

import sqlite3

conn = sqlite3.connect("therapy_link.db")
cursor = conn.cursor()

conn.execute("PRAGMA foreign_keys = ON;") 

emotions = [
    ("Stress", "Feeling under pressure, overwhelmed or unable to cope with demands such as work, study or life changes."),
    ("Anxiety", "Feeling worried, nervous, tense or afraid, sometimes with physical signs like a racing heart or restlessness."),
    ("Low mood and depression", "Feeling sad, down, lonely or hopeless, losing interest in things, including after a loss or bereavement."),
    ("Sleep problems", "Difficulty falling asleep, staying asleep or waking up feeling rested. Insomnia."),
    ("Tiredness/Low energy", "Feeling exhausted.")
]

resources = [
    ("Beginner's Body Scan","https://insighttimer.com/dorakamau/guided-meditations/beginners-body-scan-3"),
    ("End Of Day Meditation", "https://insighttimer.com/tramainecato/guided-meditations/end-of-day-meditation-2"),
    ("Mindfulness Of Body And Breath", "https://insighttimer.com/markwilliams/guided-meditations/mindfulness-of-body-and-breath-3"),
    ("Rapid Deep Rest (NSDR)", "https://insighttimer.com/allyboothroyd/guided-meditations/rapid-deep-rest-nsdr"),
    ("Everything Will Be OK", "https://insighttimer.com/marhealy/guided-meditations/everything-will-be-ok"),
    ("Stop The Anxiety Spiral: The Butterfly Hug", "https://insighttimer.com/iambeawalker/video-guided-meditations/stop-the-anxiety-spiral-the-butterfly-hug"),
    ("Unwind Into Surrender: 10-Minute Release & Relinquish", "https://insighttimer.com/sarahblondin/guided-meditations/learning-to-surrender"),
    ("Self-Compassion Break", "https://insighttimer.com/kristinneff9711/guided-meditations/self-compassion-break-19"),
    ("Stress & Anxiety Buster: Two-Minute Mindful Release", "https://insighttimer.com/davidji/guided-meditations/stress-buster-two-minute-mindful-release"),
    ("Holding On, Letting Go", "https://insighttimer.com/ruthking/guided-meditations/holding-on-letting-go"),
    ("Ten Breaths Meditation", "https://insighttimer.com/marywaldon/guided-meditations/ten-breaths-meditation"),
    ("5 Minute Morning Meditation", "https://insighttimer.com/fatimafarmer/guided-meditations/guided-meditation-5-minute-morning-meditation"),
    ("Vagus Nerve Breathing Meditation", "https://insighttimer.com/camillasacredallerup131/guided-meditations/vagus-nerve-breathing-meditation-2"),
    ("Rain & Thunder Sound Therapy", "https://insighttimer.com/desh/video-guided-meditations/rain-and-thunder-sound-therapy"),
    ("4-7-8 Breathing Technique (With Music)", "https://insighttimer.com/tramainecato/guided-meditations/4-7-8-breathing-technique-with-music"),
    ("Re-Centering In Times Of Uncertainty", "https://insighttimer.com/alex_elle/guided-meditations/re-centering-in-times-of-uncertainty"),
    ("Let Go Of Worry And Anxiety", "https://insighttimer.com/ellenhendriksen/guided-meditations/let-go-of-worry-and-anxiety"),
    ("Floating", "https://insighttimer.com/jamesanthonywalker/video-guided-meditations/floating-2"),
    ("Deep Sleep", "https://insighttimer.com/indiemusicbox/video-guided-meditations/deep-sleep"),
    ("Yoga Nidra For Sleep", "https://insighttimer.com/jenniferpiercy/video-guided-meditations/yoga-nidra-for-sleep"),
    ("Three Hours Of Pure Relaxation", "https://insighttimer.com/indiemusicbox/video-guided-meditations/three-hours-of-pure-relaxation"),
    ("Two Hours Of Tranquility", "https://insighttimer.com/indiemusicbox/video-guided-meditations/two-hours-of-tranquility"),
    ("Deep Healing", "https://insighttimer.com/davidji/guided-meditations/deep-healing"),
    ("Healing Darkness For Sleep", "https://insighttimer.com/jenniferpiercy/guided-meditations/healing-darkness-for-sleep"),
    ("Breathing Into Sleep", "https://insighttimer.com/crystaltreeroad/guided-meditations/breathing-into-sleep")
]

resource_emotions = [
    ("Beginner's Body Scan", "Stress"),
    ("Beginner's Body Scan", "Anxiety"),

    ("End Of Day Meditation", "Stress"),
    ("End Of Day Meditation", "Tiredness/Low energy"),

    ("Mindfulness Of Body And Breath", "Anxiety"),
    ("Mindfulness Of Body And Breath", "Low mood and depression"),

    ("Rapid Deep Rest (NSDR)", "Tiredness/Low energy"),
    ("Rapid Deep Rest (NSDR)", "Sleep problems"),

    ("Everything Will Be OK", "Anxiety"),
    ("Everything Will Be OK", "Low mood and depression"),

    ("Stop The Anxiety Spiral: The Butterfly Hug", "Anxiety"),

    ("Unwind Into Surrender: 10-Minute Release & Relinquish", "Stress"),

    ("Self-Compassion Break", "Low mood and depression"),
    ("Self-Compassion Break", "Stress"),

    ("Stress & Anxiety Buster: Two-Minute Mindful Release", "Stress"),
    ("Stress & Anxiety Buster: Two-Minute Mindful Release", "Anxiety"),

    ("Holding On, Letting Go", "Low mood and depression"),
    ("Holding On, Letting Go", "Anxiety"),

    ("Ten Breaths Meditation", "Anxiety"),
    ("Ten Breaths Meditation", "Stress"),

    ("5 Minute Morning Meditation", "Stress"),
    ("5 Minute Morning Meditation", "Anxiety"),
    ("5 Minute Morning Meditation", "Low mood and depression"),
    ("5 Minute Morning Meditation", "Sleep problems"),
    ("5 Minute Morning Meditation", "Tiredness/Low energy"),

    ("Vagus Nerve Breathing Meditation", "Anxiety"),
    ("Vagus Nerve Breathing Meditation", "Stress"),

    ("Rain & Thunder Sound Therapy", "Sleep problems"),

    ("4-7-8 Breathing Technique (With Music)", "Anxiety"),
    ("4-7-8 Breathing Technique (With Music)", "Sleep problems"),

    ("Re-Centering In Times Of Uncertainty", "Anxiety"),
    ("Re-Centering In Times Of Uncertainty", "Stress"),

    ("Let Go Of Worry And Anxiety", "Anxiety"),

    ("Floating", "Stress"),
    ("Floating", "Anxiety"),
    ("Floating", "Low mood and depression"),
    ("Floating", "Sleep problems"),
    ("Floating", "Tiredness/Low energy"),

    ("Deep Sleep", "Sleep problems"),

    ("Yoga Nidra For Sleep", "Sleep problems"),
    ("Yoga Nidra For Sleep", "Tiredness/Low energy"),

    ("Three Hours Of Pure Relaxation", "Sleep problems"),
    ("Three Hours Of Pure Relaxation", "Stress"),

    ("Two Hours Of Tranquility", "Sleep problems"),
    ("Two Hours Of Tranquility", "Stress"),

    ("Deep Healing", "Stress"),
    ("Deep Healing", "Anxiety"),
    ("Deep Healing", "Low mood and depression"),
    ("Deep Healing", "Sleep problems"),
    ("Deep Healing", "Tiredness/Low energy"),

    ("Healing Darkness For Sleep", "Sleep problems"),

    ("Breathing Into Sleep", "Sleep problems")
]

conn.executemany("INSERT OR IGNORE INTO emotions(name, description) VALUES(?,?)",emotions)
conn.executemany("INSERT OR IGNORE INTO resources(name, url) VALUES(?,?)",resources)
conn.executemany("""INSERT OR IGNORE INTO resource_emotions(resource_id, emotion_id) 
    SELECT resources.resource_id, emotions.emotion_id
    FROM resources, emotions
    WHERE resources.name = ? AND emotions.name = ?
""",resource_emotions)

                                                           
conn.commit()

conn.close()
