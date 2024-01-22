import re

re_filters = re.compile(r'(\+|-)([^\+-]*)')

def build_sql_filter(data: str) -> str:
    # Translate an http query to a SQL query
    
    exts = grps = ''
    
    for action, filter_ in re_filters.findall(data):
        
        type_ = action == '+'
        if (isext := filter_[0] != '$') and type_:
            exts += f'OR ext="{filter_}" '
        
        elif isext and not type_:
            exts += f'AND ext!="{filter_}" '
        
        else:
            grps += f'AND groups {("NOT ", "")[type_]}LIKE \'%"{filter_[1:]}"%\' '
    
    return f'''
            SELECT * FROM main WHERE
            ({exts.strip('OR').strip('AND') or 1})
            AND ({grps.strip('AND') or 1})
            ''';

# EOF