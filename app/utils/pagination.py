def pagination(data, total_pages, current_page):
    start_index = (current_page - 1) * total_pages
    end_index = start_index + total_pages
    record = {"data":data[start_index:end_index],"page_no":current_page,"total_data":len(data),"per_page_data":10}
    return record
