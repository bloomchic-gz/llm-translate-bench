"""
多语言术语表模块 - 基于数据库分析生成

数据来源: app_backend.product_search (28,640条产品标题)
生成日期: 2024-12

支持多个领域的术语表，可通过选项选择：
- fashion_core: 服装核心版 (50条高频术语，约+1500 tokens)
- fashion_full: 服装完整版 (120+条术语，约+3500 tokens)
- ecommerce: 电商通用术语
"""

from typing import Optional

# ============================================================
# 服装术语表 - 核心版 (50条高频术语)
# 基于数据库分析，选取出现频率 >= 500 的术语
# ============================================================
FASHION_CORE = {
    # === 领型 (Necklines) - 高频 ===
    "V Neck": {"de": "V-Ausschnitt", "fr": "Col en V", "es": "Cuello en V", "it": "Scollo a V", "pt": "Decote em V", "nl": "V-hals", "pl": "Dekolt w serek"},
    "Round Neck": {"de": "Rundhals", "fr": "Col rond", "es": "Cuello redondo", "it": "Girocollo", "pt": "Gola redonda", "nl": "Ronde hals", "pl": "Okrągły dekolt"},
    "Crew Neck": {"de": "Rundhals", "fr": "Col ras du cou", "es": "Cuello redondo", "it": "Girocollo", "pt": "Gola careca", "nl": "Ronde hals", "pl": "Okrągły dekolt"},
    "Square Neck": {"de": "Karree-Ausschnitt", "fr": "Encolure carrée", "es": "Escote cuadrado", "it": "Scollo quadrato", "pt": "Decote quadrado", "nl": "Vierkante hals", "pl": "Kwadratowy dekolt"},
    "Notched": {"de": "Reverskragen", "fr": "Col cranté", "es": "Cuello con muesca", "it": "Collo a tacca", "pt": "Gola entalhada", "nl": "Inkepingskraag", "pl": "Kołnierz z wcięciem"},

    # === 袖型 (Sleeves) - 高频 ===
    "Lantern Sleeve": {"de": "Laternenärmel", "fr": "Manche lanterne", "es": "Manga farol", "it": "Manica a lanterna", "pt": "Manga lanterna", "nl": "Lantaarnmouw", "pl": "Rękawy lampiony"},
    "Raglan Sleeve": {"de": "Raglanärmel", "fr": "Manche raglan", "es": "Manga raglán", "it": "Manica raglan", "pt": "Manga raglan", "nl": "Raglanmouw", "pl": "Rękawy raglanowe"},
    "Ruffle Sleeve": {"de": "Rüschenärmel", "fr": "Manche à volants", "es": "Manga con volantes", "it": "Manica con volant", "pt": "Manga com babados", "nl": "Rufflesmouw", "pl": "Rękawy z falbanami"},

    # === 图案 (Patterns) - 高频 ===
    "Floral": {"de": "Blumen", "fr": "Floral", "es": "Floral", "it": "Floreale", "pt": "Floral", "nl": "Bloemen", "pl": "Kwiatowy"},
    "Solid": {"de": "Einfarbig", "fr": "Uni", "es": "Liso", "it": "Tinta unita", "pt": "Liso", "nl": "Effen", "pl": "Jednolity"},
    "Contrast": {"de": "Kontrast", "fr": "Contraste", "es": "Contraste", "it": "Contrasto", "pt": "Contraste", "nl": "Contrast", "pl": "Kontrast"},
    "Striped": {"de": "Gestreift", "fr": "Rayé", "es": "Rayas", "it": "Righe", "pt": "Listrado", "nl": "Gestreept", "pl": "W paski"},
    "Plaid": {"de": "Karo", "fr": "Carreaux", "es": "Cuadros", "it": "Quadri", "pt": "Xadrez", "nl": "Geruit", "pl": "Krata"},
    "Embroidered": {"de": "Bestickt", "fr": "Brodé", "es": "Bordado", "it": "Ricamato", "pt": "Bordado", "nl": "Geborduurd", "pl": "Haftowany"},
    "Geometric": {"de": "Geometrisch", "fr": "Géométrique", "es": "Geométrico", "it": "Geometrico", "pt": "Geométrico", "nl": "Geometrisch", "pl": "Geometryczny"},
    "Colorblock": {"de": "Colorblocking", "fr": "Color block", "es": "Bloques de color", "it": "Color block", "pt": "Color block", "nl": "Colorblock", "pl": "Bloki kolorów"},
    "Polka Dot": {"de": "Tupfen", "fr": "Pois", "es": "Lunares", "it": "Pois", "pt": "Poá", "nl": "Stippen", "pl": "Groszki"},
    "Leopard": {"de": "Leopard", "fr": "Léopard", "es": "Leopardo", "it": "Leopardo", "pt": "Leopardo", "nl": "Luipaard", "pl": "Panterka"},

    # === 工艺细节 (Details) - 高频 ===
    "Pocket": {"de": "Tasche", "fr": "Poche", "es": "Bolsillo", "it": "Tasca", "pt": "Bolso", "nl": "Zak", "pl": "Kieszeń"},
    "Button": {"de": "Knopf", "fr": "Bouton", "es": "Botón", "it": "Bottone", "pt": "Botão", "nl": "Knoop", "pl": "Guzik"},
    "Ruffle": {"de": "Rüsche", "fr": "Volant", "es": "Volante", "it": "Volant", "pt": "Babado", "nl": "Ruches", "pl": "Falbana"},
    "Patchwork": {"de": "Patchwork", "fr": "Patchwork", "es": "Patchwork", "it": "Patchwork", "pt": "Patchwork", "nl": "Patchwork", "pl": "Patchwork"},
    "Belt": {"de": "Gürtel", "fr": "Ceinture", "es": "Cinturón", "it": "Cintura", "pt": "Cinto", "nl": "Riem", "pl": "Pasek"},
    "Lace": {"de": "Spitze", "fr": "Dentelle", "es": "Encaje", "it": "Pizzo", "pt": "Renda", "nl": "Kant", "pl": "Koronka"},
    "Drawstring": {"de": "Kordelzug", "fr": "Cordon de serrage", "es": "Cordón", "it": "Coulisse", "pt": "Cordão", "nl": "Trekkoord", "pl": "Sznurek"},
    "Pleated": {"de": "Plissiert", "fr": "Plissé", "es": "Plisado", "it": "Plissettato", "pt": "Plissado", "nl": "Geplisseerd", "pl": "Plisowany"},
    "Zipper": {"de": "Reißverschluss", "fr": "Fermeture éclair", "es": "Cremallera", "it": "Cerniera", "pt": "Zíper", "nl": "Rits", "pl": "Zamek"},
    "Cutout": {"de": "Ausschnitt", "fr": "Découpe", "es": "Recorte", "it": "Cut-out", "pt": "Recorte", "nl": "Uitsnijding", "pl": "Wycięcie"},
    "Tiered": {"de": "Gestuft", "fr": "À étages", "es": "Escalonado", "it": "A strati", "pt": "Em camadas", "nl": "Gelaagd", "pl": "Warstwowy"},

    # === 版型 (Silhouettes) - 高频 ===
    "Elastic Waist": {"de": "Elastische Taille", "fr": "Taille élastique", "es": "Cintura elástica", "it": "Vita elastica", "pt": "Cintura elástica", "nl": "Elastische taille", "pl": "Elastyczna talia"},
    "Wrap": {"de": "Wickel", "fr": "Portefeuille", "es": "Cruzado", "it": "A portafoglio", "pt": "Transpassado", "nl": "Wikkel", "pl": "Kopertowy"},
    "Asymmetrical": {"de": "Asymmetrisch", "fr": "Asymétrique", "es": "Asimétrico", "it": "Asimmetrico", "pt": "Assimétrico", "nl": "Asymmetrisch", "pl": "Asymetryczny"},

    # === 长度 (Length) - 高频 ===
    "Midi": {"de": "Midi", "fr": "Midi", "es": "Midi", "it": "Midi", "pt": "Midi", "nl": "Midi", "pl": "Midi"},
    "Maxi": {"de": "Maxi", "fr": "Maxi", "es": "Maxi", "it": "Maxi", "pt": "Maxi", "nl": "Maxi", "pl": "Maxi"},
    "Split Hem": {"de": "Schlitzsaum", "fr": "Ourlet fendu", "es": "Dobladillo con abertura", "it": "Orlo con spacco", "pt": "Barra com fenda", "nl": "Gespleten zoom", "pl": "Rozcięty dół"},

    # === 面料 (Fabrics) - 高频 ===
    "Knit": {"de": "Strick", "fr": "Tricot", "es": "Punto", "it": "Maglia", "pt": "Tricô", "nl": "Gebreid", "pl": "Dzianina"},
    "Mesh": {"de": "Netz", "fr": "Maille", "es": "Malla", "it": "Rete", "pt": "Malha", "nl": "Mesh", "pl": "Siatka"},
    "Ribbed": {"de": "Gerippt", "fr": "Côtelé", "es": "Acanalado", "it": "A coste", "pt": "Canelado", "nl": "Geribbeld", "pl": "Prążkowany"},

    # === 服装类型 (Garment Types) - 高频 ===
    "Dress": {"de": "Kleid", "fr": "Robe", "es": "Vestido", "it": "Abito", "pt": "Vestido", "nl": "Jurk", "pl": "Sukienka"},
    "Blouse": {"de": "Bluse", "fr": "Blouse", "es": "Blusa", "it": "Blusa", "pt": "Blusa", "nl": "Blouse", "pl": "Bluzka"},
    "T-shirt": {"de": "T-Shirt", "fr": "T-shirt", "es": "Camiseta", "it": "Maglietta", "pt": "Camiseta", "nl": "T-shirt", "pl": "Koszulka"},
    "Cardigan": {"de": "Strickjacke", "fr": "Cardigan", "es": "Cárdigan", "it": "Cardigan", "pt": "Cardigã", "nl": "Vest", "pl": "Kardigan"},
    "Pants": {"de": "Hose", "fr": "Pantalon", "es": "Pantalón", "it": "Pantaloni", "pt": "Calça", "nl": "Broek", "pl": "Spodnie"},
    "Jumpsuit": {"de": "Jumpsuit", "fr": "Combinaison", "es": "Mono", "it": "Tuta", "pt": "Macacão", "nl": "Jumpsuit", "pl": "Kombinezon"},
    "Jeans": {"de": "Jeans", "fr": "Jean", "es": "Vaqueros", "it": "Jeans", "pt": "Jeans", "nl": "Jeans", "pl": "Dżinsy"},
    "Skirt": {"de": "Rock", "fr": "Jupe", "es": "Falda", "it": "Gonna", "pt": "Saia", "nl": "Rok", "pl": "Spódnica"},

    # === 风格 (Styles) - 高频 ===
    "Boho": {"de": "Boho", "fr": "Bohème", "es": "Boho", "it": "Boho", "pt": "Boho", "nl": "Boho", "pl": "Boho"},
}

# ============================================================
# 服装术语表 - 完整版 (120+条)
# 基于数据库分析，选取出现频率 >= 30 的术语
# ============================================================
FASHION_FULL = {
    **FASHION_CORE,  # 包含核心版所有术语

    # === 更多领型 (Necklines) ===
    "Lapel": {"de": "Revers", "fr": "Revers", "es": "Solapa", "it": "Risvolto", "pt": "Lapela", "nl": "Revers", "pl": "Klapa"},
    "Keyhole": {"de": "Schlüsselloch", "fr": "Trou de serrure", "es": "Ojo de cerradura", "it": "Keyhole", "pt": "Gota", "nl": "Sleutelgat", "pl": "Łezka"},
    "Halter": {"de": "Neckholder", "fr": "Col licou", "es": "Cuello halter", "it": "Collo all'americana", "pt": "Frente única", "nl": "Halternek", "pl": "Wiązany na szyi"},
    "Mock Neck": {"de": "Stehkragen", "fr": "Col montant", "es": "Cuello alto", "it": "Collo alto", "pt": "Gola alta", "nl": "Opstaande kraag", "pl": "Stójka"},
    "Turtleneck": {"de": "Rollkragen", "fr": "Col roulé", "es": "Cuello alto", "it": "Collo alto", "pt": "Gola rolê", "nl": "Col", "pl": "Golf"},
    "Off Shoulder": {"de": "Schulterfrei", "fr": "Épaules dénudées", "es": "Hombros descubiertos", "it": "Spalle scoperte", "pt": "Ombro a ombro", "nl": "Off-shoulder", "pl": "Opadające ramiona"},
    "Cowl Neck": {"de": "Wasserfallausschnitt", "fr": "Col bénitier", "es": "Cuello drapeado", "it": "Collo a cascata", "pt": "Gola boba", "nl": "Cowlhals", "pl": "Dekolt woda"},
    "Boat Neck": {"de": "U-Boot-Ausschnitt", "fr": "Encolure bateau", "es": "Escote barco", "it": "Scollo a barca", "pt": "Decote canoa", "nl": "Boothalslijn", "pl": "Dekolt łódka"},
    "One Shoulder": {"de": "Ein-Schulter", "fr": "Asymétrique", "es": "Un hombro", "it": "Monospalla", "pt": "Um ombro", "nl": "Eén schouder", "pl": "Jedno ramię"},
    "Sweetheart": {"de": "Herzausschnitt", "fr": "Décolleté cœur", "es": "Escote corazón", "it": "Scollo a cuore", "pt": "Decote coração", "nl": "Hartvormige hals", "pl": "Dekolt serce"},
    "Scoop Neck": {"de": "Rundhalsausschnitt", "fr": "Encolure ronde", "es": "Escote redondo", "it": "Scollo tondo", "pt": "Decote redondo", "nl": "Ronde hals", "pl": "Dekolt łódka"},
    "Stand Collar": {"de": "Stehkragen", "fr": "Col droit", "es": "Cuello mao", "it": "Colletto alla coreana", "pt": "Gola padre", "nl": "Staande kraag", "pl": "Stójka"},

    # === 更多袖型 (Sleeves) ===
    "Dolman Sleeve": {"de": "Dolmanärmel", "fr": "Manche dolman", "es": "Manga dolmán", "it": "Manica a dolman", "pt": "Manga dolmã", "nl": "Dolmanmouw", "pl": "Rękawy dolman"},
    "Flutter Sleeve": {"de": "Flatterärmel", "fr": "Manche papillon", "es": "Manga mariposa", "it": "Manica a farfalla", "pt": "Manga borboleta", "nl": "Fladdermouw", "pl": "Rękawy motylek"},
    "Batwing Sleeve": {"de": "Fledermausärmel", "fr": "Manche chauve-souris", "es": "Manga murciélago", "it": "Manica a pipistrello", "pt": "Manga morcego", "nl": "Vleermuismouw", "pl": "Rękawy nietoperz"},
    "Bell Sleeve": {"de": "Trompetenärmel", "fr": "Manche évasée", "es": "Manga campana", "it": "Manica a campana", "pt": "Manga sino", "nl": "Klokmouw", "pl": "Rękawy dzwony"},
    "Cap Sleeve": {"de": "Kappenärmel", "fr": "Manche courte", "es": "Manga casquillo", "it": "Manica a aletta", "pt": "Manga curta", "nl": "Kapmouw", "pl": "Krótkie rękawy"},
    "Sleeveless": {"de": "Ärmellos", "fr": "Sans manches", "es": "Sin mangas", "it": "Senza maniche", "pt": "Sem mangas", "nl": "Mouwloos", "pl": "Bez rękawów"},
    "Puff Sleeve": {"de": "Puffärmel", "fr": "Manche bouffante", "es": "Manga abullonada", "it": "Manica a sbuffo", "pt": "Manga bufante", "nl": "Pofmouw", "pl": "Bufiaste rękawy"},
    "Cold Shoulder": {"de": "Cold Shoulder", "fr": "Épaules dénudées", "es": "Hombros descubiertos", "it": "Spalle scoperte", "pt": "Ombros de fora", "nl": "Cold shoulder", "pl": "Odkryte ramiona"},
    "Long Sleeve": {"de": "Langarm", "fr": "Manches longues", "es": "Manga larga", "it": "Manica lunga", "pt": "Manga longa", "nl": "Lange mouw", "pl": "Długi rękaw"},
    "Short Sleeve": {"de": "Kurzarm", "fr": "Manches courtes", "es": "Manga corta", "it": "Manica corta", "pt": "Manga curta", "nl": "Korte mouw", "pl": "Krótki rękaw"},
    "Half Sleeve": {"de": "Halbarm", "fr": "Demi-manches", "es": "Media manga", "it": "Mezza manica", "pt": "Meia manga", "nl": "Halve mouw", "pl": "Rękaw do łokcia"},

    # === 更多图案 (Patterns) ===
    "Tie Dye": {"de": "Batik", "fr": "Tie and dye", "es": "Tie dye", "it": "Tie dye", "pt": "Tie dye", "nl": "Tie-dye", "pl": "Tie dye"},
    "Paisley": {"de": "Paisley", "fr": "Cachemire", "es": "Cachemir", "it": "Paisley", "pt": "Paisley", "nl": "Paisley", "pl": "Paisley"},
    "Houndstooth": {"de": "Hahnentritt", "fr": "Pied-de-poule", "es": "Pata de gallo", "it": "Pied de poule", "pt": "Pied de poule", "nl": "Pied-de-poule", "pl": "Pepitka"},
    "Abstract": {"de": "Abstrakt", "fr": "Abstrait", "es": "Abstracto", "it": "Astratto", "pt": "Abstrato", "nl": "Abstract", "pl": "Abstrakcyjny"},
    "Camo": {"de": "Tarnmuster", "fr": "Camouflage", "es": "Camuflaje", "it": "Mimetico", "pt": "Camuflado", "nl": "Camouflage", "pl": "Kamuflaż"},

    # === 更多工艺细节 (Details) ===
    "Tassel": {"de": "Quaste", "fr": "Pompon", "es": "Borla", "it": "Nappa", "pt": "Borla", "nl": "Kwast", "pl": "Frędzel"},
    "Bow": {"de": "Schleife", "fr": "Nœud", "es": "Lazo", "it": "Fiocco", "pt": "Laço", "nl": "Strik", "pl": "Kokarda"},
    "Slit": {"de": "Schlitz", "fr": "Fente", "es": "Abertura", "it": "Spacco", "pt": "Fenda", "nl": "Split", "pl": "Rozcięcie"},
    "Hollow Out": {"de": "Durchbrochen", "fr": "Ajouré", "es": "Calado", "it": "Traforato", "pt": "Vazado", "nl": "Opengewerkt", "pl": "Ażurowy"},
    "Fringe": {"de": "Fransen", "fr": "Franges", "es": "Flecos", "it": "Frange", "pt": "Franjas", "nl": "Franje", "pl": "Frędzle"},

    # === 更多版型 (Silhouettes) ===
    "Flare": {"de": "Ausgestellt", "fr": "Évasé", "es": "Acampanado", "it": "Svasato", "pt": "Evasê", "nl": "Uitlopend", "pl": "Rozkloszowany"},
    "Skinny": {"de": "Skinny", "fr": "Skinny", "es": "Pitillo", "it": "Skinny", "pt": "Skinny", "nl": "Skinny", "pl": "Skinny"},
    "Straight": {"de": "Gerade", "fr": "Droit", "es": "Recto", "it": "Dritto", "pt": "Reto", "nl": "Recht", "pl": "Prosty"},
    "Wide Leg": {"de": "Weites Bein", "fr": "Jambe large", "es": "Pierna ancha", "it": "Gamba larga", "pt": "Perna larga", "nl": "Wijde pijp", "pl": "Szerokie nogawki"},
    "A-Line": {"de": "A-Linie", "fr": "Ligne A", "es": "Línea A", "it": "Linea A", "pt": "Linha A", "nl": "A-lijn", "pl": "Linia A"},
    "Fitted": {"de": "Tailliert", "fr": "Ajusté", "es": "Entallado", "it": "Aderente", "pt": "Ajustado", "nl": "Aansluitend", "pl": "Dopasowany"},
    "Relaxed": {"de": "Entspannt", "fr": "Décontracté", "es": "Relajado", "it": "Rilassato", "pt": "Relaxado", "nl": "Relaxed", "pl": "Luźny"},
    "Slim": {"de": "Schlank", "fr": "Slim", "es": "Slim", "it": "Slim", "pt": "Slim", "nl": "Slim", "pl": "Slim"},
    "Loose": {"de": "Locker", "fr": "Ample", "es": "Holgado", "it": "Largo", "pt": "Folgado", "nl": "Los", "pl": "Luźny"},
    "Bodycon": {"de": "Figurbetonend", "fr": "Moulant", "es": "Ceñido", "it": "Aderente", "pt": "Justo", "nl": "Aansluitend", "pl": "Obcisły"},
    "High Waist": {"de": "Hohe Taille", "fr": "Taille haute", "es": "Cintura alta", "it": "Vita alta", "pt": "Cintura alta", "nl": "Hoge taille", "pl": "Wysoka talia"},

    # === 更多下摆/长度 (Hem/Length) ===
    "Ruffle Hem": {"de": "Rüschensaum", "fr": "Ourlet à volants", "es": "Dobladillo con volantes", "it": "Orlo con volant", "pt": "Barra com babados", "nl": "Ruche zoom", "pl": "Dół z falbanami"},
    "Scallop": {"de": "Muschelkante", "fr": "Festonné", "es": "Festoneado", "it": "Smerlato", "pt": "Recortado", "nl": "Schulprand", "pl": "Falisty brzeg"},
    "High Low": {"de": "Vokuhila", "fr": "Asymétrique", "es": "Asimétrico", "it": "Asimmetrico", "pt": "Mullet", "nl": "High-low", "pl": "Asymetryczny"},
    "Cropped": {"de": "Kurz geschnitten", "fr": "Court", "es": "Corto", "it": "Corto", "pt": "Cropped", "nl": "Kort", "pl": "Krótki"},
    "Mini": {"de": "Mini", "fr": "Mini", "es": "Mini", "it": "Mini", "pt": "Mini", "nl": "Mini", "pl": "Mini"},

    # === 更多面料 (Fabrics) ===
    "Cotton": {"de": "Baumwolle", "fr": "Coton", "es": "Algodón", "it": "Cotone", "pt": "Algodão", "nl": "Katoen", "pl": "Bawełna"},
    "Velvet": {"de": "Samt", "fr": "Velours", "es": "Terciopelo", "it": "Velluto", "pt": "Veludo", "nl": "Fluweel", "pl": "Aksamit"},
    "Sequin": {"de": "Pailletten", "fr": "Paillettes", "es": "Lentejuelas", "it": "Paillettes", "pt": "Lantejoulas", "nl": "Pailletten", "pl": "Cekiny"},
    "Chiffon": {"de": "Chiffon", "fr": "Mousseline", "es": "Gasa", "it": "Chiffon", "pt": "Chiffon", "nl": "Chiffon", "pl": "Szyfon"},
    "Denim": {"de": "Denim", "fr": "Denim", "es": "Vaquero", "it": "Denim", "pt": "Jeans", "nl": "Denim", "pl": "Dżins"},
    "Tweed": {"de": "Tweed", "fr": "Tweed", "es": "Tweed", "it": "Tweed", "pt": "Tweed", "nl": "Tweed", "pl": "Tweed"},
    "Corduroy": {"de": "Cord", "fr": "Velours côtelé", "es": "Pana", "it": "Velluto a coste", "pt": "Veludo cotelê", "nl": "Ribfluweel", "pl": "Sztruks"},
    "Faux Leather": {"de": "Kunstleder", "fr": "Simili cuir", "es": "Cuero sintético", "it": "Ecopelle", "pt": "Couro sintético", "nl": "Kunstleer", "pl": "Eko-skóra"},
    "Satin": {"de": "Satin", "fr": "Satin", "es": "Satén", "it": "Raso", "pt": "Cetim", "nl": "Satijn", "pl": "Satyna"},
    "Linen": {"de": "Leinen", "fr": "Lin", "es": "Lino", "it": "Lino", "pt": "Linho", "nl": "Linnen", "pl": "Len"},

    # === 更多服装类型 (Garment Types) ===
    "Jacket": {"de": "Jacke", "fr": "Veste", "es": "Chaqueta", "it": "Giacca", "pt": "Jaqueta", "nl": "Jasje", "pl": "Kurtka"},
    "Coat": {"de": "Mantel", "fr": "Manteau", "es": "Abrigo", "it": "Cappotto", "pt": "Casaco", "nl": "Jas", "pl": "Płaszcz"},
    "Shorts": {"de": "Shorts", "fr": "Short", "es": "Pantalón corto", "it": "Pantaloncini", "pt": "Shorts", "nl": "Korte broek", "pl": "Szorty"},
    "Leggings": {"de": "Leggings", "fr": "Leggings", "es": "Leggings", "it": "Leggings", "pt": "Leggings", "nl": "Legging", "pl": "Legginsy"},
    "Romper": {"de": "Spielanzug", "fr": "Combishort", "es": "Mono corto", "it": "Pagliaccetto", "pt": "Macaquinho", "nl": "Playsuit", "pl": "Rampers"},
    "Vest": {"de": "Weste", "fr": "Gilet", "es": "Chaleco", "it": "Gilet", "pt": "Colete", "nl": "Vest", "pl": "Kamizelka"},
    "Sweater": {"de": "Pullover", "fr": "Pull", "es": "Jersey", "it": "Maglione", "pt": "Suéter", "nl": "Trui", "pl": "Sweter"},
    "Bodysuit": {"de": "Body", "fr": "Body", "es": "Body", "it": "Body", "pt": "Body", "nl": "Body", "pl": "Body"},
    "Top": {"de": "Top", "fr": "Haut", "es": "Top", "it": "Top", "pt": "Top", "nl": "Top", "pl": "Top"},
    "Shirt": {"de": "Hemd", "fr": "Chemise", "es": "Camisa", "it": "Camicia", "pt": "Camisa", "nl": "Overhemd", "pl": "Koszula"},

    # === 更多风格 (Styles) ===
    "Vintage": {"de": "Vintage", "fr": "Vintage", "es": "Vintage", "it": "Vintage", "pt": "Vintage", "nl": "Vintage", "pl": "Vintage"},
    "Holiday": {"de": "Urlaub", "fr": "Vacances", "es": "Vacaciones", "it": "Vacanza", "pt": "Férias", "nl": "Vakantie", "pl": "Wakacyjny"},
    "Vacation": {"de": "Urlaub", "fr": "Vacances", "es": "Vacaciones", "it": "Vacanza", "pt": "Férias", "nl": "Vakantie", "pl": "Wakacyjny"},
}

# ============================================================
# 电商通用术语表
# ============================================================
ECOMMERCE_GENERAL = {
    "Free Shipping": {"de": "Kostenloser Versand", "fr": "Livraison gratuite", "es": "Envío gratis", "it": "Spedizione gratuita", "pt": "Frete grátis", "nl": "Gratis verzending", "pl": "Darmowa dostawa"},
    "In Stock": {"de": "Auf Lager", "fr": "En stock", "es": "En stock", "it": "Disponibile", "pt": "Em estoque", "nl": "Op voorraad", "pl": "Dostępny"},
    "Out of Stock": {"de": "Nicht auf Lager", "fr": "Rupture de stock", "es": "Agotado", "it": "Esaurito", "pt": "Esgotado", "nl": "Niet op voorraad", "pl": "Niedostępny"},
    "Best Seller": {"de": "Bestseller", "fr": "Meilleures ventes", "es": "Más vendido", "it": "Più venduto", "pt": "Mais vendido", "nl": "Bestseller", "pl": "Bestseller"},
    "New Arrival": {"de": "Neuheit", "fr": "Nouveauté", "es": "Novedad", "it": "Novità", "pt": "Novidade", "nl": "Nieuw binnen", "pl": "Nowość"},
    "Limited Edition": {"de": "Limitierte Auflage", "fr": "Édition limitée", "es": "Edición limitada", "it": "Edizione limitata", "pt": "Edição limitada", "nl": "Beperkte oplage", "pl": "Limitowana edycja"},
    "Sale": {"de": "Sale", "fr": "Soldes", "es": "Rebajas", "it": "Saldi", "pt": "Promoção", "nl": "Uitverkoop", "pl": "Wyprzedaż"},
    "Clearance": {"de": "Ausverkauf", "fr": "Déstockage", "es": "Liquidación", "it": "Svendita", "pt": "Liquidação", "nl": "Opruiming", "pl": "Wyprzedaż"},
}

# ============================================================
# 术语表注册表
# ============================================================
GLOSSARY_REGISTRY = {
    "fashion_core": {
        "name": "Fashion (Core)",
        "description": "服装核心版术语表，50条高频术语（频率≥500）",
        "terms": FASHION_CORE,
        "token_estimate": 1500,
    },
    "fashion_full": {
        "name": "Fashion (Full)",
        "description": "服装完整版术语表，120+条术语（频率≥30）",
        "terms": FASHION_FULL,
        "token_estimate": 3500,
    },
    "ecommerce": {
        "name": "E-commerce General",
        "description": "电商通用术语表",
        "terms": ECOMMERCE_GENERAL,
        "token_estimate": 300,
    },
}

# 兼容旧版本名称
GLOSSARY_REGISTRY["fashion_mini"] = GLOSSARY_REGISTRY["fashion_core"]


def list_glossaries() -> dict:
    """列出所有可用的术语表"""
    return {
        key: {
            "name": info["name"],
            "description": info["description"],
            "term_count": len(info["terms"]),
            "token_estimate": info["token_estimate"],
        }
        for key, info in GLOSSARY_REGISTRY.items()
        if key != "fashion_mini"  # 隐藏别名
    }


def get_glossary(glossary_id: str) -> Optional[dict]:
    """获取指定术语表"""
    if glossary_id in GLOSSARY_REGISTRY:
        return GLOSSARY_REGISTRY[glossary_id]["terms"]
    return None


def build_glossary_prompt(target_langs: list[str], glossary_id: str = "fashion_core") -> str:
    """
    构建术语表提示词片段

    Args:
        target_langs: 目标语言代码列表
        glossary_id: 术语表ID (fashion_core, fashion_full, ecommerce)

    Returns:
        格式化的术语表字符串
    """
    glossary = get_glossary(glossary_id)
    if not glossary:
        return ""

    # 构建表头
    header = "| English | " + " | ".join([lang.upper() for lang in target_langs]) + " |"
    separator = "|" + "|".join(["---"] * (len(target_langs) + 1)) + "|"

    rows = []
    for term, translations in glossary.items():
        row_values = [term]
        for lang in target_langs:
            row_values.append(translations.get(lang, term))
        rows.append("| " + " | ".join(row_values) + " |")

    table = "\n".join([header, separator] + rows)

    glossary_info = GLOSSARY_REGISTRY.get(glossary_id, {})
    glossary_name = glossary_info.get("name", glossary_id)

    return f"""## {glossary_name} Terminology Reference
{table}
"""


def get_glossary_terms(glossary_id: str = "fashion_core") -> list[str]:
    """获取术语表中所有术语"""
    glossary = get_glossary(glossary_id)
    if glossary:
        return list(glossary.keys())
    return []


# 数据库分析统计 (28,640条产品标题)
DATABASE_STATS = {
    "garment_types": {
        "Dress": 9076, "Blouse": 3113, "T-shirt": 2279, "Top": 1671,
        "Shirt": 1474, "Cardigan": 1352, "Pants": 1097, "Jumpsuit": 798,
        "Jeans": 612, "Skirt": 542, "Jacket": 482, "Coat": 468,
        "Shorts": 377, "Leggings": 261, "Romper": 143, "Vest": 104,
        "Sweater": 84, "Bodysuit": 42,
    },
    "necklines": {
        "V Neck": 1798, "Round Neck": 1189, "Notched": 740, "Crew Neck": 694,
        "Square Neck": 565, "Lapel": 352, "Keyhole": 319, "Halter": 151,
        "Mock Neck": 149, "Turtleneck": 119, "Off Shoulder": 117, "Cowl Neck": 87,
        "Boat Neck": 64, "One Shoulder": 58, "Sweetheart": 51, "Scoop Neck": 49,
        "Stand Collar": 32,
    },
    "sleeves": {
        "Lantern Sleeve": 1141, "Raglan Sleeve": 595, "Ruffle Sleeve": 474,
        "Dolman Sleeve": 354, "Flutter Sleeve": 319, "Sleeveless": 279,
        "Batwing Sleeve": 262, "Bell Sleeve": 260, "Cap Sleeve": 258,
        "Puff Sleeve": 185, "Cold Shoulder": 142, "Long Sleeve": 64,
        "Short Sleeve": 35, "Half Sleeve": 31,
    },
    "patterns": {
        "Print": 5871, "Floral": 4678, "Solid": 2942, "Contrast": 2833,
        "Striped": 1846, "Plaid": 959, "Embroidered": 917, "Geometric": 837,
        "Colorblock": 751, "Polka Dot": 651, "Leopard": 610, "Tie Dye": 286,
        "Paisley": 161, "Houndstooth": 76, "Abstract": 72, "Camo": 43,
    },
    "details": {
        "Pocket": 5400, "Button": 2971, "Ruffle": 2783, "Patchwork": 2532,
        "Belt": 2087, "Lace": 2047, "Drawstring": 1181, "Pleated": 1037,
        "Zipper": 782, "Cutout": 725, "Tiered": 544, "Tassel": 334,
        "Bow": 310, "Slit": 230, "Hollow": 128, "Fringe": 60,
    },
    "silhouettes": {
        "Elastic Waist": 1463, "Wrap": 818, "Asymmetric": 535, "Flare": 345,
        "Skinny": 333, "Straight": 313, "Wide Leg": 172, "A-Line": 130,
        "Fitted": 124, "Relaxed": 101, "Slim": 98, "Loose": 87,
        "Bodycon": 51, "High Waist": 33,
    },
    "lengths": {
        "Midi": 2830, "Maxi": 556, "Split Hem": 431, "Ruffle Hem": 313,
        "Scallop": 139, "Cropped": 126, "High Low": 122, "Mini": 83,
    },
    "fabrics": {
        "Knit": 1831, "Mesh": 1035, "Ribbed": 578, "Cotton": 401,
        "Velvet": 336, "Sequin": 300, "Chiffon": 268, "Denim": 243,
        "Tweed": 107, "Corduroy": 109, "Faux Leather": 53, "Satin": 32,
        "Linen": 30,
    },
    "styles": {
        "Boho": 781, "Vintage": 145, "Holiday": 112, "Vacation": 50,
    },
}
