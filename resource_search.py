#Haven't considered about the result order. Now it's only order by initials.
#Now it's one keyword search. If you use more than one word, it could not get any result.

def get_emotions(connection):
    emotions = connection.execute("""
        SELECT emotion_id, name
        FROM emotions
        ORDER BY emotion_id ASC
""").fetchall()
    return emotions

def search_by_emotion(connection, emotion_id):
    result = connection.execute("""
        SELECT resources.name, resources.url
        FROM resources JOIN resource_emotions ON resources.resource_id = resource_emotions.resource_id
        WHERE resource_emotions.emotion_id = ?
        ORDER BY resources.name ASC   
""", (emotion_id,)).fetchall()
    return result

def search_resources(connection,keyword):
    searchword = "%" + keyword.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    results = connection.execute("""
        SELECT DISTINCT resources.name, resources.url
        FROM resources
        LEFT JOIN resource_emotions ON resources.resource_id = resource_emotions.resource_id
        LEFT JOIN emotions ON resource_emotions.emotion_id = emotions.emotion_id
        WHERE resources.name LIKE ? ESCAPE '!'
        OR emotions.name LIKE ? ESCAPE '!'
        OR emotions.description LIKE ? ESCAPE '!'
        ORDER BY resources.name ASC
""",(searchword,searchword,searchword)).fetchall()
    return results

def show_result(output):
    results = len(output)
    if results == 1:
        print("\n1 result found.")
    else:
        print("\n" + str(results) + " results found.")

def show_pages(output):
    page = 0
    total_pages = (len(output)+2) // 3
    while True:
        print()
        for number, i in enumerate(output[page * 3:page * 3 + 3], start=page * 3 + 1):
            print(number, end = " ")
            print(i[0],end = " ")
            print(i[1])
        if total_pages == 1:
            choice = input('\nType "b" to go back to the previous menu.\n').strip().casefold()
            if choice == "b":
                break
            else:
                print('\nInvalid input. Please enter "b".')
        else:
            print(f"\nPage {page + 1} of {total_pages}")
            choice = input('Type "n" to the next page, "p" to the previous page and "b" to go back to the previous menu.\n').strip().casefold()
            if choice == "n":
                if page == total_pages - 1:
                    print("\nThis is the last page.")
                else:
                    page += 1
                    continue
            elif choice == "p":
                if page == 0:
                    print("\nThis is the first page.")
                else:
                    page -= 1
                    continue
            elif choice == "b":
                break
            else:
                print("\nPlease enter n, p or b.")

def patient_resources(connection):
    table = get_emotions(connection)
    keyword_option = len(table) + 1
    while True:
        print()
        for number, i in enumerate(table, start=1):
            print(number, i[1])
        print(keyword_option, "Search by keyword")
        keyword = input(f'\nType a number 1-{len(table)} to see resources for that feeling.\nType {keyword_option} to search by keyword.\nType "b" to return to the patient menu.\n').strip().casefold()
        if keyword == "b":
            break
        elif keyword.isdigit() and 1 <= int(keyword) <= len(table):
            emotion_id = table[int(keyword) - 1][0]
            output = search_by_emotion(connection, emotion_id)
            if output == []:
                print("\nThere are no resources for this feeling yet. Please choose another option.")
                continue
            show_result(output)
            show_pages(output)
        elif keyword.isdigit() and int(keyword) == keyword_option:
            while True:        
                keyword = input("\nWhat is your concern at the moment in a word: ").strip().casefold()
                if keyword.isdigit():
                    print("\nInvalid input. Please input a word.")
                    continue
                elif len(keyword) <= 2:
                    print("\nInvalid input. Please enter at least 3 characters.")
                    continue
                output = search_resources(connection,keyword)
                if output == []:
                    print("\nNo results found. Please put in a new keyword.")
                    continue
                show_result(output)
                show_pages(output)
                break
        else:
            print("\nInvalid input. Please try again.")
            continue