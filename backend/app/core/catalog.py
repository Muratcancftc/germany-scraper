"""In-memory catalog of cities and target categories.

Replaces the database seed data. The list is the single source of truth; the
frontend renders it dynamically via the API. No database is used.
"""

# ruff: noqa: E501 (long search-term lists in string literals)

from dataclasses import dataclass, field


@dataclass
class City:
    id: int
    name: str
    slug: str
    state: str


@dataclass
class Category:
    id: int
    name: str
    slug: str
    group: str
    description: str
    search_terms: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)


CITIES: list[City] = [
    City(1, "Berlin", "berlin", "Berlin"),
    City(2, "Hamburg", "hamburg", "Hamburg"),
    City(3, "München", "muenchen", "Bayern"),
    City(4, "Köln", "koeln", "Nordrhein-Westfalen"),
    City(5, "Frankfurt am Main", "frankfurt", "Hessen"),
    City(6, "Stuttgart", "stuttgart", "Baden-Württemberg"),
    City(7, "Düsseldorf", "duesseldorf", "Nordrhein-Westfalen"),
    City(8, "Dortmund", "dortmund", "Nordrhein-Westfalen"),
    City(9, "Essen", "essen", "Nordrhein-Westfalen"),
    City(10, "Leipzig", "leipzig", "Sachsen"),
    City(11, "Bremen", "bremen", "Bremen"),
    City(12, "Dresden", "dresden", "Sachsen"),
    City(13, "Hannover", "hannover", "Niedersachsen"),
    City(14, "Nürnberg", "nuernberg", "Bayern"),
    City(15, "Duisburg", "duisburg", "Nordrhein-Westfalen"),
    City(16, "Bochum", "bochum", "Nordrhein-Westfalen"),
    City(17, "Wuppertal", "wuppertal", "Nordrhein-Westfalen"),
    City(18, "Bielefeld", "bielefeld", "Nordrhein-Westfalen"),
    City(19, "Bonn", "bonn", "Nordrhein-Westfalen"),
    City(20, "Münster", "muenster", "Nordrhein-Westfalen"),
]

CATEGORY_GROUPS: dict[str, str] = {
    "gewerbe": "Gewerbe / Industrie",
    "oeffentlich": "Öffentliche Hand & Soziales",
    "sonstige": "Sonstige",
}

CATEGORIES: list[Category] = [
    # --- Gewerbe / Industrie ---
    Category(
        1, "Gewerbe-/Industrieparks (Facility-Management)", "gewerbe-industrieparks",
        "gewerbe", "Gewerbe- und Industrieparks mit Facility-Management",
        search_terms=["Gewerbepark", "Industriepark", "Gewerbegebiet", "Industriegebiet", "Businesspark"],
        keywords=["gewerbepark", "industriepark", "gewerbegebiet", "industriegebiet",
                  "businesspark", "facility management", "gebäudemanagement"],
    ),
    Category(
        2, "Speditionen / Logistikzentren", "speditionen-logistik", "gewerbe",
        "Speditionen und Logistikzentren",
        search_terms=["Spedition", "Logistikzentrum", "Logistik", "Transport", "Fracht"],
        keywords=["spedition", "logistik", "transport", "fracht", "lager", "versand"],
    ),
    Category(
        3, "Produktionsbetriebe", "produktionsbetriebe", "gewerbe",
        "Produktions- und Industriebetriebe",
        search_terms=["Produktionsbetrieb", "Produktion", "Hersteller", "Fabrik", "Industriebetrieb"],
        keywords=["produktion", "hersteller", "fabrik", "industriebetrieb", "fertigung"],
    ),
    # --- Öffentliche Hand & Soziales ---
    Category(
        4, "Kommunen / Stadtverwaltungen", "kommunen-stadtverwaltungen", "oeffentlich",
        "Kommunen und Stadtverwaltungen",
        search_terms=["Stadtverwaltung", "Kommune", "Gemeinde", "Rathaus"],
        keywords=["stadtverwaltung", "kommune", "gemeinde", "rathaus", "stadt", "amt"],
    ),
    Category(
        5, "Kindergärten / Schulen (Träger)", "kindergaerten-schulen", "oeffentlich",
        "Kindergärten, Kitas und Schulträger",
        search_terms=["Kindergarten", "Kita", "Kindertagesstätte", "Schule", "Schulträger"],
        keywords=["kindergarten", "kita", "kindertagesstätte", "schule", "schulträger"],
    ),
    Category(
        6, "Kirchengemeinden", "kirchengemeinden", "oeffentlich",
        "Kirchen- und Pfarrgemeinden",
        search_terms=["Kirche", "Pfarrgemeinde", "Gemeinde", "Kirchengemeinde"],
        keywords=["kirchengemeinde", "kirche", "pfarrgemeinde", "pfarramt", "gemeinde"],
    ),
    Category(
        7, "Pflegeheime / Seniorenresidenzen", "pflegeheime-seniorenresidenzen", "oeffentlich",
        "Pflegeheime und Seniorenresidenzen",
        search_terms=["Pflegeheim", "Seniorenheim", "Seniorenresidenz", "Altenheim", "Altenpflege"],
        keywords=["pflegeheim", "seniorenheim", "seniorenresidenz", "altenheim", "altenpflege", "pflege"],
    ),
    Category(
        8, "Krankenhäuser / MVZ", "krankenhaeuser-mvz", "oeffentlich",
        "Krankenhäuser und Medizinische Versorgungszentren",
        search_terms=["Krankenhaus", "Klinik", "MVZ", "Medizinisches Versorgungszentrum"],
        keywords=["krankenhaus", "klinik", "mvz", "medizinisches versorgungszentrum", "klinikum"],
    ),
    # --- Sonstige ---
    Category(
        9, "Fitnessstudios", "fitnessstudios", "sonstige",
        "Fitnessstudios und Fitnesscenter",
        search_terms=["Fitnessstudio", "Fitnesscenter", "Fitness Club", "Gym", "Sportstudio"],
        keywords=["fitness", "fitnessstudio", "fitnesscenter", "gym", "sportstudio"],
    ),
    Category(
        10, "Kfz-Werkstätten", "kfz-werkstaetten", "sonstige",
        "Kfz-Werkstätten und Autowerkstätten",
        search_terms=["Kfz-Werkstatt", "Autowerkstatt", "Werkstatt", "KFZ Service", "Kfz-Service"],
        keywords=["kfz", "werkstatt", "autowerkstatt", "fahrzeugservice", "kfz-service"],
    ),
    Category(
        11, "Vereine mit eigenen Immobilien", "vereine-eigene-immobilien", "sonstige",
        "Vereine, die eigene Immobilien besitzen",
        search_terms=["Verein", "Sportverein", "Vereinsheim", "Sportverein Immobilien"],
        keywords=["verein", "sportverein", "vereinsheim", "vereinsgelände", "vereinshaus"],
    ),
    Category(
        12, "Andere Facility-Management-Firmen (als Subunternehmer)", "facility-management", "sonstige",
        "Facility-Management-Firmen und Subunternehmer",
        search_terms=["Facility Management", "Facility-Management", "Gebäudemanagement",
                      "Gebäudeservice", "Hausverwaltung", "Technisches Gebäudemanagement"],
        keywords=["facility management", "facility-management", "gebäudemanagement",
                  "gebäudeservice", "hausverwaltung", "gebäudetechnik", "reinigung"],
    ),
]

CITY_BY_ID: dict[int, City] = {c.id: c for c in CITIES}
CATEGORY_BY_ID: dict[int, Category] = {c.id: c for c in CATEGORIES}


def city_by_id(city_id: int) -> City | None:
    return CITY_BY_ID.get(city_id)


def category_by_id(cat_id: int) -> Category | None:
    return CATEGORY_BY_ID.get(cat_id)
