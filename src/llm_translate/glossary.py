"""
多语言术语表模块 - 基于完整数据库词频分析生成

数据来源: app_backend.product_search (28,255条产品标题)
分析方法: 词频统计 + 自然语言处理
生成日期: 2024-12

支持多个领域的术语表，可通过选项选择：
- fashion_hard: 难翻译术语表 (13条，约+400 tokens) - 基于数据科学筛选
- fashion_core: 服装核心版 (80条高频术语，约+2200 tokens)
- fashion_full: 服装完整版 (180+条术语，约+5000 tokens)
- fashion_v4: 完整运营术语表 (210条，支持智能匹配)
- ecommerce: 电商通用术语
"""

import json
import re
from pathlib import Path
from typing import Optional, List, Set, Dict

# ============================================================
# 服装术语表 - 难翻译精简版 (13条)
# 基于 53 个高频术语的翻译测试，科学筛选出模型真正翻译错误的术语
# 测试方法：词频分析 → 全量翻译测试 → 人工标注 → 筛选
# 推荐场景：需要低成本+高准确率时使用
# ============================================================
FASHION_HARD = {
    # === 翻译错误类 (模型翻译成错误的词) ===
    # Button Up: 模型翻译为 Hemdbluse(衬衫) 而非 Durchgeknöpft(扣紧式)
    "Button Up": {"de": "Durchgeknöpft", "fr": "Boutonné", "es": "Abotonado", "it": "Abbottonato", "pt": "Abotoado", "nl": "Doorknoopbaar", "pl": "Zapinany na guziki"},
    # Gathered: 模型翻译为 Gesammelte(收集) 而非 Gerafft(褶皱)
    "Gathered": {"de": "Gerafft", "fr": "Froncé", "es": "Fruncido", "it": "Arricciato", "pt": "Franzido", "nl": "Gerimpeld", "pl": "Marszczony"},
    # Ruched: 模型翻译为 Rüschen(荷叶边) 而非 Gerafft(褶皱)
    "Ruched": {"de": "Gerafft", "fr": "Froncé", "es": "Drapeado", "it": "Drappeggiato", "pt": "Drapeado", "nl": "Gerimpeld", "pl": "Drapowany"},
    # Overlap Collar: 模型翻译为 Wickelkragen(裹身领) 而非 Überlappkragen(重叠领)
    "Overlap Collar": {"de": "Überlappkragen", "fr": "Col croisé", "es": "Cuello solapado", "it": "Collo sovrapposto", "pt": "Gola sobreposta", "nl": "Overslagkraag", "pl": "Kołnierz zakładany"},
    # High Rise: 模型翻译为 High-Waist 而非德语 Hohe Taille
    "High Rise": {"de": "Hohe Taille", "fr": "Taille haute", "es": "Tiro alto", "it": "Vita alta", "pt": "Cintura alta", "nl": "Hoge taille", "pl": "Wysoka talia"},
    # Cap Sleeve: 模型翻译为 Flügelärmel(飞袖) 而非 Kappenärmel(帽袖)
    "Cap Sleeve": {"de": "Kappenärmel", "fr": "Manche courte", "es": "Manga casquillo", "it": "Manica a aletta", "pt": "Manga curta", "nl": "Kapmouw", "pl": "Krótkie rękawy"},

    # === 保留英文类 (模型不翻译，直接保留英文) ===
    # Pointelle Knit: 模型保留 Pointelle 不翻译
    "Pointelle Knit": {"de": "Lochmuster", "fr": "Maille ajourée", "es": "Punto calado", "it": "Maglia traforata", "pt": "Tricô rendado", "nl": "Ajourbreisel", "pl": "Ażurowy splot"},
    # Heather: 模型保留 Heather 不翻译
    "Heather": {"de": "Meliert", "fr": "Chiné", "es": "Jaspeado", "it": "Mélange", "pt": "Mesclado", "nl": "Gemêleerd", "pl": "Melanż"},
    # Boho Print: 模型保留 Boho-Print 不翻译
    "Boho Print": {"de": "Boho-Druck", "fr": "Imprimé bohème", "es": "Estampado boho", "it": "Stampa boho", "pt": "Estampa boho", "nl": "Boho print", "pl": "Wzór boho"},
    # Tie Dye: 模型保留 Tie-Dye 不翻译
    "Tie Dye": {"de": "Batik", "fr": "Tie and dye", "es": "Tie dye", "it": "Tie dye", "pt": "Tie dye", "nl": "Tie-dye", "pl": "Tie dye"},
    # Plaid: 模型保留 Plaid 不翻译
    "Plaid": {"de": "Karo", "fr": "Carreaux", "es": "Cuadros", "it": "Quadri", "pt": "Xadrez", "nl": "Geruit", "pl": "Krata"},
    # Colorblock: 模型保留 Colorblock 不翻译
    "Colorblock": {"de": "Colorblocking", "fr": "Color block", "es": "Bloques de color", "it": "Color block", "pt": "Color block", "nl": "Colorblock", "pl": "Bloki kolorów"},
    # Dolman Sleeve: 模型保留 Dolman 不翻译
    "Dolman Sleeve": {"de": "Dolmanärmel", "fr": "Manche dolman", "es": "Manga dolmán", "it": "Manica a dolman", "pt": "Manga dolmã", "nl": "Dolmanmouw", "pl": "Rękawy dolman"},
}

# ============================================================
# 服装术语表 - 核心版 (80条高频术语)
# 基于数据库词频分析，选取出现频率 >= 500 的术语
# ============================================================
FASHION_CORE = {
    # === 服装类型 (Garment Types) - 高频 ===
    "Dress": {"de": "Kleid", "fr": "Robe", "es": "Vestido", "it": "Abito", "pt": "Vestido", "nl": "Jurk", "pl": "Sukienka"},
    "Blouse": {"de": "Bluse", "fr": "Blouse", "es": "Blusa", "it": "Blusa", "pt": "Blusa", "nl": "Blouse", "pl": "Bluzka"},
    "T-shirt": {"de": "T-Shirt", "fr": "T-shirt", "es": "Camiseta", "it": "Maglietta", "pt": "Camiseta", "nl": "T-shirt", "pl": "Koszulka"},
    "Top": {"de": "Top", "fr": "Haut", "es": "Top", "it": "Top", "pt": "Top", "nl": "Top", "pl": "Top"},
    "Sweatshirt": {"de": "Sweatshirt", "fr": "Sweat-shirt", "es": "Sudadera", "it": "Felpa", "pt": "Moletom", "nl": "Sweater", "pl": "Bluza"},
    "Pullover": {"de": "Pullover", "fr": "Pull", "es": "Jersey", "it": "Maglione", "pt": "Pulôver", "nl": "Trui", "pl": "Sweter"},
    "Cardigan": {"de": "Strickjacke", "fr": "Cardigan", "es": "Cárdigan", "it": "Cardigan", "pt": "Cardigã", "nl": "Vest", "pl": "Kardigan"},
    "Pants": {"de": "Hose", "fr": "Pantalon", "es": "Pantalón", "it": "Pantaloni", "pt": "Calça", "nl": "Broek", "pl": "Spodnie"},
    "Jumpsuit": {"de": "Jumpsuit", "fr": "Combinaison", "es": "Mono", "it": "Tuta", "pt": "Macacão", "nl": "Jumpsuit", "pl": "Kombinezon"},
    "Jeans": {"de": "Jeans", "fr": "Jean", "es": "Vaqueros", "it": "Jeans", "pt": "Jeans", "nl": "Jeans", "pl": "Dżinsy"},
    "Skirt": {"de": "Rock", "fr": "Jupe", "es": "Falda", "it": "Gonna", "pt": "Saia", "nl": "Rok", "pl": "Spódnica"},
    "Tank Top": {"de": "Tank Top", "fr": "Débardeur", "es": "Camiseta de tirantes", "it": "Canotta", "pt": "Regata", "nl": "Tanktop", "pl": "Top na ramiączkach"},
    "Cami": {"de": "Trägertop", "fr": "Caraco", "es": "Camisola", "it": "Canotta", "pt": "Camisete", "nl": "Hemdje", "pl": "Koszulka na ramiączkach"},
    "Midi Dress": {"de": "Midikleid", "fr": "Robe midi", "es": "Vestido midi", "it": "Abito midi", "pt": "Vestido midi", "nl": "Midi-jurk", "pl": "Sukienka midi"},
    "Maxi Dress": {"de": "Maxikleid", "fr": "Robe longue", "es": "Vestido largo", "it": "Abito lungo", "pt": "Vestido longo", "nl": "Maxi-jurk", "pl": "Sukienka maxi"},
    "Swim Dress": {"de": "Badekleid", "fr": "Robe de bain", "es": "Vestido de baño", "it": "Abito da bagno", "pt": "Vestido de banho", "nl": "Zwemjurk", "pl": "Sukienka kąpielowa"},

    # === 领型 (Necklines) - 高频 ===
    "V Neck": {"de": "V-Ausschnitt", "fr": "Col en V", "es": "Cuello en V", "it": "Scollo a V", "pt": "Decote em V", "nl": "V-hals", "pl": "Dekolt w serek"},
    "Round Neck": {"de": "Rundhals", "fr": "Col rond", "es": "Cuello redondo", "it": "Girocollo", "pt": "Gola redonda", "nl": "Ronde hals", "pl": "Okrągły dekolt"},
    "Crew Neck": {"de": "Rundhals", "fr": "Col ras du cou", "es": "Cuello redondo", "it": "Girocollo", "pt": "Gola careca", "nl": "Ronde hals", "pl": "Okrągły dekolt"},
    "Square Neck": {"de": "Karree-Ausschnitt", "fr": "Encolure carrée", "es": "Escote cuadrado", "it": "Scollo quadrato", "pt": "Decote quadrado", "nl": "Vierkante hals", "pl": "Kwadratowy dekolt"},
    "Notched Collar": {"de": "Reverskragen", "fr": "Col cranté", "es": "Cuello con muesca", "it": "Collo a tacca", "pt": "Gola entalhada", "nl": "Inkepingskraag", "pl": "Kołnierz z wcięciem"},
    "Lapel Collar": {"de": "Reverskragen", "fr": "Col à revers", "es": "Cuello de solapa", "it": "Collo a risvolto", "pt": "Gola de lapela", "nl": "Reverslijn", "pl": "Kołnierz klapowy"},
    "Shirt Collar": {"de": "Hemdkragen", "fr": "Col chemise", "es": "Cuello de camisa", "it": "Colletto", "pt": "Gola de camisa", "nl": "Overhemdkraag", "pl": "Kołnierzyk"},
    "Overlap Collar": {"de": "Überlappkragen", "fr": "Col croisé", "es": "Cuello solapado", "it": "Collo sovrapposto", "pt": "Gola sobreposta", "nl": "Overslagkraag", "pl": "Kołnierz zakładany"},
    "Surplice Neck": {"de": "Wickelausschnitt", "fr": "Cache-cœur", "es": "Escote cruzado", "it": "Scollo incrociato", "pt": "Decote transpassado", "nl": "Overslaghals", "pl": "Dekolt kopertowy"},
    "Hooded": {"de": "Mit Kapuze", "fr": "À capuche", "es": "Con capucha", "it": "Con cappuccio", "pt": "Com capuz", "nl": "Met capuchon", "pl": "Z kapturem"},

    # === 袖型 (Sleeves) - 高频 ===
    "Lantern Sleeve": {"de": "Laternenärmel", "fr": "Manche lanterne", "es": "Manga farol", "it": "Manica a lanterna", "pt": "Manga lanterna", "nl": "Lantaarnmouw", "pl": "Rękawy lampiony"},
    "Raglan Sleeve": {"de": "Raglanärmel", "fr": "Manche raglan", "es": "Manga raglán", "it": "Manica raglan", "pt": "Manga raglan", "nl": "Raglanmouw", "pl": "Rękawy raglanowe"},
    "Ruffle Sleeve": {"de": "Rüschenärmel", "fr": "Manche à volants", "es": "Manga con volantes", "it": "Manica con volant", "pt": "Manga com babados", "nl": "Rufflesmouw", "pl": "Rękawy z falbanami"},
    "Flutter Sleeve": {"de": "Flatterärmel", "fr": "Manche papillon", "es": "Manga mariposa", "it": "Manica a farfalla", "pt": "Manga borboleta", "nl": "Fladdermouw", "pl": "Rękawy motylek"},
    "Drop Shoulder": {"de": "Überschnittene Schulter", "fr": "Épaule tombante", "es": "Hombro caído", "it": "Spalla scesa", "pt": "Ombro caído", "nl": "Lage schouder", "pl": "Opuszczone ramiona"},
    "Dolman Sleeve": {"de": "Dolmanärmel", "fr": "Manche dolman", "es": "Manga dolmán", "it": "Manica a dolman", "pt": "Manga dolmã", "nl": "Dolmanmouw", "pl": "Rękawy dolman"},

    # === 图案 (Patterns) - 高频 ===
    "Floral": {"de": "Blumen", "fr": "Floral", "es": "Floral", "it": "Floreale", "pt": "Floral", "nl": "Bloemen", "pl": "Kwiatowy"},
    "Floral Print": {"de": "Blumendruck", "fr": "Imprimé floral", "es": "Estampado floral", "it": "Stampa floreale", "pt": "Estampa floral", "nl": "Bloemenprint", "pl": "Kwiatowy wzór"},
    "Ditsy Floral": {"de": "Millefleurs", "fr": "Petites fleurs", "es": "Florecitas", "it": "Fiorellini", "pt": "Floral miúdo", "nl": "Klein bloemmotief", "pl": "Drobne kwiatki"},
    "Solid": {"de": "Einfarbig", "fr": "Uni", "es": "Liso", "it": "Tinta unita", "pt": "Liso", "nl": "Effen", "pl": "Jednolity"},
    "Plain": {"de": "Schlicht", "fr": "Uni", "es": "Liso", "it": "Semplice", "pt": "Liso", "nl": "Effen", "pl": "Gładki"},
    "Contrast": {"de": "Kontrast", "fr": "Contraste", "es": "Contraste", "it": "Contrasto", "pt": "Contraste", "nl": "Contrast", "pl": "Kontrast"},
    "Striped": {"de": "Gestreift", "fr": "Rayé", "es": "Rayas", "it": "Righe", "pt": "Listrado", "nl": "Gestreept", "pl": "W paski"},
    "Plaid": {"de": "Karo", "fr": "Carreaux", "es": "Cuadros", "it": "Quadri", "pt": "Xadrez", "nl": "Geruit", "pl": "Krata"},
    "Geometric": {"de": "Geometrisch", "fr": "Géométrique", "es": "Geométrico", "it": "Geometrico", "pt": "Geométrico", "nl": "Geometrisch", "pl": "Geometryczny"},
    "Boho Print": {"de": "Boho-Druck", "fr": "Imprimé bohème", "es": "Estampado boho", "it": "Stampa boho", "pt": "Estampa boho", "nl": "Boho print", "pl": "Wzór boho"},
    "Colorblock": {"de": "Colorblocking", "fr": "Color block", "es": "Bloques de color", "it": "Color block", "pt": "Color block", "nl": "Colorblock", "pl": "Bloki kolorów"},
    "Polka Dot": {"de": "Tupfen", "fr": "Pois", "es": "Lunares", "it": "Pois", "pt": "Poá", "nl": "Stippen", "pl": "Groszki"},
    "Leopard": {"de": "Leopard", "fr": "Léopard", "es": "Leopardo", "it": "Leopardo", "pt": "Leopardo", "nl": "Luipaard", "pl": "Panterka"},
    "Leopard Print": {"de": "Leopardenmuster", "fr": "Imprimé léopard", "es": "Estampado de leopardo", "it": "Stampa leopardata", "pt": "Estampa de leopardo", "nl": "Luipaardprint", "pl": "Wzór w panterkę"},
    "Bandana Print": {"de": "Bandana-Druck", "fr": "Imprimé bandana", "es": "Estampado de pañuelo", "it": "Stampa bandana", "pt": "Estampa bandana", "nl": "Bandana print", "pl": "Wzór bandana"},
    "Heather": {"de": "Meliert", "fr": "Chiné", "es": "Jaspeado", "it": "Mélange", "pt": "Mesclado", "nl": "Gemêleerd", "pl": "Melanż"},

    # === 工艺细节 (Details) - 高频 ===
    "Pocket": {"de": "Tasche", "fr": "Poche", "es": "Bolsillo", "it": "Tasca", "pt": "Bolso", "nl": "Zak", "pl": "Kieszeń"},
    "Button": {"de": "Knopf", "fr": "Bouton", "es": "Botón", "it": "Bottone", "pt": "Botão", "nl": "Knoop", "pl": "Guzik"},
    "Button Detail": {"de": "Knopfdetail", "fr": "Détail bouton", "es": "Detalle de botón", "it": "Dettaglio bottone", "pt": "Detalhe de botão", "nl": "Knoopdetail", "pl": "Detal z guzikiem"},
    "Button Up": {"de": "Durchgeknöpft", "fr": "Boutonné", "es": "Abotonado", "it": "Abbottonato", "pt": "Abotoado", "nl": "Doorknoopbaar", "pl": "Zapinany na guziki"},
    "Ruffle": {"de": "Rüsche", "fr": "Volant", "es": "Volante", "it": "Volant", "pt": "Babado", "nl": "Ruches", "pl": "Falbana"},
    "Patchwork": {"de": "Patchwork", "fr": "Patchwork", "es": "Patchwork", "it": "Patchwork", "pt": "Patchwork", "nl": "Patchwork", "pl": "Patchwork"},
    "Lace": {"de": "Spitze", "fr": "Dentelle", "es": "Encaje", "it": "Pizzo", "pt": "Renda", "nl": "Kant", "pl": "Koronka"},
    "Belt": {"de": "Gürtel", "fr": "Ceinture", "es": "Cinturón", "it": "Cintura", "pt": "Cinto", "nl": "Riem", "pl": "Pasek"},
    "Belted": {"de": "Mit Gürtel", "fr": "Ceinturé", "es": "Con cinturón", "it": "Con cintura", "pt": "Com cinto", "nl": "Met riem", "pl": "Z paskiem"},
    "Drawstring": {"de": "Kordelzug", "fr": "Cordon de serrage", "es": "Cordón", "it": "Coulisse", "pt": "Cordão", "nl": "Trekkoord", "pl": "Sznurek"},
    "Pleated": {"de": "Plissiert", "fr": "Plissé", "es": "Plisado", "it": "Plissettato", "pt": "Plissado", "nl": "Geplisseerd", "pl": "Plisowany"},
    "Shirred": {"de": "Gerafft", "fr": "Froncé", "es": "Fruncido", "it": "Arricciato", "pt": "Franzido", "nl": "Gerimpeld", "pl": "Marszczony"},
    "Gathered": {"de": "Gerafft", "fr": "Froncé", "es": "Fruncido", "it": "Arricciato", "pt": "Franzido", "nl": "Gerimpeld", "pl": "Marszczony"},
    "Ruched": {"de": "Gerafft", "fr": "Froncé", "es": "Drapeado", "it": "Drappeggiato", "pt": "Drapeado", "nl": "Gerimpeld", "pl": "Drapowany"},
    "Tiered": {"de": "Gestuft", "fr": "À étages", "es": "Escalonado", "it": "A strati", "pt": "Em camadas", "nl": "Gelaagd", "pl": "Warstwowy"},
    "Embroidered": {"de": "Bestickt", "fr": "Brodé", "es": "Bordado", "it": "Ricamato", "pt": "Bordado", "nl": "Geborduurd", "pl": "Haftowany"},
    "Zipper": {"de": "Reißverschluss", "fr": "Fermeture éclair", "es": "Cremallera", "it": "Cerniera", "pt": "Zíper", "nl": "Rits", "pl": "Zamek"},
    "Cutout": {"de": "Ausschnitt", "fr": "Découpe", "es": "Recorte", "it": "Cut-out", "pt": "Recorte", "nl": "Uitsnijding", "pl": "Wycięcie"},
    "Tie Knot": {"de": "Knotenband", "fr": "Nœud", "es": "Lazo", "it": "Fiocco", "pt": "Laço", "nl": "Strik", "pl": "Wiązanie"},
    "Frill Trim": {"de": "Rüschenbesatz", "fr": "Garniture à volants", "es": "Ribete con volantes", "it": "Bordo con volant", "pt": "Acabamento com babados", "nl": "Ruche afwerking", "pl": "Wykończenie falbanką"},

    # === 版型/下摆 (Silhouettes/Hem) - 高频 ===
    "Elastic Waist": {"de": "Elastische Taille", "fr": "Taille élastique", "es": "Cintura elástica", "it": "Vita elastica", "pt": "Cintura elástica", "nl": "Elastische taille", "pl": "Elastyczna talia"},
    "Wrap": {"de": "Wickel", "fr": "Portefeuille", "es": "Cruzado", "it": "A portafoglio", "pt": "Transpassado", "nl": "Wikkel", "pl": "Kopertowy"},
    "Asymmetrical": {"de": "Asymmetrisch", "fr": "Asymétrique", "es": "Asimétrico", "it": "Asimmetrico", "pt": "Assimétrico", "nl": "Asymmetrisch", "pl": "Asymetryczny"},
    "Asymmetrical Hem": {"de": "Asymmetrischer Saum", "fr": "Ourlet asymétrique", "es": "Dobladillo asimétrico", "it": "Orlo asimmetrico", "pt": "Barra assimétrica", "nl": "Asymmetrische zoom", "pl": "Asymetryczny dół"},
    "Split Hem": {"de": "Schlitzsaum", "fr": "Ourlet fendu", "es": "Dobladillo con abertura", "it": "Orlo con spacco", "pt": "Barra com fenda", "nl": "Gespleten zoom", "pl": "Rozcięty dół"},
    "Midi": {"de": "Midi", "fr": "Midi", "es": "Midi", "it": "Midi", "pt": "Midi", "nl": "Midi", "pl": "Midi"},
    "Maxi": {"de": "Maxi", "fr": "Maxi", "es": "Maxi", "it": "Maxi", "pt": "Maxi", "nl": "Maxi", "pl": "Maxi"},

    # === 面料/质地 (Fabrics/Textures) - 高频 ===
    "Knit": {"de": "Strick", "fr": "Tricot", "es": "Punto", "it": "Maglia", "pt": "Tricô", "nl": "Gebreid", "pl": "Dzianina"},
    "Mesh": {"de": "Netz", "fr": "Maille", "es": "Malla", "it": "Rete", "pt": "Malha", "nl": "Mesh", "pl": "Siatka"},
    "Textured": {"de": "Strukturiert", "fr": "Texturé", "es": "Texturizado", "it": "Testurizzato", "pt": "Texturizado", "nl": "Getextureerd", "pl": "Teksturowany"},
    "Stretchy": {"de": "Dehnbar", "fr": "Extensible", "es": "Elástico", "it": "Elasticizzato", "pt": "Elástico", "nl": "Rekbaar", "pl": "Rozciągliwy"},
    "Supersoft": {"de": "Superweich", "fr": "Ultra doux", "es": "Súper suave", "it": "Super morbido", "pt": "Super macio", "nl": "Superzacht", "pl": "Super miękki"},

    # === 风格 (Styles) - 高频 ===
    "Boho": {"de": "Boho", "fr": "Bohème", "es": "Boho", "it": "Boho", "pt": "Boho", "nl": "Boho", "pl": "Boho"},
}

# ============================================================
# 服装术语表 - 完整版 (180+条)
# 基于数据库词频分析，选取出现频率 >= 100 的术语
# ============================================================
FASHION_FULL = {
    **FASHION_CORE,  # 包含核心版所有术语

    # === 更多服装类型 (Garment Types) ===
    "Jacket": {"de": "Jacke", "fr": "Veste", "es": "Chaqueta", "it": "Giacca", "pt": "Jaqueta", "nl": "Jasje", "pl": "Kurtka"},
    "Coat": {"de": "Mantel", "fr": "Manteau", "es": "Abrigo", "it": "Cappotto", "pt": "Casaco", "nl": "Jas", "pl": "Płaszcz"},
    "Shorts": {"de": "Shorts", "fr": "Short", "es": "Pantalón corto", "it": "Pantaloncini", "pt": "Shorts", "nl": "Korte broek", "pl": "Szorty"},
    "Leggings": {"de": "Leggings", "fr": "Leggings", "es": "Leggings", "it": "Leggings", "pt": "Leggings", "nl": "Legging", "pl": "Legginsy"},
    "Romper": {"de": "Spielanzug", "fr": "Combishort", "es": "Mono corto", "it": "Pagliaccetto", "pt": "Macaquinho", "nl": "Playsuit", "pl": "Rampers"},
    "Vest": {"de": "Weste", "fr": "Gilet", "es": "Chaleco", "it": "Gilet", "pt": "Colete", "nl": "Vest", "pl": "Kamizelka"},
    "Blazer": {"de": "Blazer", "fr": "Blazer", "es": "Blazer", "it": "Blazer", "pt": "Blazer", "nl": "Blazer", "pl": "Blazer"},
    "Shirt": {"de": "Hemd", "fr": "Chemise", "es": "Camisa", "it": "Camicia", "pt": "Camisa", "nl": "Overhemd", "pl": "Koszula"},
    "Cami Dress": {"de": "Trägerkleid", "fr": "Robe à bretelles", "es": "Vestido de tirantes", "it": "Abito con bretelle", "pt": "Vestido de alças", "nl": "Spaghettibandjes jurk", "pl": "Sukienka na ramiączkach"},
    "Tank Dress": {"de": "Trägerkleid", "fr": "Robe débardeur", "es": "Vestido de tirantes", "it": "Abito canotta", "pt": "Vestido regata", "nl": "Mouwloze jurk", "pl": "Sukienka na ramiączkach"},
    "Swim Top": {"de": "Badeoberteil", "fr": "Haut de bain", "es": "Top de baño", "it": "Top da bagno", "pt": "Top de banho", "nl": "Zwemtop", "pl": "Góra od kostiumu"},
    "One-Piece Swimsuit": {"de": "Badeanzug", "fr": "Maillot une pièce", "es": "Bañador", "it": "Costume intero", "pt": "Maiô", "nl": "Badpak", "pl": "Kostium jednoczęściowy"},
    "Sleep Dress": {"de": "Nachthemd", "fr": "Chemise de nuit", "es": "Camisón", "it": "Camicia da notte", "pt": "Camisola", "nl": "Nachthemd", "pl": "Koszula nocna"},
    "Lounge": {"de": "Loungewear", "fr": "Tenue d'intérieur", "es": "Ropa de estar", "it": "Abbigliamento da casa", "pt": "Loungewear", "nl": "Loungewear", "pl": "Odzież domowa"},

    # === 更多领型 (Necklines) ===
    "Keyhole": {"de": "Schlüsselloch", "fr": "Trou de serrure", "es": "Ojo de cerradura", "it": "Keyhole", "pt": "Gota", "nl": "Sleutelgat", "pl": "Łezka"},
    "Halter": {"de": "Neckholder", "fr": "Col licou", "es": "Cuello halter", "it": "Collo all'americana", "pt": "Frente única", "nl": "Halternek", "pl": "Wiązany na szyi"},
    "Mock Neck": {"de": "Stehkragen", "fr": "Col montant", "es": "Cuello alto", "it": "Collo alto", "pt": "Gola alta", "nl": "Opstaande kraag", "pl": "Stójka"},
    "Cold Shoulder": {"de": "Cold Shoulder", "fr": "Épaules dénudées", "es": "Hombros descubiertos", "it": "Spalle scoperte", "pt": "Ombros de fora", "nl": "Cold shoulder", "pl": "Odkryte ramiona"},
    "Off Shoulder": {"de": "Schulterfrei", "fr": "Épaules dénudées", "es": "Hombros descubiertos", "it": "Spalle scoperte", "pt": "Ombro a ombro", "nl": "Off-shoulder", "pl": "Opadające ramiona"},
    "Heart Neckline": {"de": "Herzausschnitt", "fr": "Décolleté cœur", "es": "Escote corazón", "it": "Scollo a cuore", "pt": "Decote coração", "nl": "Hartvormige hals", "pl": "Dekolt serce"},
    "Tie Neck": {"de": "Schluppe", "fr": "Col lavallière", "es": "Cuello con lazo", "it": "Collo con fiocco", "pt": "Gola com laço", "nl": "Strikkraag", "pl": "Kołnierz z kokardą"},

    # === 更多袖型 (Sleeves) ===
    "Cap Sleeve": {"de": "Kappenärmel", "fr": "Manche courte", "es": "Manga casquillo", "it": "Manica a aletta", "pt": "Manga curta", "nl": "Kapmouw", "pl": "Krótkie rękawy"},
    "Bell Sleeve": {"de": "Trompetenärmel", "fr": "Manche évasée", "es": "Manga campana", "it": "Manica a campana", "pt": "Manga sino", "nl": "Klokmouw", "pl": "Rękawy dzwony"},
    "Batwing Sleeve": {"de": "Fledermausärmel", "fr": "Manche chauve-souris", "es": "Manga murciélago", "it": "Manica a pipistrello", "pt": "Manga morcego", "nl": "Vleermuismouw", "pl": "Rękawy nietoperz"},
    "Puff Sleeve": {"de": "Puffärmel", "fr": "Manche bouffante", "es": "Manga abullonada", "it": "Manica a sbuffo", "pt": "Manga bufante", "nl": "Pofmouw", "pl": "Bufiaste rękawy"},
    "Sleeveless": {"de": "Ärmellos", "fr": "Sans manches", "es": "Sin mangas", "it": "Senza maniche", "pt": "Sem mangas", "nl": "Mouwloos", "pl": "Bez rękawów"},
    "Tab Sleeve": {"de": "Ärmel mit Lasche", "fr": "Manche à patte", "es": "Manga con trabilla", "it": "Manica con linguetta", "pt": "Manga com pala", "nl": "Mouw met tab", "pl": "Rękaw z patką"},
    "Petal Sleeve": {"de": "Blütenblattärmel", "fr": "Manche pétale", "es": "Manga pétalo", "it": "Manica a petalo", "pt": "Manga pétala", "nl": "Bloembladmouw", "pl": "Rękaw płatkowy"},
    "Kimono": {"de": "Kimono", "fr": "Kimono", "es": "Kimono", "it": "Kimono", "pt": "Quimono", "nl": "Kimono", "pl": "Kimono"},
    "Long Sleeve": {"de": "Langarm", "fr": "Manches longues", "es": "Manga larga", "it": "Manica lunga", "pt": "Manga longa", "nl": "Lange mouw", "pl": "Długi rękaw"},
    "Half Sleeve": {"de": "Halbarm", "fr": "Demi-manches", "es": "Media manga", "it": "Mezza manica", "pt": "Meia manga", "nl": "Halve mouw", "pl": "Rękaw do łokcia"},

    # === 更多图案 (Patterns) ===
    "Tie Dye": {"de": "Batik", "fr": "Tie and dye", "es": "Tie dye", "it": "Tie dye", "pt": "Tie dye", "nl": "Tie-dye", "pl": "Tie dye"},
    "Tropical Print": {"de": "Tropendruck", "fr": "Imprimé tropical", "es": "Estampado tropical", "it": "Stampa tropicale", "pt": "Estampa tropical", "nl": "Tropische print", "pl": "Wzór tropikalny"},
    "Paisley": {"de": "Paisley", "fr": "Cachemire", "es": "Cachemir", "it": "Paisley", "pt": "Paisley", "nl": "Paisley", "pl": "Paisley"},
    "Gingham": {"de": "Vichy-Karo", "fr": "Vichy", "es": "Cuadros vichy", "it": "Quadretti vichy", "pt": "Xadrez vichy", "nl": "Boerenbont", "pl": "Kratka vichy"},
    "Ombre": {"de": "Ombré", "fr": "Ombré", "es": "Degradado", "it": "Sfumato", "pt": "Degradê", "nl": "Ombré", "pl": "Ombre"},
    "Two Tone": {"de": "Zweifarbig", "fr": "Bicolore", "es": "Bicolor", "it": "Bicolore", "pt": "Bicolor", "nl": "Tweekleurig", "pl": "Dwukolorowy"},
    "Color Block": {"de": "Farbblöcke", "fr": "Blocs de couleur", "es": "Bloques de color", "it": "Blocchi di colore", "pt": "Blocos de cor", "nl": "Kleurblokken", "pl": "Bloki kolorów"},
    "Houndstooth": {"de": "Hahnentritt", "fr": "Pied-de-poule", "es": "Pata de gallo", "it": "Pied de poule", "pt": "Pied de poule", "nl": "Pied-de-poule", "pl": "Pepitka"},
    "Abstract": {"de": "Abstrakt", "fr": "Abstrait", "es": "Abstracto", "it": "Astratto", "pt": "Abstrato", "nl": "Abstract", "pl": "Abstrakcyjny"},

    # === 更多工艺细节 (Details) ===
    "Lace Trim": {"de": "Spitzenbesatz", "fr": "Bordure en dentelle", "es": "Ribete de encaje", "it": "Bordo in pizzo", "pt": "Acabamento em renda", "nl": "Kanten rand", "pl": "Wykończenie koronkowe"},
    "Lace Panel": {"de": "Spitzeneinsatz", "fr": "Panneau en dentelle", "es": "Panel de encaje", "it": "Pannello in pizzo", "pt": "Painel de renda", "nl": "Kanten paneel", "pl": "Panel koronkowy"},
    "Ruffle Trim": {"de": "Rüschenbesatz", "fr": "Bordure à volants", "es": "Ribete con volantes", "it": "Bordo con volant", "pt": "Acabamento com babados", "nl": "Ruche rand", "pl": "Wykończenie falbanką"},
    "Ruffle Hem": {"de": "Rüschensaum", "fr": "Ourlet à volants", "es": "Dobladillo con volantes", "it": "Orlo con volant", "pt": "Barra com babados", "nl": "Ruche zoom", "pl": "Dół z falbanami"},
    "Layered Hem": {"de": "Lagensaum", "fr": "Ourlet superposé", "es": "Dobladillo en capas", "it": "Orlo a strati", "pt": "Barra em camadas", "nl": "Gelaagde zoom", "pl": "Warstwowy dół"},
    "Arc Hem": {"de": "Bogensaum", "fr": "Ourlet arrondi", "es": "Dobladillo curvado", "it": "Orlo arrotondato", "pt": "Barra arredondada", "nl": "Gebogen zoom", "pl": "Zaokrąglony dół"},
    "Hanky Hem": {"de": "Zipfelsaum", "fr": "Ourlet mouchoir", "es": "Dobladillo de pañuelo", "it": "Orlo a fazzoletto", "pt": "Barra assimétrica", "nl": "Puntige zoom", "pl": "Asymetryczny dół"},
    "High Low": {"de": "Vokuhila", "fr": "Asymétrique", "es": "Asimétrico", "it": "Asimmetrico", "pt": "Mullet", "nl": "High-low", "pl": "Asymetryczny"},
    "Twist Front": {"de": "Gedrehte Front", "fr": "Devant torsadé", "es": "Frente cruzado", "it": "Davanti incrociato", "pt": "Frente torcida", "nl": "Gedraaide voorkant", "pl": "Skręcony przód"},
    "Open Front": {"de": "Offene Front", "fr": "Devant ouvert", "es": "Frente abierto", "it": "Davanti aperto", "pt": "Frente aberta", "nl": "Open voorkant", "pl": "Otwarty przód"},
    "Crisscross": {"de": "Überkreuz", "fr": "Croisé", "es": "Entrecruzado", "it": "Incrociato", "pt": "Cruzado", "nl": "Gekruist", "pl": "Skrzyżowany"},
    "Crossover": {"de": "Überkreuzung", "fr": "Croisé", "es": "Cruzado", "it": "Incrociato", "pt": "Cruzado", "nl": "Overslag", "pl": "Kopertowy"},
    "Tassel": {"de": "Quaste", "fr": "Pompon", "es": "Borla", "it": "Nappa", "pt": "Borla", "nl": "Kwast", "pl": "Frędzel"},
    "Bowknot": {"de": "Schleife", "fr": "Nœud papillon", "es": "Lazo", "it": "Fiocco", "pt": "Laço", "nl": "Strik", "pl": "Kokarda"},
    "Sequin": {"de": "Pailletten", "fr": "Paillettes", "es": "Lentejuelas", "it": "Paillettes", "pt": "Lantejoulas", "nl": "Pailletten", "pl": "Cekiny"},
    "Beaded": {"de": "Mit Perlen", "fr": "Perlé", "es": "Con cuentas", "it": "Con perline", "pt": "Com contas", "nl": "Met kralen", "pl": "Z koralikami"},
    "Rhinestone": {"de": "Strass", "fr": "Strass", "es": "Pedrería", "it": "Strass", "pt": "Strass", "nl": "Strass", "pl": "Cyrkonie"},
    "Pearl": {"de": "Perle", "fr": "Perle", "es": "Perla", "it": "Perla", "pt": "Pérola", "nl": "Parel", "pl": "Perła"},
    "Buckle": {"de": "Schnalle", "fr": "Boucle", "es": "Hebilla", "it": "Fibbia", "pt": "Fivela", "nl": "Gesp", "pl": "Klamra"},
    "Slit": {"de": "Schlitz", "fr": "Fente", "es": "Abertura", "it": "Spacco", "pt": "Fenda", "nl": "Split", "pl": "Rozcięcie"},
    "Hollow Out": {"de": "Durchbrochen", "fr": "Ajouré", "es": "Calado", "it": "Traforato", "pt": "Vazado", "nl": "Opengewerkt", "pl": "Ażurowy"},
    "Eyelet": {"de": "Ösen", "fr": "Œillets", "es": "Ojales", "it": "Occhielli", "pt": "Ilhós", "nl": "Oogjes", "pl": "Oczka"},

    # === 更多版型 (Silhouettes) ===
    "Flare": {"de": "Ausgestellt", "fr": "Évasé", "es": "Acampanado", "it": "Svasato", "pt": "Evasê", "nl": "Uitlopend", "pl": "Rozkloszowany"},
    "Skinny": {"de": "Skinny", "fr": "Skinny", "es": "Pitillo", "it": "Skinny", "pt": "Skinny", "nl": "Skinny", "pl": "Skinny"},
    "Straight": {"de": "Gerade", "fr": "Droit", "es": "Recto", "it": "Dritto", "pt": "Reto", "nl": "Recht", "pl": "Prosty"},
    "Straight-Leg": {"de": "Gerades Bein", "fr": "Jambe droite", "es": "Pierna recta", "it": "Gamba dritta", "pt": "Perna reta", "nl": "Rechte pijp", "pl": "Prosta nogawka"},
    "Wide Leg": {"de": "Weites Bein", "fr": "Jambe large", "es": "Pierna ancha", "it": "Gamba larga", "pt": "Perna larga", "nl": "Wijde pijp", "pl": "Szerokie nogawki"},
    "Wide-Leg": {"de": "Weites Bein", "fr": "Jambe large", "es": "Pierna ancha", "it": "Gamba larga", "pt": "Perna larga", "nl": "Wijde pijp", "pl": "Szerokie nogawki"},
    "Bootcut": {"de": "Bootcut", "fr": "Bootcut", "es": "Bootcut", "it": "Bootcut", "pt": "Bootcut", "nl": "Bootcut", "pl": "Bootcut"},
    "A-Line": {"de": "A-Linie", "fr": "Ligne A", "es": "Línea A", "it": "Linea A", "pt": "Linha A", "nl": "A-lijn", "pl": "Linia A"},
    "Fitted": {"de": "Tailliert", "fr": "Ajusté", "es": "Entallado", "it": "Aderente", "pt": "Ajustado", "nl": "Aansluitend", "pl": "Dopasowany"},
    "Flowy": {"de": "Fließend", "fr": "Fluide", "es": "Fluido", "it": "Fluido", "pt": "Fluido", "nl": "Vloeiend", "pl": "Zwiewny"},
    "High Rise": {"de": "Hohe Taille", "fr": "Taille haute", "es": "Tiro alto", "it": "Vita alta", "pt": "Cintura alta", "nl": "Hoge taille", "pl": "Wysoka talia"},
    "Mid Rise": {"de": "Mittlere Taille", "fr": "Taille moyenne", "es": "Tiro medio", "it": "Vita media", "pt": "Cintura média", "nl": "Middelhoge taille", "pl": "Średnia talia"},
    "Cropped": {"de": "Kurz geschnitten", "fr": "Court", "es": "Corto", "it": "Corto", "pt": "Cropped", "nl": "Kort", "pl": "Krótki"},
    "Mini": {"de": "Mini", "fr": "Mini", "es": "Mini", "it": "Mini", "pt": "Mini", "nl": "Mini", "pl": "Mini"},

    # === 更多面料 (Fabrics) ===
    "Cotton": {"de": "Baumwolle", "fr": "Coton", "es": "Algodón", "it": "Cotone", "pt": "Algodão", "nl": "Katoen", "pl": "Bawełna"},
    "Velvet": {"de": "Samt", "fr": "Velours", "es": "Terciopelo", "it": "Velluto", "pt": "Veludo", "nl": "Fluweel", "pl": "Aksamit"},
    "Chiffon": {"de": "Chiffon", "fr": "Mousseline", "es": "Gasa", "it": "Chiffon", "pt": "Chiffon", "nl": "Chiffon", "pl": "Szyfon"},
    "Denim": {"de": "Denim", "fr": "Denim", "es": "Vaquero", "it": "Denim", "pt": "Jeans", "nl": "Denim", "pl": "Dżins"},
    "Rayon": {"de": "Viskose", "fr": "Rayonne", "es": "Rayón", "it": "Rayon", "pt": "Rayon", "nl": "Rayon", "pl": "Wiskoza"},
    "Sheer": {"de": "Durchsichtig", "fr": "Transparent", "es": "Transparente", "it": "Trasparente", "pt": "Transparente", "nl": "Doorzichtig", "pl": "Przezroczysty"},
    "Woven": {"de": "Gewebt", "fr": "Tissé", "es": "Tejido", "it": "Tessuto", "pt": "Tecido", "nl": "Geweven", "pl": "Tkany"},
    "Rib Knit": {"de": "Rippstrick", "fr": "Côtelé", "es": "Punto acanalado", "it": "Maglia a coste", "pt": "Tricô canelado", "nl": "Ribbreisel", "pl": "Ścieg prążkowany"},
    "Cable Knit": {"de": "Zopfmuster", "fr": "Torsade", "es": "Punto trenzado", "it": "Maglia a treccia", "pt": "Tricô trançado", "nl": "Kabelbreisel", "pl": "Splot warkoczowy"},
    "Waffle Knit": {"de": "Waffelmuster", "fr": "Maille gaufrée", "es": "Punto gofre", "it": "Maglia a nido d'ape", "pt": "Tricô waffle", "nl": "Wafelbreisel", "pl": "Splot waflowy"},
    "Pointelle Knit": {"de": "Lochmuster", "fr": "Maille ajourée", "es": "Punto calado", "it": "Maglia traforata", "pt": "Tricô rendado", "nl": "Ajourbreisel", "pl": "Ażurowy splot"},
    "Ribbed": {"de": "Gerippt", "fr": "Côtelé", "es": "Acanalado", "it": "A coste", "pt": "Canelado", "nl": "Geribbeld", "pl": "Prążkowany"},
    "Jacquard": {"de": "Jacquard", "fr": "Jacquard", "es": "Jacquard", "it": "Jacquard", "pt": "Jacquard", "nl": "Jacquard", "pl": "Żakard"},
    "Tweed": {"de": "Tweed", "fr": "Tweed", "es": "Tweed", "it": "Tweed", "pt": "Tweed", "nl": "Tweed", "pl": "Tweed"},
    "Corduroy": {"de": "Cord", "fr": "Velours côtelé", "es": "Pana", "it": "Velluto a coste", "pt": "Veludo cotelê", "nl": "Ribfluweel", "pl": "Sztruks"},
    "Plisse": {"de": "Plissee", "fr": "Plissé", "es": "Plisado", "it": "Plissé", "pt": "Plissado", "nl": "Plissé", "pl": "Plisowany"},
    "Crochet": {"de": "Häkel", "fr": "Crochet", "es": "Ganchillo", "it": "Uncinetto", "pt": "Crochê", "nl": "Gehaakt", "pl": "Szydełkowy"},
    "Crochet Lace": {"de": "Häkelspitze", "fr": "Dentelle au crochet", "es": "Encaje de ganchillo", "it": "Pizzo all'uncinetto", "pt": "Renda de crochê", "nl": "Gehaakte kant", "pl": "Koronka szydełkowa"},
    "Guipure Lace": {"de": "Guipure-Spitze", "fr": "Guipure", "es": "Guipur", "it": "Guipure", "pt": "Guipure", "nl": "Guipure kant", "pl": "Koronka gipiurowa"},
    "Broderie Anglaise": {"de": "Lochstickerei", "fr": "Broderie anglaise", "es": "Bordado inglés", "it": "Sangallo", "pt": "Bordado inglês", "nl": "Broderie anglaise", "pl": "Haft angielski"},

    # === 更多风格 (Styles) ===
    "Vintage": {"de": "Vintage", "fr": "Vintage", "es": "Vintage", "it": "Vintage", "pt": "Vintage", "nl": "Vintage", "pl": "Vintage"},
    "Holiday": {"de": "Urlaub", "fr": "Vacances", "es": "Vacaciones", "it": "Vacanza", "pt": "Férias", "nl": "Vakantie", "pl": "Wakacyjny"},
    "Halloween": {"de": "Halloween", "fr": "Halloween", "es": "Halloween", "it": "Halloween", "pt": "Halloween", "nl": "Halloween", "pl": "Halloween"},
    "Christmas": {"de": "Weihnachten", "fr": "Noël", "es": "Navidad", "it": "Natale", "pt": "Natal", "nl": "Kerst", "pl": "Świąteczny"},
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
    "fashion_hard": {
        "name": "Fashion (Hard Terms)",
        "description": "难翻译术语表，13条基于数据科学筛选的术语",
        "terms": FASHION_HARD,
        "token_estimate": 400,
    },
    "fashion_core": {
        "name": "Fashion (Core)",
        "description": "服装核心版术语表，80条高频术语（频率≥500）",
        "terms": FASHION_CORE,
        "token_estimate": 2200,
    },
    "fashion_full": {
        "name": "Fashion (Full)",
        "description": "服装完整版术语表，180+条术语（频率≥100）",
        "terms": FASHION_FULL,
        "token_estimate": 5000,
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


# 数据库词频分析统计 (28,255条产品标题)
DATABASE_STATS = {
    "total_titles": 28255,
    "analysis_method": "词频统计",
    "top_words": {
        "Dress": 8976, "Print": 5560, "Neck": 5442, "Sleeve": 5072,
        "Floral": 4542, "Pocket": 4305, "Blouse": 3076, "Hem": 2945,
        "Solid": 2926, "Button": 2784, "Contrast": 2775, "Midi": 2765,
        "Patchwork": 2503, "Waist": 2413, "T-shirt": 2238, "Plain": 2207,
        "Lace": 2027, "Detail": 2003, "Knit": 1948, "Elastic": 1796,
    },
    "top_bigrams": {
        "Midi Dress": 2577, "Floral Print": 1657, "Elastic Waist": 1416,
        "Round Neck": 1153, "Button Detail": 1142, "Lantern Sleeve": 1115,
        "Sleeve Blouse": 876, "Sleeve Dress": 732, "Crew Neck": 679,
        "Ditsy Floral": 653, "Button Up": 639, "Swim Dress": 612,
    },
}


# ============================================================
# V4 术语表 - 完整运营术语表 (210条)
# 数据来源: glossary_complete.csv
# 支持智能匹配：只发送文本中出现的术语
# ============================================================

# 缓存 V4 术语表
_GLOSSARY_V4_CACHE: Optional[Dict] = None


def _load_glossary_v4() -> Dict:
    """加载 V4 术语表（带缓存）"""
    global _GLOSSARY_V4_CACHE
    if _GLOSSARY_V4_CACHE is not None:
        return _GLOSSARY_V4_CACHE

    # 从 JSON 文件加载
    json_path = Path(__file__).parent.parent.parent / "data" / "glossary_multilang.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            _GLOSSARY_V4_CACHE = json.load(f)
    else:
        _GLOSSARY_V4_CACHE = {}

    return _GLOSSARY_V4_CACHE


def _build_term_patterns(glossary: Dict) -> List[tuple]:
    """
    构建术语匹配模式（按长度降序排列，优先匹配长术语）

    匹配策略：
    - 含连字符的术语（如 "T-shirts"）：使用标准词边界 \\b
    - 不含连字符的术语（如 "Shirts"）：使用更严格的边界检查，
      确保前后不是字母或连字符，避免匹配到复合词的一部分
      （例如 "Shirts" 不应匹配 "T-shirts" 中的 "shirts"）

    Returns:
        List of (term, pattern) tuples
    """
    patterns = []
    for term in glossary.keys():
        # 转义特殊字符
        escaped = re.escape(term)

        if '-' in term:
            # 含连字符的术语，使用标准词边界
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
        else:
            # 不含连字符的术语，使用更严格的边界检查
            # (?<![a-zA-Z\-]) 前面不能是字母或连字符
            # (?![a-zA-Z\-]) 后面不能是字母或连字符
            pattern = re.compile(
                r'(?<![a-zA-Z\-])' + escaped + r'(?![a-zA-Z\-])',
                re.IGNORECASE
            )
        patterns.append((term, pattern))

    # 按术语长度降序排列，优先匹配长术语（如 "V Neck" 优先于 "V"）
    patterns.sort(key=lambda x: len(x[0]), reverse=True)
    return patterns


# 缓存匹配模式
_TERM_PATTERNS_CACHE: Optional[List[tuple]] = None


def match_glossary_terms(texts: List[str], glossary_id: str = "fashion_v4") -> Dict:
    """
    从文本中匹配术语表中的术语（短语优先，排除冗余单词）

    匹配策略：
    1. 按术语长度降序匹配，优先匹配长术语（短语）
    2. 当短语被匹配后，其包含的单词不再单独匹配
       例如：匹配到 "V Neck" 后，不会再单独匹配 "Neck"

    Args:
        texts: 待匹配的文本列表
        glossary_id: 术语表ID

    Returns:
        匹配到的术语子集 {term: translations}
    """
    global _TERM_PATTERNS_CACHE

    # 获取术语表
    if glossary_id == "fashion_v4":
        glossary = _load_glossary_v4()
    else:
        glossary = get_glossary(glossary_id)

    if not glossary:
        return {}

    # 构建或获取匹配模式
    if glossary_id == "fashion_v4" and _TERM_PATTERNS_CACHE is not None:
        patterns = _TERM_PATTERNS_CACHE
    else:
        patterns = _build_term_patterns(glossary)
        if glossary_id == "fashion_v4":
            _TERM_PATTERNS_CACHE = patterns

    # 合并所有文本进行匹配
    combined_text = " ".join(texts)

    # 匹配术语（短语优先策略）
    matched_terms: Set[str] = set()
    covered_words: Set[str] = set()  # 已被短语覆盖的单词

    # patterns 已按长度降序排列，先匹配长术语
    for term, pattern in patterns:
        if pattern.search(combined_text):
            # 检查此术语是否已被更长的短语覆盖
            term_words = set(term.lower().split())
            if not term_words.issubset(covered_words):
                matched_terms.add(term)
                # 将此术语的所有单词标记为已覆盖
                covered_words.update(term_words)

    # 返回匹配到的术语及其翻译
    return {term: glossary[term] for term in matched_terms if term in glossary}


def build_matched_glossary_prompt(
    texts: List[str],
    target_langs: List[str],
    glossary_id: str = "fashion_v4"
) -> str:
    """
    构建只包含匹配术语的提示词片段

    Args:
        texts: 待翻译的文本列表
        target_langs: 目标语言代码列表
        glossary_id: 术语表ID

    Returns:
        格式化的术语表字符串（只包含匹配到的术语）
    """
    # 匹配术语
    matched = match_glossary_terms(texts, glossary_id)

    if not matched:
        return ""

    # 构建表头
    header = "| English | " + " | ".join([lang.upper() for lang in target_langs]) + " |"
    separator = "|" + "|".join(["---"] * (len(target_langs) + 1)) + "|"

    rows = []
    for term, translations in sorted(matched.items()):
        row_values = [term]
        for lang in target_langs:
            row_values.append(translations.get(lang, term))
        rows.append("| " + " | ".join(row_values) + " |")

    table = "\n".join([header, separator] + rows)

    return f"""## Terminology Reference ({len(matched)} terms matched)
{table}
"""


# 注册 V4 术语表
def _register_v4_glossary():
    """延迟注册 V4 术语表"""
    v4_glossary = _load_glossary_v4()
    if v4_glossary and "fashion_v4" not in GLOSSARY_REGISTRY:
        GLOSSARY_REGISTRY["fashion_v4"] = {
            "name": "Fashion V4 (Smart Match)",
            "description": "完整运营术语表，210条术语，支持智能匹配",
            "terms": v4_glossary,
            "token_estimate": 6000,  # 完整时的估计
        }


# 自动注册
_register_v4_glossary()
