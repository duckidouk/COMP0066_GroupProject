import sqlite3
from datetime import datetime, time, timedelta

DATABASE_PATH = "therapy_link.db"


SAMPLE_USERS = [
    ("admin", "", "TherapyLink Administrator", "admin@therapylink.test", "admin", "2026-11-01T09:00:00"),
    ("mhwp1", "", "Dr Alex Brown", "alex.brown@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp2", "", "Dr Morgan Lee", "morgan.lee@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp3", "", "Dr Priya Shah", "priya.shah@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp4", "", "Dr Daniel Green", "daniel.green@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp5", "", "Dr Aisha Khan", "aisha.khan@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp6", "", "Dr Oliver Scott", "oliver.scott@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp7", "", "Dr Sofia Martinez", "sofia.martinez@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp8", "", "Dr Ethan Wright", "ethan.wright@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp9", "", "Dr Grace Chen", "grace.chen@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp10", "", "Dr Noah Patel", "noah.patel@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp11", "", "Dr Maya Wilson", "maya.wilson@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp12", "", "Dr Lucas Evans", "lucas.evans@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp13", "", "Dr Amara Okafor", "amara.okafor@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp14", "", "Dr Henry Adams", "henry.adams@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp15", "", "Dr Leila Hassan", "leila.hassan@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp16", "", "Dr Benjamin Turner", "benjamin.turner@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp17", "", "Dr Chloe Robinson", "chloe.robinson@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp18", "", "Dr Samuel Brooks", "samuel.brooks@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp19", "", "Dr Fatima Ali", "fatima.ali@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp20", "", "Dr James Cooper", "james.cooper@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp21", "", "Dr Elena Rossi", "elena.rossi@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp22", "", "Dr William Parker", "william.parker@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp23", "", "Dr Nia Williams", "nia.williams@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp24", "", "Dr Arthur Bell", "arthur.bell@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp25", "", "Dr Zara Ahmed", "zara.ahmed@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp26", "", "Dr Leo Campbell", "leo.campbell@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp27", "", "Dr Emily Foster", "emily.foster@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp28", "", "Dr Yusuf Ibrahim", "yusuf.ibrahim@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp29", "", "Dr Isla Hughes", "isla.hughes@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("mhwp30", "", "Dr Theo Mitchell", "theo.mitchell@therapylink.test", "practitioner", "2026-11-01T09:00:00"),
    ("patient1", "", "Jamie Taylor", "jamie.taylor@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient2", "", "Riley Morgan", "riley.morgan@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient3", "", "Casey Bennett", "casey.bennett@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient4", "", "Jordan Kim", "jordan.kim@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient5", "", "Taylor Reed", "taylor.reed@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient6", "", "Avery Brooks", "avery.brooks@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient7", "", "Quinn Murphy", "quinn.murphy@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient8", "", "Cameron Price", "cameron.price@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient9", "", "Drew Foster", "drew.foster@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient10", "", "Harper Diaz", "harper.diaz@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient11", "", "Reese Morgan", "reese.morgan@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient12", "", "Rowan Cole", "rowan.cole@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient13", "", "Morgan Hayes", "morgan.hayes@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient14", "", "Alex Rivera", "alex.rivera@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient15", "", "Jamie Collins", "jamie.collins@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient16", "", "Riley Thompson", "riley.thompson@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient17", "", "Casey Ward", "casey.ward@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient18", "", "Jordan Price", "jordan.price@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient19", "", "Taylor James", "taylor.james@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient20", "", "Avery Scott", "avery.scott@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient21", "", "Quinn Bell", "quinn.bell@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient22", "", "Cameron Young", "cameron.young@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient23", "", "Drew King", "drew.king@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient24", "", "Harper Lewis", "harper.lewis@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient25", "", "Reese Carter", "reese.carter@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient26", "", "Rowan Mitchell", "rowan.mitchell@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient27", "", "Morgan Evans", "morgan.evans@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient28", "", "Alex Turner", "alex.turner@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient29", "", "Jamie Cooper", "jamie.cooper@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient30", "", "Riley Parker", "riley.parker@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient31", "", "Casey Adams", "casey.adams@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient32", "", "Jordan Hughes", "jordan.hughes@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient33", "", "Taylor Bennett", "taylor.bennett@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient34", "", "Avery Kim", "avery.kim@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient35", "", "Quinn Reed", "quinn.reed@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient36", "", "Cameron Brooks", "cameron.brooks@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient37", "", "Drew Murphy", "drew.murphy@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient38", "", "Harper Price", "harper.price@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient39", "", "Reese Foster", "reese.foster@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient40", "", "Rowan Diaz", "rowan.diaz@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient41", "", "Morgan Cole", "morgan.cole@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient42", "", "Alex Hayes", "alex.hayes@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient43", "", "Jamie Rivera", "jamie.rivera@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient44", "", "Riley Collins", "riley.collins@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient45", "", "Casey Thompson", "casey.thompson@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient46", "", "Jordan Ward", "jordan.ward@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient47", "", "Taylor Jameson", "taylor.jameson@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient48", "", "Avery Reed", "avery.reed@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient49", "", "Quinn Scott", "quinn.scott@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient50", "", "Cameron Bell", "cameron.bell@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient51", "", "Drew Young", "drew.young@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient52", "", "Harper King", "harper.king@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient53", "", "Reese Lewis", "reese.lewis@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient54", "", "Rowan Carter", "rowan.carter@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient55", "", "Morgan Mitchell", "morgan.mitchell@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient56", "", "Alex Evans", "alex.evans@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient57", "", "Jamie Turner", "jamie.turner@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient58", "", "Riley Cooper", "riley.cooper@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient59", "", "Casey Parker", "casey.parker@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient60", "", "Jordan Adams", "jordan.adams@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient61", "", "Taylor Hughes", "taylor.hughes@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient62", "", "Avery Bennett", "avery.bennett@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient63", "", "Quinn Kim", "quinn.kim@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient64", "", "Cameron Reed", "cameron.reed@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient65", "", "Drew Brooks", "drew.brooks@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient66", "", "Harper Murphy", "harper.murphy@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient67", "", "Reese Price", "reese.price@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient68", "", "Rowan Foster", "rowan.foster@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient69", "", "Morgan Diaz", "morgan.diaz@therapylink.test", "patient", "2026-11-01T09:00:00"),
    ("patient70", "", "Alex Cole", "alex.cole@therapylink.test", "patient", "2026-11-01T09:00:00"),
]

SAMPLE_PATIENT_PROFILES = [
    ("patient1", "emergency1@therapylink.test", "mhwp1"),
    ("patient2", "emergency2@therapylink.test", "mhwp2"),
    ("patient3", "emergency3@therapylink.test", "mhwp3"),
    ("patient4", "emergency4@therapylink.test", "mhwp4"),
    ("patient5", "emergency5@therapylink.test", "mhwp5"),
    ("patient6", "emergency6@therapylink.test", "mhwp6"),
    ("patient7", "emergency7@therapylink.test", "mhwp7"),
    ("patient8", "emergency8@therapylink.test", "mhwp8"),
    ("patient9", "emergency9@therapylink.test", "mhwp9"),
    ("patient10", "emergency10@therapylink.test", "mhwp10"),
    ("patient11", "emergency11@therapylink.test", "mhwp11"),
    ("patient12", "emergency12@therapylink.test", "mhwp12"),
    ("patient13", "emergency13@therapylink.test", "mhwp13"),
    ("patient14", "emergency14@therapylink.test", "mhwp14"),
    ("patient15", "emergency15@therapylink.test", "mhwp15"),
    ("patient16", "emergency16@therapylink.test", "mhwp16"),
    ("patient17", "emergency17@therapylink.test", "mhwp17"),
    ("patient18", "emergency18@therapylink.test", "mhwp18"),
    ("patient19", "emergency19@therapylink.test", "mhwp19"),
    ("patient20", "emergency20@therapylink.test", "mhwp20"),
    ("patient21", "emergency21@therapylink.test", "mhwp21"),
    ("patient22", "emergency22@therapylink.test", "mhwp22"),
    ("patient23", "emergency23@therapylink.test", "mhwp23"),
    ("patient24", "emergency24@therapylink.test", "mhwp24"),
    ("patient25", "emergency25@therapylink.test", "mhwp25"),
    ("patient26", "emergency26@therapylink.test", "mhwp26"),
    ("patient27", "emergency27@therapylink.test", "mhwp27"),
    ("patient28", "emergency28@therapylink.test", "mhwp28"),
    ("patient29", "emergency29@therapylink.test", "mhwp29"),
    ("patient30", "emergency30@therapylink.test", "mhwp30"),
    ("patient31", "emergency31@therapylink.test", "mhwp1"),
    ("patient32", "emergency32@therapylink.test", "mhwp2"),
    ("patient33", "emergency33@therapylink.test", "mhwp3"),
    ("patient34", "emergency34@therapylink.test", "mhwp4"),
    ("patient35", "emergency35@therapylink.test", "mhwp5"),
    ("patient36", "emergency36@therapylink.test", "mhwp6"),
    ("patient37", "emergency37@therapylink.test", "mhwp7"),
    ("patient38", "emergency38@therapylink.test", "mhwp8"),
    ("patient39", "emergency39@therapylink.test", "mhwp9"),
    ("patient40", "emergency40@therapylink.test", "mhwp10"),
    ("patient41", "emergency41@therapylink.test", "mhwp11"),
    ("patient42", "emergency42@therapylink.test", "mhwp12"),
    ("patient43", "emergency43@therapylink.test", "mhwp13"),
    ("patient44", "emergency44@therapylink.test", "mhwp14"),
    ("patient45", "emergency45@therapylink.test", "mhwp15"),
    ("patient46", "emergency46@therapylink.test", "mhwp16"),
    ("patient47", "emergency47@therapylink.test", "mhwp17"),
    ("patient48", "emergency48@therapylink.test", "mhwp18"),
    ("patient49", "emergency49@therapylink.test", "mhwp19"),
    ("patient50", "emergency50@therapylink.test", "mhwp20"),
    ("patient51", "emergency51@therapylink.test", "mhwp21"),
    ("patient52", "emergency52@therapylink.test", "mhwp22"),
    ("patient53", "emergency53@therapylink.test", "mhwp23"),
    ("patient54", "emergency54@therapylink.test", "mhwp24"),
    ("patient55", "emergency55@therapylink.test", "mhwp25"),
    ("patient56", "emergency56@therapylink.test", "mhwp26"),
    ("patient57", "emergency57@therapylink.test", "mhwp27"),
    ("patient58", "emergency58@therapylink.test", "mhwp28"),
    ("patient59", "emergency59@therapylink.test", "mhwp29"),
    ("patient60", "emergency60@therapylink.test", "mhwp30"),
    ("patient61", "emergency61@therapylink.test", "mhwp1"),
    ("patient62", "emergency62@therapylink.test", "mhwp2"),
    ("patient63", "emergency63@therapylink.test", "mhwp3"),
    ("patient64", "emergency64@therapylink.test", "mhwp4"),
    ("patient65", "emergency65@therapylink.test", "mhwp5"),
    ("patient66", "emergency66@therapylink.test", "mhwp6"),
    ("patient67", "emergency67@therapylink.test", "mhwp7"),
    ("patient68", "emergency68@therapylink.test", "mhwp8"),
    ("patient69", "emergency69@therapylink.test", "mhwp9"),
    ("patient70", "emergency70@therapylink.test", "mhwp10"),
]

SAMPLE_CONDITIONS = [
    ("Anxiety", "Persistent worry or fear that can affect daily life."),
    ("Depression", "Persistent low mood or loss of interest."),
    ("Stress", "Emotional or physical strain in response to demands."),
]

SAMPLE_PATIENT_CONDITIONS = [
    ("patient1", "Anxiety", "mhwp1"),
    ("patient2", "Stress", "mhwp2"),
    ("patient3", "Depression", "mhwp3"),
    ("patient4", "Anxiety", "mhwp4"),
    ("patient5", "Stress", "mhwp5"),
    ("patient6", "Depression", "mhwp6"),
    ("patient7", "Anxiety", "mhwp7"),
    ("patient8", "Stress", "mhwp8"),
    ("patient9", "Depression", "mhwp9"),
    ("patient10", "Anxiety", "mhwp10"),
    ("patient11", "Stress", "mhwp11"),
    ("patient12", "Depression", "mhwp12"),
    ("patient13", "Anxiety", "mhwp13"),
    ("patient14", "Stress", "mhwp14"),
    ("patient15", "Depression", "mhwp15"),
    ("patient16", "Anxiety", "mhwp16"),
    ("patient17", "Stress", "mhwp17"),
    ("patient18", "Depression", "mhwp18"),
    ("patient19", "Anxiety", "mhwp19"),
    ("patient20", "Stress", "mhwp20"),
    ("patient21", "Depression", "mhwp21"),
    ("patient22", "Anxiety", "mhwp22"),
    ("patient23", "Stress", "mhwp23"),
    ("patient24", "Depression", "mhwp24"),
    ("patient25", "Anxiety", "mhwp25"),
    ("patient26", "Stress", "mhwp26"),
    ("patient27", "Depression", "mhwp27"),
    ("patient28", "Anxiety", "mhwp28"),
    ("patient29", "Stress", "mhwp29"),
    ("patient30", "Depression", "mhwp30"),
    ("patient31", "Anxiety", "mhwp1"),
    ("patient32", "Stress", "mhwp2"),
    ("patient33", "Depression", "mhwp3"),
    ("patient34", "Anxiety", "mhwp4"),
    ("patient35", "Stress", "mhwp5"),
    ("patient36", "Depression", "mhwp6"),
    ("patient37", "Anxiety", "mhwp7"),
    ("patient38", "Stress", "mhwp8"),
    ("patient39", "Depression", "mhwp9"),
    ("patient40", "Anxiety", "mhwp10"),
    ("patient41", "Stress", "mhwp11"),
    ("patient42", "Depression", "mhwp12"),
    ("patient43", "Anxiety", "mhwp13"),
    ("patient44", "Stress", "mhwp14"),
    ("patient45", "Depression", "mhwp15"),
    ("patient46", "Anxiety", "mhwp16"),
    ("patient47", "Stress", "mhwp17"),
    ("patient48", "Depression", "mhwp18"),
    ("patient49", "Anxiety", "mhwp19"),
    ("patient50", "Stress", "mhwp20"),
    ("patient51", "Depression", "mhwp21"),
    ("patient52", "Anxiety", "mhwp22"),
    ("patient53", "Stress", "mhwp23"),
    ("patient54", "Depression", "mhwp24"),
    ("patient55", "Anxiety", "mhwp25"),
    ("patient56", "Stress", "mhwp26"),
    ("patient57", "Depression", "mhwp27"),
    ("patient58", "Anxiety", "mhwp28"),
    ("patient59", "Stress", "mhwp29"),
    ("patient60", "Depression", "mhwp30"),
    ("patient61", "Anxiety", "mhwp1"),
    ("patient62", "Stress", "mhwp2"),
    ("patient63", "Depression", "mhwp3"),
    ("patient64", "Anxiety", "mhwp4"),
    ("patient65", "Stress", "mhwp5"),
    ("patient66", "Depression", "mhwp6"),
    ("patient67", "Anxiety", "mhwp7"),
    ("patient68", "Stress", "mhwp8"),
    ("patient69", "Depression", "mhwp9"),
    ("patient70", "Anxiety", "mhwp10"),
]

SAMPLE_MOOD_ENTRIES = [
    ("patient1", 2, "Felt rested after a good night's sleep.", "2026-11-08T09:00:00"),
    ("patient1", 4, "A busy day left me feeling tense.", "2026-11-09T09:00:00"),
    ("patient1", 3, "A short walk helped me feel more settled.", "2026-11-10T09:00:00"),
    ("patient2", 5, "I felt overwhelmed by several things today.", "2026-11-08T09:00:00"),
    ("patient2", 4, "Talking with a friend helped a little.", "2026-11-09T09:00:00"),
    ("patient2", 3, "I made time to rest this afternoon.", "2026-11-10T09:00:00"),
    ("patient3", 3, "I felt calmer after taking a short walk.", "2026-11-08T09:00:00"),
    ("patient3", 4, "A busy day left me feeling tense.", "2026-11-09T09:00:00"),
    ("patient3", 2, "I slept well and felt rested today.", "2026-11-10T09:00:00"),
    ("patient4", 2, "I felt focused and ready for the day.", "2026-11-08T09:00:00"),
    ("patient4", 3, "I took a break when I needed one.", "2026-11-09T09:00:00"),
    ("patient4", 4, "I felt a little anxious this afternoon.", "2026-11-10T09:00:00"),
    ("patient5", 5, "I felt overwhelmed by my to-do list.", "2026-11-08T09:00:00"),
    ("patient5", 4, "Talking with a friend helped a little.", "2026-11-09T09:00:00"),
    ("patient5", 3, "I made time to rest this afternoon.", "2026-11-10T09:00:00"),
    ("patient6", 3, "I felt more settled after lunch.", "2026-11-08T09:00:00"),
    ("patient6", 2, "I enjoyed spending time outdoors.", "2026-11-09T09:00:00"),
    ("patient6", 3, "I managed a difficult task today.", "2026-11-10T09:00:00"),
    ("patient7", 4, "I had a stressful morning.", "2026-11-08T09:00:00"),
    ("patient7", 5, "I found it hard to switch off today.", "2026-11-09T09:00:00"),
    ("patient7", 3, "A quiet evening helped me unwind.", "2026-11-10T09:00:00"),
    ("patient8", 2, "I felt cheerful when I woke up.", "2026-11-08T09:00:00"),
    ("patient8", 3, "I felt a bit tired in the afternoon.", "2026-11-09T09:00:00"),
    ("patient8", 2, "I had a peaceful day.", "2026-11-10T09:00:00"),
    ("patient9", 4, "I was nervous about an upcoming event.", "2026-11-08T09:00:00"),
    ("patient9", 3, "I tried a breathing exercise today.", "2026-11-09T09:00:00"),
    ("patient9", 4, "I felt unsettled before bed.", "2026-11-10T09:00:00"),
    ("patient10", 3, "I felt okay after getting some fresh air.", "2026-11-08T09:00:00"),
    ("patient10", 2, "I had a good conversation today.", "2026-11-09T09:00:00"),
    ("patient10", 3, "I finished the day feeling steady.", "2026-11-10T09:00:00"),
    ("patient11", 5, "I felt under pressure at work.", "2026-11-08T09:00:00"),
    ("patient11", 4, "I took a proper lunch break today.", "2026-11-09T09:00:00"),
    ("patient11", 3, "I felt less tense by the evening.", "2026-11-10T09:00:00"),
    ("patient12", 2, "I woke up feeling hopeful.", "2026-11-08T09:00:00"),
    ("patient12", 3, "I had a low-energy afternoon.", "2026-11-09T09:00:00"),
    ("patient12", 2, "I did something kind for myself today.", "2026-11-10T09:00:00"),
    ("patient13", 3, "I kept a good pace through the day.", "2026-11-08T09:00:00"),
    ("patient13", 4, "I felt worried about a family matter.", "2026-11-09T09:00:00"),
    ("patient13", 3, "I felt more relaxed after dinner.", "2026-11-10T09:00:00"),
    ("patient14", 4, "I had a restless night and felt tired.", "2026-11-08T09:00:00"),
    ("patient14", 3, "A short break helped me reset.", "2026-11-09T09:00:00"),
    ("patient14", 2, "I felt rested after an early night.", "2026-11-10T09:00:00"),
    ("patient15", 5, "I struggled to concentrate today.", "2026-11-08T09:00:00"),
    ("patient15", 4, "I reached out to someone I trust.", "2026-11-09T09:00:00"),
    ("patient15", 3, "I felt supported by a friend today.", "2026-11-10T09:00:00"),
    ("patient16", 2, "I enjoyed a relaxed start to the day.", "2026-11-08T09:00:00"),
    ("patient16", 3, "I felt unsettled during a meeting.", "2026-11-09T09:00:00"),
    ("patient16", 2, "I felt more confident by the evening.", "2026-11-10T09:00:00"),
    ("patient17", 4, "I felt stretched by several commitments.", "2026-11-08T09:00:00"),
    ("patient17", 5, "I found today especially demanding.", "2026-11-09T09:00:00"),
    ("patient17", 4, "I gave myself time to slow down.", "2026-11-10T09:00:00"),
    ("patient18", 3, "I had a steady day overall.", "2026-11-08T09:00:00"),
    ("patient18", 2, "I felt proud of a small accomplishment.", "2026-11-09T09:00:00"),
    ("patient18", 3, "I felt tired but content today.", "2026-11-10T09:00:00"),
    ("patient19", 4, "I was uneasy about a change in plans.", "2026-11-08T09:00:00"),
    ("patient19", 3, "I made space to think things through.", "2026-11-09T09:00:00"),
    ("patient19", 2, "I felt more at ease this evening.", "2026-11-10T09:00:00"),
    ("patient20", 3, "I felt balanced between work and rest.", "2026-11-08T09:00:00"),
    ("patient20", 4, "I felt impatient during a busy afternoon.", "2026-11-09T09:00:00"),
    ("patient20", 3, "I wound down with a calming activity.", "2026-11-10T09:00:00"),
    ("patient21", 2, "I felt energised after my morning walk.", "2026-11-08T09:00:00"),
    ("patient21", 3, "I felt a little flat after lunch.", "2026-11-09T09:00:00"),
    ("patient21", 2, "I enjoyed catching up with a friend.", "2026-11-10T09:00:00"),
    ("patient22", 5, "I felt anxious about several deadlines.", "2026-11-08T09:00:00"),
    ("patient22", 4, "I broke my tasks into smaller steps.", "2026-11-09T09:00:00"),
    ("patient22", 3, "The smaller steps made today manageable.", "2026-11-10T09:00:00"),
    ("patient23", 3, "I felt comfortable with my routine today.", "2026-11-08T09:00:00"),
    ("patient23", 2, "I took time to enjoy a favourite meal.", "2026-11-09T09:00:00"),
    ("patient23", 3, "I felt calm at the end of the day.", "2026-11-10T09:00:00"),
    ("patient24", 4, "I felt distracted and needed extra breaks.", "2026-11-08T09:00:00"),
    ("patient24", 3, "I got outside for a little while.", "2026-11-09T09:00:00"),
    ("patient24", 4, "I had mixed feelings about today.", "2026-11-10T09:00:00"),
    ("patient25", 2, "I felt refreshed after a good night's sleep.", "2026-11-08T09:00:00"),
    ("patient25", 3, "I felt tense while running errands.", "2026-11-09T09:00:00"),
    ("patient25", 2, "I took a quiet moment for myself.", "2026-11-10T09:00:00"),
    ("patient26", 4, "I had trouble getting started this morning.", "2026-11-08T09:00:00"),
    ("patient26", 3, "I made progress after asking for help.", "2026-11-09T09:00:00"),
    ("patient26", 3, "I felt relieved when I finished my tasks.", "2026-11-10T09:00:00"),
    ("patient27", 3, "I kept calm during a busy day.", "2026-11-08T09:00:00"),
    ("patient27", 4, "I felt frustrated by a delay.", "2026-11-09T09:00:00"),
    ("patient27", 3, "I let go of things I could not control.", "2026-11-10T09:00:00"),
    ("patient28", 2, "I enjoyed a peaceful morning.", "2026-11-08T09:00:00"),
    ("patient28", 3, "I felt tired after a long afternoon.", "2026-11-09T09:00:00"),
    ("patient28", 2, "I felt grateful for a supportive message.", "2026-11-10T09:00:00"),
    ("patient29", 4, "I worried about making a good impression.", "2026-11-08T09:00:00"),
    ("patient29", 3, "I felt more comfortable after talking it through.", "2026-11-09T09:00:00"),
    ("patient29", 2, "I felt optimistic about tomorrow.", "2026-11-10T09:00:00"),
    ("patient30", 5, "I had a lot on my mind today.", "2026-11-08T09:00:00"),
    ("patient30", 4, "I paused to take a few deep breaths.", "2026-11-09T09:00:00"),
    ("patient30", 3, "I felt less overwhelmed by the evening.", "2026-11-10T09:00:00"),
    ("patient31", 3, "I felt settled after my usual routine.", "2026-11-08T09:00:00"),
    ("patient31", 2, "I enjoyed a walk in the afternoon.", "2026-11-09T09:00:00"),
    ("patient31", 3, "I made time for a relaxing evening.", "2026-11-10T09:00:00"),
    ("patient32", 4, "I felt nervous before an appointment.", "2026-11-08T09:00:00"),
    ("patient32", 3, "The appointment went better than expected.", "2026-11-09T09:00:00"),
    ("patient32", 2, "I felt relieved and more positive today.", "2026-11-10T09:00:00"),
    ("patient33", 2, "I woke feeling rested and clear-headed.", "2026-11-08T09:00:00"),
    ("patient33", 3, "I felt low on energy after lunch.", "2026-11-09T09:00:00"),
    ("patient33", 2, "I did something enjoyable this evening.", "2026-11-10T09:00:00"),
    ("patient34", 5, "I felt rushed for most of the day.", "2026-11-08T09:00:00"),
    ("patient34", 4, "I prioritised one task at a time.", "2026-11-09T09:00:00"),
    ("patient34", 3, "I felt calmer after finishing my main task.", "2026-11-10T09:00:00"),
    ("patient35", 3, "I felt connected after speaking with family.", "2026-11-08T09:00:00"),
    ("patient35", 4, "I felt uneasy about a decision.", "2026-11-09T09:00:00"),
    ("patient35", 3, "I gave myself time to consider my options.", "2026-11-10T09:00:00"),
    ("patient36", 2, "I had a calm start to the morning.", "2026-11-08T09:00:00"),
    ("patient36", 3, "A change of plans made me feel unsettled.", "2026-11-09T09:00:00"),
    ("patient36", 2, "I adapted and ended the day feeling okay.", "2026-11-10T09:00:00"),
    ("patient37", 4, "I was tense while preparing for a task.", "2026-11-08T09:00:00"),
    ("patient37", 3, "I took a short break and stretched.", "2026-11-09T09:00:00"),
    ("patient37", 3, "I felt more comfortable by the afternoon.", "2026-11-10T09:00:00"),
    ("patient38", 3, "I had an ordinary but steady day.", "2026-11-08T09:00:00"),
    ("patient38", 2, "I found time to do something creative.", "2026-11-09T09:00:00"),
    ("patient38", 3, "I felt content with how today went.", "2026-11-10T09:00:00"),
    ("patient39", 5, "I felt discouraged by a setback.", "2026-11-08T09:00:00"),
    ("patient39", 4, "I reminded myself that progress takes time.", "2026-11-09T09:00:00"),
    ("patient39", 3, "I noticed one thing that went well today.", "2026-11-10T09:00:00"),
    ("patient40", 2, "I felt rested and ready this morning.", "2026-11-08T09:00:00"),
    ("patient40", 3, "I felt a little overwhelmed by noise.", "2026-11-09T09:00:00"),
    ("patient40", 2, "A quiet break helped me feel better.", "2026-11-10T09:00:00"),
    ("patient41", 4, "I felt uncertain about a conversation.", "2026-11-08T09:00:00"),
    ("patient41", 3, "I communicated more openly than I expected.", "2026-11-09T09:00:00"),
    ("patient41", 2, "I felt proud of speaking up today.", "2026-11-10T09:00:00"),
    ("patient42", 3, "I felt balanced and present today.", "2026-11-08T09:00:00"),
    ("patient42", 4, "I felt frustrated when plans changed.", "2026-11-09T09:00:00"),
    ("patient42", 3, "I found a new plan that worked for me.", "2026-11-10T09:00:00"),
    ("patient43", 2, "I enjoyed a relaxed breakfast.", "2026-11-08T09:00:00"),
    ("patient43", 3, "I felt tired after a full day.", "2026-11-09T09:00:00"),
    ("patient43", 2, "I made sure to get enough rest tonight.", "2026-11-10T09:00:00"),
    ("patient44", 4, "I felt stressed by competing priorities.", "2026-11-08T09:00:00"),
    ("patient44", 3, "I asked for support with one task.", "2026-11-09T09:00:00"),
    ("patient44", 3, "Sharing the load made today easier.", "2026-11-10T09:00:00"),
    ("patient45", 3, "I felt comfortable spending time alone.", "2026-11-08T09:00:00"),
    ("patient45", 2, "I enjoyed a conversation with a neighbour.", "2026-11-09T09:00:00"),
    ("patient45", 3, "I felt good about keeping in touch.", "2026-11-10T09:00:00"),
    ("patient46", 5, "I was worried about an upcoming change.", "2026-11-08T09:00:00"),
    ("patient46", 4, "I wrote down questions to help me prepare.", "2026-11-09T09:00:00"),
    ("patient46", 3, "Having a plan helped me feel steadier.", "2026-11-10T09:00:00"),
    ("patient47", 2, "I felt upbeat after listening to music.", "2026-11-08T09:00:00"),
    ("patient47", 3, "I had a demanding afternoon.", "2026-11-09T09:00:00"),
    ("patient47", 2, "I relaxed with a favourite book tonight.", "2026-11-10T09:00:00"),
    ("patient48", 4, "I found it hard to focus this morning.", "2026-11-08T09:00:00"),
    ("patient48", 3, "I worked in shorter, manageable intervals.", "2026-11-09T09:00:00"),
    ("patient48", 2, "I felt satisfied with my progress today.", "2026-11-10T09:00:00"),
    ("patient49", 3, "I felt relaxed while doing a familiar activity.", "2026-11-08T09:00:00"),
    ("patient49", 4, "I felt anxious about a phone call.", "2026-11-09T09:00:00"),
    ("patient49", 3, "Making the call was a relief.", "2026-11-10T09:00:00"),
    ("patient50", 2, "I slept well and felt refreshed.", "2026-11-08T09:00:00"),
    ("patient50", 3, "I felt irritable when I got hungry.", "2026-11-09T09:00:00"),
    ("patient50", 2, "A meal and some rest helped.", "2026-11-10T09:00:00"),
    ("patient51", 4, "I felt pressure to get everything done.", "2026-11-08T09:00:00"),
    ("patient51", 3, "I chose the most important things first.", "2026-11-09T09:00:00"),
    ("patient51", 2, "I felt relieved after completing my priorities.", "2026-11-10T09:00:00"),
    ("patient52", 3, "I had a calm day at home.", "2026-11-08T09:00:00"),
    ("patient52", 2, "I enjoyed getting some fresh air.", "2026-11-09T09:00:00"),
    ("patient52", 3, "I felt comfortable winding down tonight.", "2026-11-10T09:00:00"),
    ("patient53", 5, "I felt lonely for part of the day.", "2026-11-08T09:00:00"),
    ("patient53", 4, "I sent a message to someone I miss.", "2026-11-09T09:00:00"),
    ("patient53", 3, "We had a nice conversation this evening.", "2026-11-10T09:00:00"),
    ("patient54", 3, "I felt capable of handling today's plans.", "2026-11-08T09:00:00"),
    ("patient54", 4, "A delay made me feel impatient.", "2026-11-09T09:00:00"),
    ("patient54", 3, "I used the extra time to take a break.", "2026-11-10T09:00:00"),
    ("patient55", 2, "I felt optimistic when I woke up.", "2026-11-08T09:00:00"),
    ("patient55", 3, "I felt unsettled by some news.", "2026-11-09T09:00:00"),
    ("patient55", 2, "Talking it over helped me feel grounded.", "2026-11-10T09:00:00"),
    ("patient56", 4, "I felt tired after a restless night.", "2026-11-08T09:00:00"),
    ("patient56", 3, "I paced myself and took a break.", "2026-11-09T09:00:00"),
    ("patient56", 2, "I felt better after an early evening.", "2026-11-10T09:00:00"),
    ("patient57", 3, "I enjoyed a routine that felt familiar.", "2026-11-08T09:00:00"),
    ("patient57", 4, "I felt nervous about trying something new.", "2026-11-09T09:00:00"),
    ("patient57", 3, "I tried it and felt glad I did.", "2026-11-10T09:00:00"),
    ("patient58", 5, "I felt weighed down by a difficult week.", "2026-11-08T09:00:00"),
    ("patient58", 4, "I took time to notice what I needed.", "2026-11-09T09:00:00"),
    ("patient58", 3, "Resting helped me feel more like myself.", "2026-11-10T09:00:00"),
    ("patient59", 2, "I felt calm while preparing breakfast.", "2026-11-08T09:00:00"),
    ("patient59", 3, "I felt distracted by several notifications.", "2026-11-09T09:00:00"),
    ("patient59", 2, "Turning off my phone helped me relax.", "2026-11-10T09:00:00"),
    ("patient60", 4, "I felt uncertain about how someone was feeling.", "2026-11-08T09:00:00"),
    ("patient60", 3, "I asked directly instead of guessing.", "2026-11-09T09:00:00"),
    ("patient60", 2, "I felt reassured after we talked.", "2026-11-10T09:00:00"),
    ("patient61", 3, "I felt steady through a busy morning.", "2026-11-08T09:00:00"),
    ("patient61", 2, "I enjoyed a break with a colleague.", "2026-11-09T09:00:00"),
    ("patient61", 3, "I felt ready for tomorrow.", "2026-11-10T09:00:00"),
    ("patient62", 5, "I felt frustrated with myself today.", "2026-11-08T09:00:00"),
    ("patient62", 4, "I tried to speak to myself more kindly.", "2026-11-09T09:00:00"),
    ("patient62", 3, "I recognised a few things I did well.", "2026-11-10T09:00:00"),
    ("patient63", 2, "I felt peaceful after a slow morning.", "2026-11-08T09:00:00"),
    ("patient63", 3, "I felt tense while waiting for news.", "2026-11-09T09:00:00"),
    ("patient63", 2, "The news was reassuring and I relaxed.", "2026-11-10T09:00:00"),
    ("patient64", 4, "I had difficulty switching between tasks.", "2026-11-08T09:00:00"),
    ("patient64", 3, "I focused on one thing at a time.", "2026-11-09T09:00:00"),
    ("patient64", 3, "I felt more organised by the evening.", "2026-11-10T09:00:00"),
    ("patient65", 3, "I felt grateful for a helpful friend.", "2026-11-08T09:00:00"),
    ("patient65", 2, "I enjoyed a hobby I had missed.", "2026-11-09T09:00:00"),
    ("patient65", 3, "I felt relaxed after making time for myself.", "2026-11-10T09:00:00"),
    ("patient66", 5, "I felt anxious about a busy schedule.", "2026-11-08T09:00:00"),
    ("patient66", 4, "I left some space between my plans.", "2026-11-09T09:00:00"),
    ("patient66", 3, "Having more space made the day easier.", "2026-11-10T09:00:00"),
    ("patient67", 2, "I felt positive after a good night's rest.", "2026-11-08T09:00:00"),
    ("patient67", 3, "I felt a little down in the afternoon.", "2026-11-09T09:00:00"),
    ("patient67", 2, "I made a plan I am looking forward to.", "2026-11-10T09:00:00"),
    ("patient68", 4, "I felt stressed about an unexpected expense.", "2026-11-08T09:00:00"),
    ("patient68", 3, "I looked at my options and made a plan.", "2026-11-09T09:00:00"),
    ("patient68", 3, "I felt more in control today.", "2026-11-10T09:00:00"),
    ("patient69", 3, "I had a quiet day and felt at ease.", "2026-11-08T09:00:00"),
    ("patient69", 2, "I enjoyed a meal with someone close to me.", "2026-11-09T09:00:00"),
    ("patient69", 3, "I felt peaceful as the day ended.", "2026-11-10T09:00:00"),
    ("patient70", 4, "I felt worried about an upcoming conversation.", "2026-11-08T09:00:00"),
    ("patient70", 3, "I thought about what I wanted to say.", "2026-11-09T09:00:00"),
    ("patient70", 2, "The conversation went well and I felt relieved.", "2026-11-10T09:00:00"),
]

SAMPLE_JOURNAL_ENTRIES = [
    ("patient1", "I took a break outside today and noticed that it helped me reset."),
    ("patient2", "Writing down one thing I handled well today made the evening feel easier."),
]

SAMPLE_PATIENT_NOTES = [
    ("patient1", "mhwp1", "Discussed grounding techniques and agreed to review them next session."),
    ("patient2", "mhwp2", "Patient identified taking regular breaks as a helpful coping strategy."),
]

SAMPLE_APPOINTMENTS = [
    ("patient1", "mhwp1", "2026-11-12T10:00:00", "confirmed", "2026-11-10T11:00:00"),
    ("patient1", "mhwp1", "2026-11-13T14:00:00", "requested", "2026-11-10T11:00:00"),
    ("patient2", "mhwp2", "2026-11-13T11:00:00", "confirmed", "2026-11-10T11:00:00"),
]


def upcoming_sample_appointments(now):
    workdays = []
    day = now.date()
    while len(workdays) < 3:
        day += timedelta(days=1)
        if day.weekday() < 5:
            workdays.append(day)

    first, second, third = workdays
    slots = [
        ("patient1", "mhwp1", first, 10, "requested"),
        ("patient2", "mhwp2", first, 11, "confirmed"),
        ("patient1", "mhwp1", second, 14, "confirmed"),
        ("patient2", "mhwp2", second, 9, "requested"),
        ("patient1", "mhwp1", third, 11, "requested"),
        ("patient2", "mhwp2", third, 15, "confirmed"),
    ]
    created_at = now.isoformat(timespec="seconds")
    return [
        (patient, practitioner, datetime.combine(day, time(hour)).isoformat(timespec="seconds"), status, created_at)
        for patient, practitioner, day, hour, status in slots
    ]


def seed_sample_data():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executemany(
            """
            INSERT OR IGNORE INTO users
                (username, password, name, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            SAMPLE_USERS,
        )

        user_ids = {
            username: connection.execute(
                "SELECT user_id FROM users WHERE username = ?", (username,)
            ).fetchone()[0]
            for username, _, _, _, role, _ in SAMPLE_USERS
            if role != "admin"
        }

        connection.executemany(
            """
            INSERT OR IGNORE INTO patient_profiles
                (patient_id, emergency_contact_email, assigned_practitioner_id)
            VALUES (?, ?, ?)
            """,
            [
                (user_ids[patient], emergency_email, user_ids[practitioner])
                for patient, emergency_email, practitioner in SAMPLE_PATIENT_PROFILES
            ],
        )

        connection.executemany(
            "INSERT OR IGNORE INTO conditions (name, description) VALUES (?, ?)",
            SAMPLE_CONDITIONS,
        )
        condition_ids = {
            name: connection.execute(
                "SELECT condition_id FROM conditions WHERE name = ?", (name,)
            ).fetchone()[0]
            for name in ("Anxiety", "Depression", "Stress")
        }
        connection.executemany(
            """
            INSERT OR IGNORE INTO patient_conditions
                (patient_id, condition_id, practitioner_id)
            VALUES (?, ?, ?)
            """,
            [
                (user_ids[patient], condition_ids[condition], user_ids[practitioner])
                for patient, condition, practitioner in SAMPLE_PATIENT_CONDITIONS
            ],
        )

        for username, score, comment, created_at in SAMPLE_MOOD_ENTRIES:
            patient_id = user_ids[username]
            exists = connection.execute(
                """
                SELECT 1 FROM mood_entries
                WHERE patient_id = ? AND comment = ?
                """,
                (patient_id, comment),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO mood_entries (patient_id, score, comment, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (patient_id, score, comment, created_at),
                )

        for username, content in SAMPLE_JOURNAL_ENTRIES:
            patient_id = user_ids[username]
            exists = connection.execute(
                """
                SELECT 1 FROM journal_entries
                WHERE patient_id = ? AND content = ?
                """,
                (patient_id, content),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO journal_entries (patient_id, content, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (patient_id, content, "2026-11-10T10:00:00"),
                )

        for username, practitioner, content in SAMPLE_PATIENT_NOTES:
            patient_id = user_ids[username]
            practitioner_id = user_ids[practitioner]
            exists = connection.execute(
                """
                SELECT 1 FROM patient_notes
                WHERE patient_id = ? AND content = ?
                """,
                (patient_id, content),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO patient_notes
                        (patient_id, practitioner_id, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (patient_id, practitioner_id, content, "2026-11-10T10:30:00"),
                )

        appointments = SAMPLE_APPOINTMENTS + upcoming_sample_appointments(datetime.now())
        for patient, practitioner, scheduled_time, status, created_at in appointments:
            exists = connection.execute(
                """
                SELECT 1 FROM appointments
                WHERE practitioner_id = ? AND datetime(scheduled_time) = datetime(?)
                  AND (patient_id = ? OR status != 'cancelled')
                """,
                (user_ids[practitioner], scheduled_time, user_ids[patient]),
            ).fetchone()
            if not exists:
                connection.execute(
                    """
                    INSERT INTO appointments
                        (patient_id, practitioner_id, scheduled_time, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_ids[patient],
                        user_ids[practitioner],
                        scheduled_time,
                        status,
                        created_at,
                    ),
                )

    print(f"Sample data is ready in {DATABASE_PATH}")
    print("Test logins: admin, mhwp1-mhwp30, patient1-patient70 (all passwords are blank).")


if __name__ == "__main__":
    seed_sample_data()
