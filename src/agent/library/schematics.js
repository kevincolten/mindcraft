import fs from 'fs';
import path from 'path';

const SCHEMATICS_DIR = process.env.SCHEMATICS_DIR || '/app/schematics';
const INDEX_FILE = 'schematics_index.json';

let cachedIndex = null;

// Words that shouldn't count toward a match score.
const STOPWORDS = new Set([
    'a', 'an', 'the', 'of', 'in', 'on', 'at', 'to', 'and', 'or', 'with', 'is',
    'are', 'was', 'were', 'it', 'its', 'this', 'that', 'these', 'those',
    'build', 'builds', 'me', 'my', 'please', 'can', 'you', 'could', 'would',
    'make', 'making', 'create', 'want', 'like', 'some', 'for', 'us', 'here',
    'minecraft', 'thing', 'something', 'one'
]);

// Common kid phrasing -> words that actually appear in the descriptions.
const SYNONYMS = {
    'fort': ['fortress', 'castle'],
    'palace': ['castle', 'mansion'],
    'hut': ['cabin', 'cottage', 'house'],
    'shack': ['cabin', 'cottage'],
    'skyscraper': ['tower', 'building'],
    'spooky': ['haunted', 'dark', 'creepy'],
    'scary': ['haunted', 'dark', 'creepy'],
    'boat': ['ship'],
    'plane': ['airplane', 'aircraft'],
    'store': ['shop', 'market'],
    'restaurant': ['cafe', 'tavern', 'inn'],
    'big': ['large', 'giant', 'huge'],
    'small': ['tiny', 'little'],
    'pretty': ['beautiful', 'decorative'],
};

function loadIndex() {
    if (cachedIndex) return cachedIndex;
    const indexPath = path.join(SCHEMATICS_DIR, INDEX_FILE);
    try {
        cachedIndex = JSON.parse(fs.readFileSync(indexPath, 'utf8'));
    } catch (e) {
        cachedIndex = null;
    }
    return cachedIndex;
}

function tokenize(text) {
    return (text || '')
        .toLowerCase()
        .match(/[a-z]+/g)
        ?.filter(w => w.length > 2 && !STOPWORDS.has(w)) || [];
}

function expand(words) {
    const out = new Set(words);
    for (const w of words) {
        if (SYNONYMS[w]) SYNONYMS[w].forEach(s => out.add(s));
    }
    return [...out];
}

/**
 * Score every schematic against the query and return the best matches.
 * Falls back to plain filename matching if the index file is missing.
 */
export function searchSchematics(query, limit = 5) {
    const index = loadIndex();
    const queryWords = expand(tokenize(query));
    if (queryWords.length === 0) return [];

    if (!index) {
        // No index: fall back to filename substring matching.
        let files = [];
        try {
            files = fs.readdirSync(SCHEMATICS_DIR)
                .filter(f => f.endsWith('.schem') || f.endsWith('.schematic'));
        } catch (e) {
            return [];
        }
        return files
            .filter(f => queryWords.some(w => f.toLowerCase().includes(w)))
            .slice(0, limit)
            .map(f => ({ file: f, label: f.replace(/\.(schem|schematic)$/, '').replace(/_/g, ' '), score: 1 }));
    }

    const results = [];
    for (const [file, meta] of Object.entries(index)) {
        const keywords = new Set(meta.keywords || []);
        const nameWords = new Set(tokenize(meta.name));
        let score = 0;
        for (const w of queryWords) {
            if (nameWords.has(w)) score += 3;      // in the short name = strong signal
            else if (keywords.has(w)) score += 1;  // somewhere in the description
        }
        if (score > 0) {
            // Slight nudge toward bigger, more interesting builds on ties.
            score += Math.min((meta.blocks || 0) / 100000, 0.5);
            results.push({ file, label: meta.name, description: meta.description, score });
        }
    }

    results.sort((a, b) => b.score - a.score);
    return results.slice(0, limit);
}

/** A few example builds, used when a search comes up empty. */
export function sampleSuggestions(count = 4) {
    const index = loadIndex();
    if (!index) return [];
    const keys = Object.keys(index);
    const picks = [];
    for (let i = 0; i < count && keys.length; i++) {
        const k = keys[Math.floor(Math.random() * keys.length)];
        if (!picks.includes(index[k].name)) picks.push(index[k].name);
    }
    return picks;
}

export function countSchematics() {
    const index = loadIndex();
    if (index) return Object.keys(index).length;
    try {
        return fs.readdirSync(SCHEMATICS_DIR).filter(f => f.endsWith('.schem')).length;
    } catch (e) {
        return 0;
    }
}
