'''
Haven't included the emotion tags in searching.
Haven't considered about the result order.
'''

def search_resources(connection,keyword):
    searchword = "%" + keyword.replace("!", "!!").replace("%", "!%").replace("_", "!_") + "%"
    results = connection.execute("""
        SELECT resources.name, url
        FROM resources
        WHERE resources.name LIKE ? ESCAPE '!'
        ORDER BY resources.name ASC; 
    """,(searchword,)).fetchall()
    return results

def show_pages(output):
    page = 0
    total_pages = (len(output)+2) // 3
    while True:
        for number, i in enumerate(output[page * 3:page * 3 + 3], start=page * 3 + 1):
            print(number, end = " ")
            print(i[0],end = " ")
            print(i[1])
        if total_pages == 1:
            choice = input('Type "b" to go back to the menu.\n').strip().casefold()
            if choice == "b":
                break
            else:
                print('Invalid input. Please enter "b".')   
        else:
            print(f"Page {page + 1} of {total_pages}")
            choice = input('Type "n" to the next page, "p" to the previous page and "b" to go back to the menu.\n').strip().casefold()
            if choice == "n":
                if page == total_pages - 1:
                    print("This is the last page.")
                else:
                    page += 1
                    continue
            elif choice == "p":
                if page == 0:
                    print("This is the first page.")
                else:
                    page -= 1
                    continue
            elif choice == "b":
                break
            else:
                print("Please enter n, p or b.")

def patient_resources(connection):
    print('Type "b" to return to the menu.')
    while True:        
        keyword = input("What is your concern at the moment: ").strip().casefold()
        if keyword == "b":
            break
        elif len(keyword) < 2:
            print("Invalid input. Please enter at least 2 characters.")
            continue
        output = search_resources(connection,keyword)
        if output == []:
            print("No results found. Please put in a new keyword.")
            continue
        results = len(output)
        if results == 1:
            print("1 result found.")
        else:
            print(str(results) + " results found.")
        show_pages(output)
        break