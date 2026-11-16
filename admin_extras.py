"""Extra admin reports: features added beyond the brief (A1 to A9 are in admin_cli_prototype.py).

  mood_trend        View reports, option 4: a text bar chart of the clinic's average mood per day.
  week_group_menu   Report A8, after the tables: a 7-day text bar chart for one gender or age group.

The core file calls these two functions. Everything else here is a helper for them.
Shared helpers and settings (NOW, MIN_GROUP, ask, heading and so on) stay in the core file.
"""
from datetime import datetime, timedelta

import admin_cli_prototype as core

TREND_STEP = 0.3       # a week trend smaller than this (in mood points) is "about the same"


def mood_trend(conn, days=30):
    """Text bar chart of the average mood per day over the last `days` days."""
    start = (core.NOW - timedelta(days=days - 1)).strftime("%Y-%m-%d")
    df = core.frame(conn, "SELECT date(created_at) AS day, score FROM mood_entries WHERE date(created_at) >= ?",
               (start,))
    core.heading(f"MOOD TREND: LAST {days} DAYS")
    if df.empty:
        print("  No mood entries in this period.")
        return
    daily = df.groupby("day")["score"].agg(["mean", "count"])
    print("  Average mood per day across all patients. 1 = best, 6 = worst,")
    print("  so a longer bar means a worse day.\n")
    print(f"  {'Day':<11}{'':<26}{'Average':>7}{'Entries':>9}")
    for day, r in daily.iterrows():
        bar = "█" * round(r["mean"] * 4)               # 4 characters per point, at most 24
        print(f"  {core.show_date(day):<11}{bar:<26}{r['mean']:>7.2f}{int(r['count']):>9}")
    if len(daily) >= 14:                                # compare whole weeks, so one odd day does not decide it
        first, last = daily["mean"].iloc[:7].mean(), daily["mean"].iloc[-7:].mean()
        change = "worse" if last - first >= TREND_STEP else "better" if last - first <= -TREND_STEP else "about the same"
        print(f"\n  First week average {first:.2f}, last week average {last:.2f}: mood is {change}.")


def text_bar(value, per_point=6):
    """A bar of value * per_point characters, drawn to 1/8 of a character so small changes show."""
    eighths = round(value * per_point * 8)
    return "█" * (eighths // 8) + ("", "▏", "▎", "▍", "▌", "▋", "▊", "▉")[eighths % 8]


def week_group_days(conn, per):
    """Last 7 days for each gender and age band group, using the same patients as the tables above.
    Returns (days, groups). Each group is a dict: col, key, patients, daily {day: average or None}.
    A day is None when fewer than MIN_GROUP patients in the group logged a mood that day."""
    days = [(core.NOW - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(6, -1, -1)]
    df = core.frame(conn, """SELECT patient_id AS pid, date(created_at) AS day, score FROM mood_entries
                        WHERE date(created_at) >= ? AND created_at <= ?""", [days[0], core.ts(core.NOW)])
    df = df[df["pid"].isin(per.index)].join(per[["gender", "band"]], on="pid")
    groups = []
    for col in ("gender", "band"):
        for key, members in per.groupby(col):
            g = df[df[col] == key]
            avg, n = g.groupby("day")["score"].mean(), g.groupby("day")["pid"].nunique()
            daily = {d: (avg[d] if n.get(d, 0) >= core.MIN_GROUP else None) for d in days}
            groups.append({"col": col, "key": key, "patients": len(members), "daily": daily})
    return days, groups


def week_trend(daily):
    """(first 3 days average, last 3 days average, word), or None if there are too few days shown.
    3 days against 3 days, so one odd day does not decide it."""
    shown = [v for v in daily.values() if v is not None]
    if len(shown) < 6:
        return None
    first, last = sum(shown[:3]) / 3, sum(shown[-3:]) / 3
    word = "worse" if last - first >= TREND_STEP else "better" if last - first <= -TREND_STEP else "about the same"
    return first, last, word


def week_group_menu(conn, per):
    """First choose gender or age band, then a group, then see its day by day bar chart."""
    days, groups = week_group_days(conn, per)
    while True:
        core.heading("MOOD BY GROUP: LAST 7 DAYS")
        print("   1  By gender\n   2  By age band\n   0  Back")
        c = core.ask_number("Choose 1, 2 or 0: ", 0, 2)
        if c == 0:
            return
        col = "gender" if c == 1 else "band"
        week_group_list(days, [g for g in groups if g["col"] == col],
                        "BY GENDER" if col == "gender" else "BY AGE BAND")


def week_group_list(days, groups, title):
    """One line per group in this category, then the chart for the group chosen."""
    visible = [g for g in groups if g["patients"] >= core.MIN_GROUP]
    hidden = [g["key"] for g in groups if g["patients"] < core.MIN_GROUP]
    while True:
        core.heading(f"MOOD {title}: LAST 7 DAYS")
        print("  First 3 days against last 3 days. 1 is best, 6 is worst.\n")
        if not visible:
            print(f"  Every group has fewer than {core.MIN_GROUP} patients, so all are hidden.")
            return
        print(f"{'No':>3}  {'Group':<20}{'Patients':>8}{'First 3':>9}{'Last 3':>8}  Trend")
        for i, g in enumerate(visible, 1):
            t = week_trend(g["daily"])
            cells = f"{t[0]:>9.2f}{t[1]:>8.2f}  {t[2]}" if t else f"{'not enough days':>25}"
            print(f"{i:>3}  {g['key']:<20}{g['patients']:>8}{cells}")
        if hidden:
            print(f"\n  Hidden (fewer than {core.MIN_GROUP} patients): {', '.join(hidden)}")
        core.set_menu([g["key"] for g in visible])
        n = core.ask_number("Choose a group to see day by day, or 0 to go back: ", 0, len(visible))
        if n == 0:
            return
        week_group_detail(days, visible[n - 1])


def week_group_detail(days, g):
    core.heading(f"{g['key'].upper()}: LAST 7 DAYS ({g['patients']} patients)")
    print("  Average mood per day. 1 is best, 6 is worst, so a longer bar is a worse day.")
    print(f"  A day with fewer than {core.MIN_GROUP} patients in the group is hidden.")
    prev = None
    for day in days:
        label = datetime.strptime(day, "%Y-%m-%d").strftime("%a %d/%m")
        avg = g["daily"][day]
        if avg is None:
            print(f"\n    {label}  (hidden or no entries)")
            prev = None
            continue
        change = ""
        if prev is not None:
            diff = avg - prev
            change = ("▲ worse" if diff >= 0.05 else "▼ better" if diff <= -0.05 else "  same") + f" {diff:+.2f}"
        print(f"\n    {label}  {text_bar(avg):<37} {avg:.2f}  {change}")
        prev = avg
    shown = {day: v for day, v in g["daily"].items() if v is not None}
    if len(shown) >= 2:                                 # lowest score is the best day
        best, worst = min(shown, key=shown.get), max(shown, key=shown.get)
        name = lambda day: datetime.strptime(day, "%Y-%m-%d").strftime("%a")
        print(f"\n    Best day {shown[best]:.2f} ({name(best)}), worst day {shown[worst]:.2f} ({name(worst)}).")
    core.ask("\nPress Enter to go back to the list: ")      # pause, so the chart is not pushed off the screen
