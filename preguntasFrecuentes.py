import difflib

faq = {
    "¿Qué es la bolsa térmica digital Ziloy?": 
        "Ziloy es una bolsa térmica portátil e inteligente diseñada para mantener bebidas calientes o frías por más tiempo. "
        "Mide la temperatura real del líquido en su interior y la muestra en pantalla digital, combinando tecnología, sostenibilidad y diseño ergonómico.",

    "¿De qué materiales está hecha la bolsa Ziloy?": 
        "Está fabricada con materiales aislantes ecológicos y una capa térmica de alta eficiencia que reduce la pérdida de calor. "
        "Su exterior es de neopreno reforzado y tela reciclada, resistente al agua y fácil de limpiar.",

    "¿Qué tipo de bebidas puedo guardar?": 
        "Puedes usarla para café, té, sopas, infusiones, chocolate caliente o bebidas frías. "
        "Solo asegúrate de cerrar bien el recipiente interno y evitar líquidos gaseosos o con alcohol.",

    "¿Cuánto tiempo mantiene caliente la bebida?": 
        "Según las pruebas, Ziloy conserva la temperatura de bebidas calientes por 30 a 50 minutos, "
        "dependiendo del volumen, la temperatura ambiente y el tipo de líquido.",

    "¿A qué temperatura se considera que una bebida ya está fría?": 
        "Para café o té, una bebida se considera fría cuando baja de 50 °C. "
        "El rango ideal de consumo está entre 60 °C y 70 °C, que Ziloy ayuda a conservar durante el mayor tiempo posible.",

    "¿Ziloy también funciona con bebidas frías?": 
        "Sí. Ziloy conserva bebidas frías por más de 1 hora, dependiendo del clima y del volumen del líquido. "
        "Solo evita exponerla al sol directo o ambientes de alta temperatura.",

    "¿La bolsa puede calentar o enfriar automáticamente?": 
        "No. Ziloy no calienta ni enfría por sí misma; su función es mantener la temperatura actual "
        "y medirla digitalmente para que el usuario conozca cuánto tiempo permanecerá caliente o fría.",

    "¿Cómo muestra la temperatura?": 
        "La bolsa incluye un sensor térmico digital que detecta la temperatura del contenido "
        "y la muestra en una pequeña pantalla LED externa.",

    "¿Se puede lavar la bolsa?": 
        "Sí. Se puede limpiar con un paño húmedo o lavar a mano con agua fría. "
        "No se recomienda sumergirla completamente ni usar lavadora, ya que puede dañar los componentes electrónicos.",

    "¿Cuánto dura la batería del sensor?": 
        "La pantalla digital funciona con una batería recargable que puede durar de 5 a 7 días según el uso. "
        "Se carga mediante puerto USB tipo C.",

    "¿Es resistente al agua?": 
        "Es resistente a salpicaduras y humedad, pero no sumergible. "
        "Los materiales protegen el sensor, pero se recomienda mantener la parte del display seca.",

    # ====== COMPRAS Y GARANTÍA ======

    "¿Dónde puedo comprar una bolsa Ziloy?": 
        "Puedes adquirirla directamente en nuestro marketplace oficial Ziloy.com, "
        "donde encontrarás todas las versiones, colores y accesorios.",

    "¿Qué métodos de pago aceptan?": 
        "Aceptamos tarjeta de crédito, débito, PayPal y MercadoPago. "
        "También puedes realizar transferencias seguras desde la app de tu banco.",

    "¿Tienen envíos a todo el país?": 
        "Sí. Realizamos envíos a todo el territorio nacional mediante servicios logísticos aliados. "
        "El tiempo promedio de entrega es de 2 a 5 días hábiles.",

    "¿Tienen garantía?": 
        "Sí. Ziloy tiene una garantía de 6 meses que cubre defectos de fabricación y fallas del sensor. "
        "No cubre daños por mal uso o exposición al agua.",

    "¿Ofrecen devoluciones o cambios?": 
        "Sí, dentro de los primeros 15 días después de la compra, siempre que el producto esté en perfecto estado "
        "y con su empaque original.",

    "¿Tienen versiones diferentes de la bolsa?": 
        "Actualmente contamos con tres versiones:\n"
        "- Ziloy Basic: modelo estándar.\n"
        "- Ziloy Premium: con materiales de mayor aislamiento y pantalla digital ampliada.\n"
        "- Ziloy Travel: versión compacta para transporte fácil.",

    "¿Qué incluye la compra?": 
        "Cada bolsa Ziloy incluye:\n- Bolsa térmica digital.\n- Cable de carga USB.\n"
        "- Manual de usuario digital.\n- Acceso al predictor térmico en línea.",

    "¿Cómo contacto con atención al cliente?": 
        "Puedes escribirnos directamente al WhatsApp oficial de Ziloy o al correo soporte@ziloy.com. "
        "Nuestro horario de atención es de lunes a sábado, de 8:00 a.m. a 6:00 p.m."
}


def obtener_respuesta(pregunta_usuario):
    """Busca la pregunta más parecida y devuelve su respuesta."""
    pregunta_usuario = pregunta_usuario.lower().strip()
    preguntas = list(faq.keys())

    # Buscar coincidencia aproximada
    coincidencia = difflib.get_close_matches(pregunta_usuario, preguntas, n=1, cutoff=0.4)

    if coincidencia:
        return faq[coincidencia[0]]
    else:
        return ("No tengo una respuesta exacta para eso. "
                "Puedes preguntar cosas como '¿Qué es la bolsa Ziloy?' o '¿Tienen garantía?'.")
