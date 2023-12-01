from jornal_parser import JournalParser


def main():
    url = "http://limnolfwbiol.com/"  
    parser = JournalParser(url)

    arr = []

    years = parser.get_available_years()
    for year in years:
        numbers = [num.split('№')[1].strip() for num in parser.get_available_numbers(year)]
        for number in numbers:
            arr.append(parser.get_issue_data(year, '№ ' + number))

    return arr

    # export_target = "elibrary"

    # export = ExportCrossRef(issue) if export_target.lower() == "crossref" else ExportElibrary(issue)

    # path = './out.xlsx'
    # export.export(path)

    # print("Экспорт выполнен успешно")

