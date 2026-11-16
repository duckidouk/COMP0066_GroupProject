'''
Run this program to insert the resources into the database.
Chose these 25 resources from the most popular ones on the website.
Have manually checked that these resources are all working.

Future classification:
emotion tag after building the real emotion table
music/guided with music/guided without music
audio/video(actually only 1 video...)
male/female voice
'''

import sqlite3

conn = sqlite3.connect("therapy_link.db")
cursor = conn.cursor()

conn.execute("PRAGMA foreign_keys = ON;") 

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

conn.executemany("INSERT OR IGNORE INTO resources (name, url) VALUES(?,?)",resources)
                                                           
conn.commit()

conn.close()
