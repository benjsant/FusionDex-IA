-- ============================================================
-- FusionDex-IA — Schéma PostgreSQL complet v2
-- Bilingue EN/FR — Pokémon Infinite Fusion
-- ============================================================
--
-- IMPORTANT — Numérotation des Pokémon :
--   pokemon.id         = ID interne Infinite Fusion
--                        (utilisé dans les noms de sprites : head_id.body_id.png)
--   pokemon.national_id = Numéro Pokédex national (pour PokeAPI / Pokepedia)
--   Pour Gen 1-2 les deux IDs coïncident (1-251).
--   Au-delà, IF utilise sa propre numérotation → ne jamais supposer qu'ils sont égaux.
--
-- TYPES :
--   Le jeu contient 27 types : 18 officiels + 9 types propres aux triple fusions.
--   Les types triple-fusion sont traités comme des types uniques dans les calculs.
-- ============================================================


-- ============================================================
-- BLOC 1 — Référentiels de base
-- ============================================================

-- 1. generation
CREATE TABLE IF NOT EXISTS generation (
    id      SERIAL      PRIMARY KEY,
    name_en VARCHAR(30) NOT NULL UNIQUE,   -- 'generation-i'
    name_fr VARCHAR(30) NOT NULL UNIQUE    -- 'génération-i'
);

-- 2. type  (27 types : 18 officiels + 9 triple-fusion)
--    is_triple_fusion_type = TRUE pour les 9 types exclusifs aux triples fusions
CREATE TABLE IF NOT EXISTS type (
    id                   SERIAL      PRIMARY KEY,
    name_en              VARCHAR(30) NOT NULL UNIQUE,
    name_fr              VARCHAR(30),
    is_triple_fusion_type BOOLEAN    NOT NULL DEFAULT FALSE
);

-- 3. ability  (~289 capacités spéciales)
--    Source principale : wiki IF (List of Abilities) — EN + liste Pokémon
--    Source secondaire : CSV fourni par l'utilisateur — FR + descriptions
CREATE TABLE IF NOT EXISTS ability (
    id             SERIAL       PRIMARY KEY,
    name_en        VARCHAR(100) NOT NULL UNIQUE,
    name_fr        VARCHAR(100),
    description_en TEXT,
    description_fr TEXT
);


-- ============================================================
-- BLOC 2 — Moves et CTs
-- ============================================================

-- 4. move  (644 moves présents dans Infinite Fusion)
--    category : Physical | Special | Status
--    source   : 'base' → jeux officiels / 'infinite_fusion' → ajout ou modif IF
CREATE TABLE IF NOT EXISTS move (
    id             SERIAL       PRIMARY KEY,
    name_en        VARCHAR(100) NOT NULL UNIQUE,
    name_fr        VARCHAR(100),
    type_id        INTEGER      NOT NULL REFERENCES type(id),
    category       VARCHAR(10)  NOT NULL CHECK (category IN ('Physical', 'Special', 'Status')),
    power          INTEGER,     -- NULL pour Status
    accuracy       INTEGER,     -- NULL si précision infinie
    pp             INTEGER      NOT NULL,
    description_en TEXT,
    description_fr TEXT,
    source         VARCHAR(20)  NOT NULL DEFAULT 'base'
                                CHECK (source IN ('base', 'infinite_fusion'))
);

-- 5. tm  (121 CTs disponibles dans Infinite Fusion)
CREATE TABLE IF NOT EXISTS tm (
    id       SERIAL  PRIMARY KEY,
    number   INTEGER NOT NULL UNIQUE,   -- 1 = TM01, 121 = TM121
    move_id  INTEGER NOT NULL REFERENCES move(id),
    location TEXT                       -- localisation dans le jeu IF
);


-- ============================================================
-- BLOC 3 — Pokémon de base
-- ============================================================

-- 6. pokemon  (501 Pokémon de base du jeu)
CREATE TABLE IF NOT EXISTS pokemon (
    id              INTEGER      PRIMARY KEY,  -- IF internal ID
    national_id     INTEGER      UNIQUE,       -- National Pokédex (PokeAPI), NULL si pas d'équivalent
    name_en         VARCHAR(100) NOT NULL,
    name_fr         VARCHAR(100),
    generation_id   INTEGER      NOT NULL REFERENCES generation(id),
    hp              INTEGER      NOT NULL,
    attack          INTEGER      NOT NULL,
    defense         INTEGER      NOT NULL,
    sp_attack       INTEGER      NOT NULL,
    sp_defense      INTEGER      NOT NULL,
    speed           INTEGER      NOT NULL,
    base_experience INTEGER,
    is_hoenn_only   BOOLEAN      NOT NULL DEFAULT FALSE,
    sprite_path     TEXT                   -- chemin local ou clé S3
);

-- 7. pokemon_type  (jusqu'à 2 types pour les Pokémon standards)
--    slot 1 = type primaire (obligatoire), slot 2 = type secondaire (optionnel)
--    if_override = TRUE → le type a été modifié dans IF par rapport au jeu officiel
--                  (ex: Scizor dont les types Bug/Steel sont inversés)
CREATE TABLE IF NOT EXISTS pokemon_type (
    pokemon_id  INTEGER NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    type_id     INTEGER NOT NULL REFERENCES type(id),
    slot        INTEGER NOT NULL CHECK (slot IN (1, 2)),
    if_override BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (pokemon_id, slot)
);

-- 8. pokemon_ability  (source : wiki IF + Pokepedia)
--    slot 1, 2 = talents normaux / slot 3 = talent caché
--    if_swapped  = TRUE → slots 1 et 2 échangés par rapport au jeu officiel
--                  (concerne ~15 Pokémon : Pidgey, Ekans, Diglett, Gengar, etc.)
--    if_override = TRUE → le talent a été remplacé par IF
--                  (ex: Gengar a Lévitation au lieu de Corps Maudit)
CREATE TABLE IF NOT EXISTS pokemon_ability (
    pokemon_id  INTEGER NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    ability_id  INTEGER NOT NULL REFERENCES ability(id),
    slot        INTEGER NOT NULL CHECK (slot IN (1, 2, 3)),
    is_hidden   BOOLEAN NOT NULL DEFAULT FALSE,
    if_swapped  BOOLEAN NOT NULL DEFAULT FALSE,
    if_override BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (pokemon_id, slot)
);

-- 9. pokemon_evolution
--    Stocke les chaînes d'évolution de tous les Pokémon.
--    Source : PokeAPI pour les évolutions officielles.
--    Les cas modifiés dans IF sont marqués if_override = TRUE.
--
--    trigger_type : 'level_up' | 'use_item' | 'trade' | 'friendship' | 'other'
--
--    Certains Pokémon ont PLUSIEURS conditions possibles pour la même évolution
--    (ex: Kadabra → Niveau 40 OU Corde de Liaison).
--    Chaque condition possible = une ligne distincte avec le même (pokemon_id, evolves_into_id).
--    L'application traitera ces lignes comme des alternatives (OR).
--
--    if_override = TRUE → la condition a été modifiée par IF
--    if_notes    → description lisible de la condition IF
CREATE TABLE IF NOT EXISTS pokemon_evolution (
    id              SERIAL       PRIMARY KEY,
    pokemon_id      INTEGER      NOT NULL REFERENCES pokemon(id),         -- Pokémon de départ
    evolves_into_id INTEGER      NOT NULL REFERENCES pokemon(id),         -- Pokémon cible
    trigger_type    VARCHAR(20)  NOT NULL CHECK (
                        trigger_type IN ('level_up', 'use_item', 'trade', 'friendship', 'other')
                    ),
    min_level       INTEGER,     -- niveau minimum (level_up)
    item_name_en    VARCHAR(100),-- nom de l'objet requis (use_item ou trade+item)
    item_name_fr    VARCHAR(100),
    if_override     BOOLEAN      NOT NULL DEFAULT FALSE,
    if_notes        TEXT,        -- description lisible de la condition modifiée dans IF
    UNIQUE (pokemon_id, evolves_into_id, trigger_type, item_name_en)
);


-- ============================================================
-- BLOC 4 — Localisations et movesets
-- ============================================================

-- 10. location  (zones du jeu Infinite Fusion)
CREATE TABLE IF NOT EXISTS location (
    id      SERIAL       PRIMARY KEY,
    name_en VARCHAR(200) NOT NULL UNIQUE,
    name_fr VARCHAR(200),
    region  VARCHAR(50)   -- 'Kanto', 'Johto', 'Other'
);

-- 11. pokemon_location  (où trouver chaque Pokémon dans IF)
--     method : 'wild' | 'gift' | 'trade' | 'static' | 'fishing' | 'headbutt'
CREATE TABLE IF NOT EXISTS pokemon_location (
    id          SERIAL      PRIMARY KEY,
    pokemon_id  INTEGER     NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    location_id INTEGER     NOT NULL REFERENCES location(id),
    method      VARCHAR(20) CHECK (
                    method IN ('wild', 'gift', 'trade', 'static', 'fishing', 'headbutt')
                ),
    notes       TEXT,
    UNIQUE (pokemon_id, location_id, method)
);

-- 12. pokemon_move  (moveset complet — source duale Pokepedia + IF)
--
--     method : 'level_up' | 'tm' | 'tutor' | 'breeding' | 'special'
--     source : 'base'            → Pokepedia Gen 1-7 (jeux officiels)
--              'infinite_fusion' → ajout ou override propre à IF
--
--     Exemple Azumarill + Aqua Jet :
--       row 1 : method='breeding', source='base'             (Pokepedia)
--       row 2 : method='tm',       source='infinite_fusion'  (CT ajoutée dans IF)
CREATE TABLE IF NOT EXISTS pokemon_move (
    id          SERIAL      PRIMARY KEY,
    pokemon_id  INTEGER     NOT NULL REFERENCES pokemon(id) ON DELETE CASCADE,
    move_id     INTEGER     NOT NULL REFERENCES move(id),
    method      VARCHAR(20) NOT NULL CHECK (
                    method IN ('level_up', 'tm', 'tutor', 'breeding', 'special')
                ),
    level       INTEGER,    -- niveau d'apprentissage (level_up uniquement)
    source      VARCHAR(20) NOT NULL DEFAULT 'base'
                            CHECK (source IN ('base', 'infinite_fusion')),
    UNIQUE (pokemon_id, move_id, method)
);


-- ============================================================
-- BLOC 5 — Triple Fusions
-- ============================================================

-- 13. triple_fusion  (23 Pokémon triple fusion uniques)
--
--     Ce sont des Pokémon à part entière avec leurs propres stats,
--     pouvant avoir 3 ou 4 types simultanément.
--
--     evolves_from_id → pour les starters qui ont une chaîne d'évolution
--                       ex: Bulbmantle (NULL) → Ivymelortle → Venustoizard
--     evolution_level → niveau auquel cette triple fusion évolue vers la suivante
CREATE TABLE IF NOT EXISTS triple_fusion (
    id              SERIAL       PRIMARY KEY,
    name_en         VARCHAR(100) NOT NULL UNIQUE,
    name_fr         VARCHAR(100),
    hp              INTEGER      NOT NULL,
    attack          INTEGER      NOT NULL,
    defense         INTEGER      NOT NULL,
    sp_attack       INTEGER      NOT NULL,
    sp_defense      INTEGER      NOT NULL,
    speed           INTEGER      NOT NULL,
    evolves_from_id INTEGER      REFERENCES triple_fusion(id),  -- NULL si première forme
    evolution_level INTEGER,     -- niveau pour évoluer depuis evolves_from_id
    steps_to_hatch  INTEGER,     -- pour les œufs (starters uniquement)
    sprite_path     TEXT
);

-- 14. triple_fusion_type  (jusqu'à 4 types par triple fusion)
CREATE TABLE IF NOT EXISTS triple_fusion_type (
    triple_fusion_id INTEGER NOT NULL REFERENCES triple_fusion(id) ON DELETE CASCADE,
    type_id          INTEGER NOT NULL REFERENCES type(id),
    slot             INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 4),
    PRIMARY KEY (triple_fusion_id, slot)
);

-- 15. triple_fusion_component  (les 3 Pokémon de base qui composent la triple fusion)
CREATE TABLE IF NOT EXISTS triple_fusion_component (
    triple_fusion_id INTEGER NOT NULL REFERENCES triple_fusion(id) ON DELETE CASCADE,
    pokemon_id       INTEGER NOT NULL REFERENCES pokemon(id),
    position         INTEGER NOT NULL CHECK (position IN (1, 2, 3)),
    PRIMARY KEY (triple_fusion_id, position)
);

-- 16. triple_fusion_ability  (talents de chaque triple fusion)
--     slot 1, 2 = normaux / slot 3 = caché
CREATE TABLE IF NOT EXISTS triple_fusion_ability (
    triple_fusion_id INTEGER NOT NULL REFERENCES triple_fusion(id) ON DELETE CASCADE,
    ability_id       INTEGER NOT NULL REFERENCES ability(id),
    slot             INTEGER NOT NULL CHECK (slot IN (1, 2, 3)),
    is_hidden        BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (triple_fusion_id, slot)
);


-- ============================================================
-- BLOC 6 — Sprites
-- ============================================================

-- 17. creator  (artistes de sprites custom)
--     Source : CSV du jeu ou métadonnées communautaires
CREATE TABLE IF NOT EXISTS creator (
    id   SERIAL       PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- 18. fusion_sprite
--
--     Nommage fichier IF : {head_if_id}.{body_if_id}.png
--       → head_id / body_id référencent pokemon.id (IF ID, pas national)
--       → Ex : 1.1.png  = double fusion Bulbasaur  (IF#1 head + IF#1 body)
--       → Ex : 25.6.png = Pikachu (IF#25) head + Charizard (IF#6) body
--
--     is_custom  = FALSE → sprite auto-généré par le jeu
--     is_custom  = TRUE  → sprite custom communautaire
--     is_default = TRUE  → sprite affiché par défaut pour cette paire
--                          (un seul par paire — géré applicativement)
--     source : 'local' | 'community' | 'auto_generated'
CREATE TABLE IF NOT EXISTS fusion_sprite (
    id          SERIAL      PRIMARY KEY,
    head_id     INTEGER     NOT NULL REFERENCES pokemon(id),
    body_id     INTEGER     NOT NULL REFERENCES pokemon(id),
    sprite_path TEXT        NOT NULL,
    is_custom   BOOLEAN     NOT NULL DEFAULT FALSE,
    is_default  BOOLEAN     NOT NULL DEFAULT FALSE,
    source      VARCHAR(20) NOT NULL DEFAULT 'local'
                            CHECK (source IN ('local', 'community', 'auto_generated'))
);

-- 19. fusion_sprite_creator  (jonction sprite ↔ artiste, N-N)
--     Un sprite custom peut avoir plusieurs créateurs
CREATE TABLE IF NOT EXISTS fusion_sprite_creator (
    fusion_sprite_id INTEGER NOT NULL REFERENCES fusion_sprite(id) ON DELETE CASCADE,
    creator_id       INTEGER NOT NULL REFERENCES creator(id),
    PRIMARY KEY (fusion_sprite_id, creator_id)
);

-- 20. type_effectiveness  (multiplicateurs offensifs Gen 7 — identiques à IF)
--     Seules les entrées non-neutres (≠ 1.0) sont stockées.
--     multiplier : 0.00 = immunité | 0.50 = peu efficace | 2.00 = super efficace
--     Peuplé par etl/scripts/seed_type_effectiveness.py
CREATE TABLE IF NOT EXISTS type_effectiveness (
    attacking_type_id INTEGER     NOT NULL REFERENCES type(id) ON DELETE CASCADE,
    defending_type_id INTEGER     NOT NULL REFERENCES type(id) ON DELETE CASCADE,
    multiplier        NUMERIC(3,2) NOT NULL,
    PRIMARY KEY (attacking_type_id, defending_type_id)
);


-- ============================================================
-- Index pour les requêtes fréquentes
-- ============================================================

-- pokemon
CREATE INDEX IF NOT EXISTS idx_pokemon_national      ON pokemon(national_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_generation    ON pokemon(generation_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_name_en       ON pokemon(name_en);
CREATE INDEX IF NOT EXISTS idx_pokemon_name_fr       ON pokemon(name_fr);

-- types & abilities
CREATE INDEX IF NOT EXISTS idx_pokemon_type_pokemon  ON pokemon_type(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_type_type     ON pokemon_type(type_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_ability_pok   ON pokemon_ability(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_ability_ab    ON pokemon_ability(ability_id);

-- évolutions
CREATE INDEX IF NOT EXISTS idx_evolution_from        ON pokemon_evolution(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_evolution_into        ON pokemon_evolution(evolves_into_id);
CREATE INDEX IF NOT EXISTS idx_evolution_override    ON pokemon_evolution(if_override);

-- moves
CREATE INDEX IF NOT EXISTS idx_pokemon_move_pokemon  ON pokemon_move(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_move_move     ON pokemon_move(move_id);
CREATE INDEX IF NOT EXISTS idx_pokemon_move_method   ON pokemon_move(method);
CREATE INDEX IF NOT EXISTS idx_move_type             ON move(type_id);
CREATE INDEX IF NOT EXISTS idx_move_category         ON move(category);

-- localisations
CREATE INDEX IF NOT EXISTS idx_pokemon_location_pok  ON pokemon_location(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_location_region       ON location(region);

-- triple fusions
CREATE INDEX IF NOT EXISTS idx_tf_evolves_from       ON triple_fusion(evolves_from_id);
CREATE INDEX IF NOT EXISTS idx_tf_type_fusion        ON triple_fusion_type(triple_fusion_id);
CREATE INDEX IF NOT EXISTS idx_tf_component_fusion   ON triple_fusion_component(triple_fusion_id);
CREATE INDEX IF NOT EXISTS idx_tf_component_pokemon  ON triple_fusion_component(pokemon_id);

-- sprites
CREATE INDEX IF NOT EXISTS idx_fusion_sprite_pair       ON fusion_sprite(head_id, body_id);
CREATE INDEX IF NOT EXISTS idx_fusion_sprite_default    ON fusion_sprite(head_id, body_id, is_default);
CREATE INDEX IF NOT EXISTS idx_fusion_creator_sprite    ON fusion_sprite_creator(fusion_sprite_id);

-- type effectiveness
CREATE INDEX IF NOT EXISTS idx_type_eff_attacking       ON type_effectiveness(attacking_type_id);
CREATE INDEX IF NOT EXISTS idx_type_eff_defending       ON type_effectiveness(defending_type_id);
