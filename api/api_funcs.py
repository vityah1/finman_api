def conv_refuel_data_to_desc(req: dict) -> dict:
    result = req.copy()
    if req.get('km') and req.get('litres'):
        result['mydesc'] = '{}км;{}л'.format(req.get('km'), req.get('litres'))
        if req.get('price_val'):
            result['mydesc'] += ';{}eur'.format(req.get('price_val'))
        if req.get('name') or req.get('station'):
            result['mydesc'] += ';{}'.format(
                req.get('name') if req.get('name') else req.get('station')
                )
    return result