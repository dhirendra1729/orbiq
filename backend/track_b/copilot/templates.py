"""Bilingual situation copilot response templates in English and Nepali."""

from typing import Any, Dict, List


ENGLISH_TEMPLATES = {
    "hazard_summary": (
        "Based on Sentinel-1 SAR change detection and Copernicus GLO-30 DEM analysis for run {run_id}, "
        "a total of {water_area_sq_km} km² ({water_area_m2} m²) of newly inundated flood water was delineated. "
        "Additionally, {debris_area_sq_km} km² was mapped as candidate debris along flow corridors. "
        "Permanent baseline water accounted for {perm_area_sq_km} km²."
    ),
    "asset_exposure": (
        "Infrastructure exposure assessment identified {exposed_buildings} potentially affected building footprints "
        "and {exposed_roads_km} km of exposed road segments ({exposed_ways} distinct ways). "
        "Inspection is prioritized for {exposed_bridges} bridge structures intersecting the hazard envelope."
    ),
    "access_loss": (
        "Under the {scenario} scenario, access network analysis across {total_settlements} mapped settlements "
        "determined that {cut_off_count} settlements have become newly cut off from hospital services, "
        "and {rerouted_count} settlements require detours exceeding 10% of their baseline travel distance."
    ),
    "unsupported_casualty": (
        "Scope Limitation: Orbiq does not model or estimate casualties, injured individuals, or population counts. "
        "Satellite footprint intersection identifies exposed physical infrastructure only, not building occupancy rates or casualties."
    ),
    "unsupported_destruction": (
        "Scope Limitation: Satellite raster intersection indicates geometric exposure to flood water or debris, "
        "not confirmed structural collapse, bridge pier failure, or physical road impassability. Ground inspection is required."
    ),
    "unsupported_evacuation": (
        "Operational Notice: Orbiq is an educational prototype and does not issue real-time evacuation orders "
        "or calculate dynamic minutes-ahead flood wave arrival times."
    )
}

NEPALI_TEMPLATES = {
    "hazard_summary": (
        "सेन्टिनेल-१ (Sentinel-1) रार परिवर्तन विश्लेषण अनुसार (रन {run_id}), "
        "जम्मा {water_area_sq_km} वर्ग किलोमिटर ({water_area_m2} वर्ग मिटर) नयाँ बाढीको पानी नक्सांकन गरिएको छ। "
        "यसका साथै बहाव क्षेत्रमा {debris_area_sq_km} वर्ग किलोमिटर गेग्रान/पहिरो (debris) पहिचान गरिएको छ। "
        "स्थायी पानीको क्षेत्र {perm_area_sq_km} वर्ग किलोमिटर मापन गरिएको थियो।"
    ),
    "asset_exposure": (
        "पूर्वाधार जोखिम विश्लेषण अनुसार {exposed_buildings} वटा घर/भवनका संरचनाहरू "
        "र {exposed_roads_km} किलोमिटर सडक खण्डहरू बाढीको क्षेत्रमा परेका छन्। "
        "{exposed_bridges} वटा पुलहरू जोखिम क्षेत्रमा रहेकाले तत्काल स्थलगत निरीक्षण आवश्यक देखिन्छ।"
    ),
    "access_loss": (
        "{scenario} परिदृश्य अनुसार, {total_settlements} वटा बस्तीहरूको सडक सञ्जाल विश्लेषण गर्दा "
        "{cut_off_count} वटा बस्तीहरू अस्पताल सेवाबाट पूर्ण रूपमा सम्पर्कविहीन (cut-off) भएका छन्, "
        "र {rerouted_count} वटा बस्तीहरूले १०% भन्दा लामो वैकल्पिक बाटो प्रयोग गर्नुपर्ने अवस्था छ।"
    ),
    "unsupported_casualty": (
        "प्रणालीगत सीमा: फ्लडसिल्डले मानवीय क्षति, घाइते वा जनसंख्याको अनुमान गर्दैन। "
        "उपग्रह नक्सांकनले भौतिक पूर्वाधारको जोखिम मात्र देखाउँछ, मानवीय हताहती वा उद्धार संख्या निर्धारण गर्दैन।"
    ),
    "unsupported_destruction": (
        "प्रणालीगत सीमा: उपग्रह नक्सांकनले पानी वा गेग्रानको सम्पर्क (exposure) मात्र देखाउँछ। "
        "यसले पुल वा भवन पूर्ण रूपमा भत्किएको वा बाटो पूर्ण रूपमा अवरुद्ध भएको पुष्टि गर्दैन। भौतिक परीक्षण आवश्यक पर्दछ।"
    ),
    "unsupported_evacuation": (
        "सूचना: यो प्रणाली शैक्षिक तथा अनुसन्धान प्रोटोटाइप हो। यसले प्रत्यक्ष उद्धार आदेश वा बाढी आउने समय (arrival time) जारी गर्दैन।"
    )
}


def render_response(
    template_key: str,
    language: str,
    slots: Dict[str, Any]
) -> str:
    """Render a verified response text in English or Nepali."""
    templates = NEPALI_TEMPLATES if language == "ne" else ENGLISH_TEMPLATES
    template_str = templates.get(template_key, ENGLISH_TEMPLATES.get(template_key, ""))
    try:
        return template_str.format(**slots)
    except KeyError as exc:
        return f"Fact rendering error: missing slot {exc}"
