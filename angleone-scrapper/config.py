def number_of_pages():
    return 10

BATCH_SIZE = 10

def get_last_page():

    try:
        with open("last_page.txt", "r") as f:
            return int(f.read().strip())

    except FileNotFoundError:
        return 0


def update_last_page(page_no):

    with open("last_page.txt", "w") as f:
        f.write(str(page_no))


# last_page = get_last_page()

# start_page = last_page + 1

# end_page = last_page + BATCH_SIZE

# print(
#     f"Processing pages "
#     f"{start_page} to {end_page}"
# )

# for page_no in range(start_page, end_page + 1):

#     print(f"Processing Page {page_no}")

#     rows_found = scrape_page(page_no)

#     # stop if page doesn't exist
#     if rows_found == 0:

#         print(
#             f"No data found on page "
#             f"{page_no}"
#         )

#         update_last_page(page_no - 1)

#         break

# else:
#     # all pages processed successfully
#     update_last_page(end_page)

# print("Completed")