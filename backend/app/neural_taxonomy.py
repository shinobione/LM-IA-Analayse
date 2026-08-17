from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

TAXONOMY_VERSION = '3.6-shinobi-2026-08'


@dataclass(frozen=True)
class GenreCandidate:
    label: str
    family: str
    prompts: tuple[str, ...]
    region: str | None = None


# CLAP is an open-vocabulary audio/text model. These candidates are deliberately
# broader than the old 24-label closed list, and each style can carry several
# paraphrases to reduce prompt-wording bias. Regional styles are kept distinct
# where collapsing them would be musically wrong (for example Vietnamese Bolero
# vs Latin-American Bolero).
GENRE_CANDIDATES: tuple[GenreCandidate, ...] = (
    # Hip-Hop / Rap
    GenreCandidate('Hip-Hop', 'Hip-Hop / Rap', ('hip hop music', 'rap and hip hop music')),
    GenreCandidate('Boom Bap', 'Hip-Hop / Rap', ('boom bap hip hop', 'classic sample-based boom bap rap')),
    GenreCandidate('Trap', 'Hip-Hop / Rap', ('trap hip hop', 'modern trap rap with 808 drums')),
    GenreCandidate('Drill', 'Hip-Hop / Rap', ('drill rap', 'dark drill hip hop with sliding 808 bass')),
    GenreCandidate('Phonk', 'Hip-Hop / Rap', ('phonk music', 'dark Memphis-influenced phonk with cowbells')),
    GenreCandidate(
        'Drift Phonk',
        'Hip-Hop / Rap',
        (
            'drift phonk',
            'aggressive drift phonk with distorted cowbells and clipped 808 bass',
            'high-energy modern phonk with Memphis vocal chops and distorted club drums',
        ),
    ),
    GenreCandidate(
        'Cyber Trap',
        'Hip-Hop / Rap',
        (
            'cyber trap hip hop',
            'futuristic industrial trap with distorted 808 bass and digital glitch textures',
            'dark cyberpunk trap rap with mechanical electronic production',
        ),
    ),
    GenreCandidate(
        'Industrial Hip-Hop',
        'Hip-Hop / Rap',
        (
            'industrial hip hop',
            'abrasive industrial rap with mechanical percussion and distorted bass',
            'dark experimental hip hop with harsh electronic noise and heavy low end',
        ),
    ),
    GenreCandidate(
        'Glitch Hop',
        'Hip-Hop / Rap',
        (
            'glitch hop',
            'hip hop groove with chopped digital glitches and syncopated electronic bass',
            'glitch-heavy electronic hip hop with broken edits and punchy drums',
        ),
    ),
    GenreCandidate(
        'Electronic Drill',
        'Hip-Hop / Rap',
        (
            'electronic drill rap',
            'drill hip hop fused with harsh electronic synths and industrial sound design',
            'dark futuristic drill with sliding 808 bass and mechanical electronic production',
        ),
    ),
    GenreCandidate('Memphis Rap', 'Hip-Hop / Rap', ('Memphis rap', '90s Memphis underground hip hop')),
    GenreCandidate('G-Funk', 'Hip-Hop / Rap', ('G-funk hip hop', 'West Coast G-funk with synth leads and deep bass')),
    GenreCandidate('Cloud Rap', 'Hip-Hop / Rap', ('cloud rap', 'atmospheric dreamy cloud rap')),
    GenreCandidate('Lo-Fi Hip-Hop', 'Hip-Hop / Rap', ('lo-fi hip hop', 'dusty relaxed lo-fi hip hop beats')),
    GenreCandidate('Jazzy Hip-Hop', 'Hip-Hop / Rap', ('jazzy hip hop', 'jazz-influenced hip hop')),
    GenreCandidate('Pop Rap', 'Hip-Hop / Rap', ('pop rap', 'melodic mainstream pop rap')),
    GenreCandidate(
        'Grime',
        'Hip-Hop / Rap',
        (
            'UK grime music',
            'East London grime around 140 BPM with sparse syncopated electronic beats and square-wave synths',
            'British grime MC music with cold minimal riddims and UK garage lineage',
        ),
    ),
    GenreCandidate('Horrorcore', 'Hip-Hop / Rap', ('horrorcore rap', 'dark horror-themed hip hop')),
    GenreCandidate('Alternative Hip-Hop', 'Hip-Hop / Rap', ('alternative hip hop', 'experimental alternative rap')),

    # R&B / Soul / Funk
    GenreCandidate('Contemporary R&B', 'R&B / Soul / Funk', ('contemporary R&B', 'modern rhythm and blues')),
    GenreCandidate('Alternative R&B', 'R&B / Soul / Funk', ('alternative R&B', 'experimental atmospheric R&B')),
    GenreCandidate(
        'Neo Soul',
        'R&B / Soul / Funk',
        (
            'neo soul music',
            'neo-soul with laid-back pocket, soulful harmony and organic R&B instrumentation',
            'modern neo-soul with live groove, warm vocals and jazz-influenced chords',
        ),
    ),
    GenreCandidate('Soul', 'R&B / Soul / Funk', ('soul music', 'classic expressive soul music')),
    GenreCandidate('Funk', 'R&B / Soul / Funk', ('funk music', 'groove-driven funk music')),
    GenreCandidate('New Jack Swing', 'R&B / Soul / Funk', ('new jack swing', 'late 80s and 90s R&B new jack swing')),
    GenreCandidate('Quiet Storm', 'R&B / Soul / Funk', ('quiet storm R&B', 'smooth romantic quiet storm soul')),

    # Pop and dance-pop hybrids
    GenreCandidate('Pop', 'Pop', ('pop music', 'mainstream contemporary pop')),
    GenreCandidate('Pop Ballad', 'Pop', ('pop ballad', 'slow emotional vocal pop ballad')),
    GenreCandidate('Synth-Pop', 'Pop', ('synth-pop', 'melodic pop driven by synthesizers')),
    GenreCandidate('Electropop', 'Pop', ('electropop', 'electronic pop music')),
    GenreCandidate('Indie Pop', 'Pop', ('indie pop', 'independent alternative pop')),
    GenreCandidate('City Pop', 'Pop', ('Japanese city pop', '80s-inspired city pop')),
    GenreCandidate('J-Pop', 'Pop', ('Japanese J-pop', 'modern Japanese pop music'), region='Japan'),
    GenreCandidate('K-Pop', 'Pop', ('K-pop', 'modern Korean pop music'), region='Korea'),
    GenreCandidate('French Chanson', 'Pop', ('French chanson', 'French singer-songwriter chanson'), region='France'),
    GenreCandidate(
        'Europop',
        'Pop',
        (
            'Europop',
            'European dance-oriented pop',
            'late 1990s and 2000s melodic European dance-pop',
            'polished European club pop with electronic dance production',
        ),
    ),
    GenreCandidate(
        'Dancehall Pop',
        'Pop',
        (
            'dancehall pop',
            'pop song built on a syncopated Jamaican dancehall rhythm',
            'Caribbean-influenced dance-pop with electronic production',
            'late 2000s dancehall-influenced pop with a bouncy club groove',
        ),
    ),
    GenreCandidate(
        'Eurodance',
        'Pop',
        (
            'Eurodance pop',
            'European dance-pop with a four-on-the-floor house beat',
            'late 1990s and 2000s Eurodance club pop',
            'Y2K European vocal dance music with bright synths and club drums',
        ),
    ),

    # Vietnamese / Asian regional vocabulary
    GenreCandidate(
        'Vietnamese Bolero',
        'Vietnamese / Asian',
        (
            'Vietnamese bolero music',
            'traditional Vietnamese sentimental bolero',
            'Vietnamese nhạc vàng bolero',
            'Vietnamese nhạc trữ tình bolero ballad',
            'slow romantic Vietnamese bolero with sentimental vocals',
        ),
        region='Vietnam',
    ),
    GenreCandidate(
        'Nhạc Vàng',
        'Vietnamese / Asian',
        ('Vietnamese nhạc vàng music', 'South Vietnamese sentimental golden music', 'Vietnamese pre-1975 sentimental popular music'),
        region='Vietnam',
    ),
    GenreCandidate(
        'Nhạc Trữ Tình',
        'Vietnamese / Asian',
        ('Vietnamese nhạc trữ tình', 'Vietnamese sentimental romantic popular song', 'Vietnamese sentimental ballad music'),
        region='Vietnam',
    ),
    GenreCandidate('V-Pop', 'Vietnamese / Asian', ('Vietnamese V-pop', 'modern Vietnamese pop music'), region='Vietnam'),
    GenreCandidate('Vietnamese Pop Ballad', 'Vietnamese / Asian', ('Vietnamese pop ballad', 'modern Vietnamese sentimental pop ballad'), region='Vietnam'),
    GenreCandidate('Vietnamese Folk', 'Vietnamese / Asian', ('Vietnamese folk music', 'traditional Vietnamese folk song'), region='Vietnam'),
    GenreCandidate('Vietnamese Traditional', 'Vietnamese / Asian', ('traditional Vietnamese music', 'Vietnamese traditional acoustic music'), region='Vietnam'),
    GenreCandidate('Asian Ballad', 'Vietnamese / Asian', ('East Asian sentimental ballad', 'slow Asian romantic pop ballad')),
    GenreCandidate('Bollywood', 'Vietnamese / Asian', ('Bollywood film music', 'Indian Bollywood pop'), region='India'),

    # Folk / World
    GenreCandidate('World Music', 'Folk / World', ('world music', 'global traditional popular music')),
    GenreCandidate('Folk', 'Folk / World', ('folk music', 'traditional acoustic folk song')),
    GenreCandidate('Fado', 'Folk / World', ('Portuguese fado', 'melancholic Portuguese fado music'), region='Portugal'),
    GenreCandidate('Zouk', 'Folk / World', ('zouk music', 'French Caribbean zouk'), region='Caribbean'),
    GenreCandidate('Highlife', 'Folk / World', ('West African highlife', 'Ghanaian highlife music'), region='West Africa'),
    GenreCandidate('Afrobeat', 'Folk / World', ('Afrobeat music', 'West African Afrobeat groove'), region='West Africa'),
    GenreCandidate(
        'Afropop',
        'Folk / World',
        (
            'Afropop music',
            'modern African pop with melodic vocals and a syncopated dance groove',
            'Afro-pop dance music with bright pop production and layered percussion',
        ),
        region='Africa',
    ),
    GenreCandidate('Indian Classical', 'Folk / World', ('Indian classical music', 'Hindustani or Carnatic classical music'), region='India'),

    # Electronic
    GenreCandidate('House', 'Electronic', ('house music', 'four-on-the-floor house music')),
    GenreCandidate('Deep House', 'Electronic', ('deep house', 'warm atmospheric deep house')),
    GenreCandidate(
        'Euro-House',
        'Electronic',
        (
            'Euro house music',
            'European vocal house with pop songwriting',
            'Y2K European house-pop with four-on-the-floor club drums',
        ),
    ),
    GenreCandidate('Techno', 'Electronic', ('techno music', 'driving electronic techno')),
    GenreCandidate('Drum and Bass', 'Electronic', ('drum and bass', 'fast breakbeat drum and bass')),
    GenreCandidate('Jungle', 'Electronic', ('jungle music', 'old-school jungle breakbeats')),
    GenreCandidate('Dubstep', 'Electronic', ('dubstep', 'bass-heavy dubstep music')),
    GenreCandidate('Future Bass', 'Electronic', ('future bass', 'melodic future bass electronic music')),
    GenreCandidate('Ambient', 'Electronic', ('ambient music', 'spacious atmospheric ambient music')),
    GenreCandidate('Dark Ambient', 'Electronic', ('dark ambient music', 'ominous atmospheric dark ambient')),
    GenreCandidate('Downtempo', 'Electronic', ('downtempo electronic music', 'slow chilled electronic downtempo')),
    GenreCandidate('Synthwave', 'Electronic', ('synthwave', 'retro 80s synthwave electronic music')),
    GenreCandidate('Vaporwave', 'Electronic', ('vaporwave', 'nostalgic vaporwave electronic music')),
    GenreCandidate('Trip Hop', 'Electronic', ('trip hop', 'downtempo trip hop with hip hop beats')),
    GenreCandidate('Glitch', 'Electronic', ('glitch electronic music', 'digital glitch music')),
    GenreCandidate('IDM', 'Electronic', ('IDM intelligent dance music', 'experimental electronic IDM')),
    GenreCandidate('Industrial Electronic', 'Electronic', ('industrial electronic music', 'harsh mechanical industrial electronics')),
    GenreCandidate('Trance', 'Electronic', ('trance music', 'euphoric electronic trance')),
    GenreCandidate('Hardstyle', 'Electronic', ('hardstyle', 'hard electronic dance music with distorted kicks')),

    # Reggae / Caribbean
    GenreCandidate('Reggae', 'Reggae / Caribbean', ('reggae music', 'Jamaican reggae')),
    GenreCandidate(
        'Dancehall',
        'Reggae / Caribbean',
        (
            'dancehall music',
            'Jamaican dancehall',
            'digital dancehall riddim with syncopated Caribbean drums and bass',
            'modern Jamaican dancehall groove',
        ),
    ),
    GenreCandidate('Dub', 'Reggae / Caribbean', ('dub reggae', 'echo-heavy Jamaican dub')),
    GenreCandidate('Lovers Rock', 'Reggae / Caribbean', ('lovers rock reggae', 'romantic smooth reggae')),
    GenreCandidate('Ska', 'Reggae / Caribbean', ('ska music', 'upbeat Jamaican ska')),
    GenreCandidate('Soca', 'Reggae / Caribbean', ('soca music', 'Caribbean soca dance music')),

    # Latin — Latin Bolero is intentionally distinct from Vietnamese Bolero.
    GenreCandidate('Latin Bolero', 'Latin', ('Latin American bolero', 'Cuban romantic bolero', 'Spanish-language bolero music'), region='Latin America'),
    GenreCandidate('Bossa Nova', 'Latin', ('Brazilian bossa nova', 'soft Brazilian bossa nova'), region='Brazil'),
    GenreCandidate('Salsa', 'Latin', ('salsa music', 'Afro-Cuban salsa dance music'), region='Latin America'),
    GenreCandidate('Reggaeton', 'Latin', ('reggaeton', 'Latin urban reggaeton'), region='Latin America'),
    GenreCandidate('Cumbia', 'Latin', ('cumbia music', 'Latin American cumbia dance music'), region='Latin America'),
    GenreCandidate('Bachata', 'Latin', ('bachata music', 'Dominican romantic bachata'), region='Dominican Republic'),
    GenreCandidate('Tango', 'Latin', ('Argentine tango', 'traditional tango music'), region='Argentina'),
    GenreCandidate('Samba', 'Latin', ('Brazilian samba', 'samba music with Brazilian percussion'), region='Brazil'),

    # Rock / Metal
    GenreCandidate('Rock', 'Rock / Metal', ('rock music', 'guitar-driven rock music')),
    GenreCandidate('Alternative Rock', 'Rock / Metal', ('alternative rock', 'modern alternative guitar rock')),
    GenreCandidate('Indie Rock', 'Rock / Metal', ('indie rock', 'independent guitar rock')),
    GenreCandidate('Hard Rock', 'Rock / Metal', ('hard rock', 'heavy guitar-driven hard rock')),
    GenreCandidate('Heavy Metal', 'Rock / Metal', ('heavy metal', 'heavy distorted metal music')),
    GenreCandidate('Punk', 'Rock / Metal', ('punk rock', 'fast raw punk music')),
    GenreCandidate('Post-Rock', 'Rock / Metal', ('post-rock', 'atmospheric instrumental post-rock')),
    GenreCandidate('Dream Pop', 'Rock / Metal', ('dream pop', 'ethereal dreamy guitar pop')),
    GenreCandidate('Shoegaze', 'Rock / Metal', ('shoegaze', 'dense reverb-heavy shoegaze rock')),

    # Jazz / Blues
    GenreCandidate('Jazz', 'Jazz / Blues', ('jazz music', 'acoustic jazz ensemble')),
    GenreCandidate('Smooth Jazz', 'Jazz / Blues', ('smooth jazz', 'polished relaxed smooth jazz')),
    GenreCandidate('Jazz-Funk', 'Jazz / Blues', ('jazz-funk', 'funky electric jazz fusion')),
    GenreCandidate('Blues', 'Jazz / Blues', ('blues music', 'traditional blues')),
    GenreCandidate('Rhythm & Blues', 'Jazz / Blues', ('classic rhythm and blues', 'traditional R&B rhythm and blues')),

    # Classical / Screen
    GenreCandidate('Classical', 'Classical / Screen', ('classical music', 'Western classical music')),
    GenreCandidate('Orchestral', 'Classical / Screen', ('orchestral music', 'full symphonic orchestra music')),
    GenreCandidate('Cinematic Score', 'Classical / Screen', ('cinematic film score', 'dramatic cinematic soundtrack music')),
    GenreCandidate('Soundtrack', 'Classical / Screen', ('soundtrack music', 'music written for film or television')),
    GenreCandidate('Neo-Classical', 'Classical / Screen', ('neo-classical music', 'modern contemporary classical music')),

    # Country / Acoustic
    GenreCandidate('Country', 'Country / Acoustic', ('country music', 'American country song')),
    GenreCandidate('Singer-Songwriter', 'Country / Acoustic', ('singer-songwriter music', 'intimate acoustic singer songwriter song')),
    GenreCandidate('Acoustic Ballad', 'Country / Acoustic', ('acoustic ballad', 'slow acoustic guitar vocal ballad')),
)


MOOD_LABELS: tuple[str, ...] = (
    'energetic', 'dark', 'melancholic', 'dreamy', 'aggressive', 'euphoric',
    'romantic', 'relaxed', 'uplifting', 'tense', 'mysterious', 'confident',
    'nostalgic', 'intimate', 'playful', 'sentimental', 'bittersweet',
    'cinematic', 'hypnotic', 'menacing', 'serene', 'hopeful', 'sensual',
    'triumphant', 'anxious', 'warm', 'cold', 'dramatic', 'reflective', 'rebellious',
)


INSTRUMENT_LABELS: tuple[str, ...] = (
    'male vocals', 'female vocals', 'rap vocals', 'spoken vocals', 'choir',
    'acoustic drums', 'electronic drums', 'drum machine', 'percussion',
    'congas and bongos', '808 bass', 'synth bass', 'bass guitar', 'upright bass',
    'synthesizer', 'ambient pads', 'piano', 'electric piano', 'acoustic guitar',
    'nylon-string guitar', 'electric guitar', 'strings', 'violin', 'brass',
    'flute', 'saxophone', 'accordion', 'orchestra', 'Vietnamese đàn tranh zither',
    'Vietnamese đàn bầu monochord',
)


def families(candidates: Iterable[GenreCandidate] = GENRE_CANDIDATES) -> tuple[str, ...]:
    return tuple(dict.fromkeys(candidate.family for candidate in candidates))


def regional_candidates(candidates: Iterable[GenreCandidate] = GENRE_CANDIDATES) -> tuple[GenreCandidate, ...]:
    return tuple(candidate for candidate in candidates if candidate.region)


def confidence_policy(
    *,
    primary_similarity: float,
    second_similarity: float,
    style_consensus: float,
    family_consensus: float,
    minimum_similarity: float = 0.10,
) -> dict[str, object]:
    """Return conservative evidence confidence, never an absolute probability.

    CLAP cosine similarities are model-relative. Confidence therefore combines
    temporal agreement and winner margin; it deliberately supports UNKNOWN.
    """
    margin = max(0.0, primary_similarity - second_similarity)
    margin_strength = max(0.0, min(1.0, margin / 0.055))
    evidence = max(
        0.0,
        min(1.0, 0.42 * family_consensus + 0.33 * style_consensus + 0.25 * margin_strength),
    )

    reasons: list[str] = []
    if primary_similarity < minimum_similarity:
        reasons.append('top similarity is below the minimum evidence floor')
    if style_consensus < 0.40:
        reasons.append('style winner changes across representative segments')
    if family_consensus < 0.55:
        reasons.append('genre family is unstable across representative segments')
    if margin < 0.012:
        reasons.append('top candidates are nearly tied')

    is_unknown = (
        primary_similarity < minimum_similarity
        or evidence < 0.34
        or (style_consensus < 0.40 and margin < 0.018)
    )
    level = 'high' if evidence >= 0.72 and not is_unknown else 'medium' if evidence >= 0.50 and not is_unknown else 'low'

    return {
        'score': round(evidence, 4),
        'percent': round(evidence * 100.0, 1),
        'level': level,
        'is_unknown': is_unknown,
        'margin': round(margin, 5),
        'reasons': reasons,
        'note': 'Evidence confidence from CLAP similarity margin + temporal consensus; not an absolute genre probability.',
    }
