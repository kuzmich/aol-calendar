def teacher_names(teachers):
    names = []
    for t in teachers:
        last_name, first_name = t.split()
        names.append(f'{last_name} {first_name[0]}.')
    return ' + '.join(names)
