def detectar_anomalias(consumos):
    """
    Detecta consumos anómalos con una regla simple:
    Si el consumo es 2.1 veces mayor que el promedio → alerta.
    """
    if not consumos or len(consumos) < 3:
        return None

    promedio = sum(consumos) / len(consumos)
    ultimo = consumos[-1]

    if ultimo > promedio * 2.1:
        return {
            "tipo": "Consumo excesivo",
            "valor": ultimo,
            "promedio": promedio
        }
    return None
