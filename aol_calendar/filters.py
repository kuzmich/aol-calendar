import re


# "Свами Каушик (Каши)"
fname_lname_nickname_re = re.compile(r'(\w+) (\w+) \((\w+)\)')


def teacher_names(teachers):
    names = []
    for t in teachers:
        try:
            last_name, first_name = t.split()
            names.append(f'{last_name} {first_name[0]}.')
        except Exception as e:
            if (match := fname_lname_nickname_re.search(t)):
                names.append(match.group(3))
            else:
                raise
    return ' + '.join(names)
