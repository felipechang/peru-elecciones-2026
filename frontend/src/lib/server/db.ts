import postgres from 'postgres';
import {env} from '$env/dynamic/private';

// Singleton connection pool reused across requests in the same Node process.
let _sql: ReturnType<typeof postgres> | null = null;

function sql() {
    if (!_sql) {
        _sql = postgres({
            host: env.POSTGRES_HOST ?? 'localhost',
            port: Number(env.POSTGRES_PORT ?? 5432),
            user: env.POSTGRES_USER ?? 'postgres',
            password: env.POSTGRES_PASSWORD ?? 'password',
            database: env.POSTGRES_DB ?? 'peru_elecciones'
        });
    }
    return _sql;
}

// ---- Types -----------------------------------------------------------------

export interface Party {
    id: number;
    name: string;
    summary: string | null;
}

export interface Candidate {
    id: number;
    name: string;
    position: string;
    scope: string | null;
    list_order: number | null;
    party_id: number;
    party_name: string;
}

export interface Topic {
    id: number;
    name: string;
}

export interface TopicWithPartyCount extends Topic {
    party_count: number;
}

export interface PartySection {
    id: number;
    topic: string;
    content: string;
}

export interface TopicSection {
    party_id: number;
    party_name: string;
    content: string;
}

export interface Event {
    id: number;
    title: string;
    summary: string | null;
    event_date: string | null;
    source: string | null;
    candidate_id: number;
    candidate_name: string;
    party_name: string;
}

// ---- Queries ---------------------------------------------------------------

export async function getParties(): Promise<Party[]> {
    return sql()<Party[]>`SELECT id, name, summary FROM parties ORDER BY name`;
}

export async function getParty(id: number): Promise<Party | null> {
    const rows = await sql()<Party[]>`SELECT id, name, summary FROM parties WHERE id = ${id}`;
    return rows[0] ?? null;
}

export async function getPartyCandidates(partyId: number): Promise<Candidate[]> {
    return sql()<Candidate[]>`
		SELECT id, name, position, scope, list_order
		FROM candidates
		WHERE party_id = ${partyId}
		ORDER BY position, list_order
	`;
}

export async function getPartySections(partyId: number): Promise<PartySection[]> {
    return sql()<PartySection[]>`
		SELECT ps.id, t.name AS topic, ps.content
		FROM party_sections ps
		JOIN topics t ON t.id = ps.topic_id
		WHERE ps.party_id = ${partyId}
		ORDER BY t.name
	`;
}

export async function getCandidates(params: {
    q?: string;
    position?: string;
    partyId?: number;
    limit?: number;
    offset?: number;
}): Promise<{ total: number; items: Candidate[] }> {
    const {q, position, partyId, limit = 50, offset = 0} = params;
    const db = sql();

    const items = await db<Candidate[]>`
		SELECT c.id, c.name, c.position, c.scope, c.list_order,
		       p.id AS party_id, p.name AS party_name
		FROM candidates c
		JOIN parties p ON p.id = c.party_id
		WHERE TRUE
		  ${q ? db`AND c.name ILIKE ${'%' + q + '%'}` : db``}
		  ${position ? db`AND c.position = ${position}` : db``}
		  ${partyId ? db`AND c.party_id = ${partyId}` : db``}
		ORDER BY c.name
		LIMIT ${limit} OFFSET ${offset}
	`;

    const [{total}] = await db<[{ total: number }]>`
		SELECT COUNT(*)::int AS total
		FROM candidates c
		WHERE TRUE
		  ${q ? db`AND c.name ILIKE ${'%' + q + '%'}` : db``}
		  ${position ? db`AND c.position = ${position}` : db``}
		  ${partyId ? db`AND c.party_id = ${partyId}` : db``}
	`;

    return {total, items};
}

export async function getCandidate(id: number): Promise<Candidate | null> {
    const rows = await sql()<Candidate[]>`
		SELECT c.id, c.name, c.position, c.scope, c.list_order,
		       p.id AS party_id, p.name AS party_name
		FROM candidates c
		JOIN parties p ON p.id = c.party_id
		WHERE c.id = ${id}
	`;
    return rows[0] ?? null;
}

export async function getCandidateEvents(candidateId: number): Promise<Event[]> {
    return sql()<Event[]>`
		SELECT id, title, summary, event_date::text, source
		FROM events
		WHERE candidate_id = ${candidateId}
		ORDER BY event_date DESC NULLS LAST, created_at DESC
	`;
}

export async function getTopics(): Promise<TopicWithPartyCount[]> {
    return sql()<TopicWithPartyCount[]>`
		SELECT t.id, t.name, COUNT(ps.party_id)::int AS party_count
		FROM topics t
		LEFT JOIN party_sections ps ON ps.topic_id = t.id
		GROUP BY t.id, t.name
		ORDER BY t.name
	`;
}

export async function getTopicComparison(
    topicId: number
): Promise<{ topic: Topic; sections: TopicSection[] } | null> {
    const db = sql();
    const topics = await db<Topic[]>`SELECT id, name FROM topics WHERE id = ${topicId}`;
    if (!topics[0]) return null;

    const sections = await db<TopicSection[]>`
		SELECT p.id AS party_id, p.name AS party_name, ps.content
		FROM party_sections ps
		JOIN parties p ON p.id = ps.party_id
		WHERE ps.topic_id = ${topicId}
		ORDER BY p.name
	`;

    return {topic: topics[0], sections};
}

export async function getLatestEvents(limit = 20): Promise<Event[]> {
    return sql()<Event[]>`
		SELECT e.id, e.title, e.summary, e.event_date::text, e.source,
		       c.id AS candidate_id, c.name AS candidate_name,
		       p.name AS party_name
		FROM events e
		JOIN candidates c ON c.id = e.candidate_id
		JOIN parties p ON p.id = c.party_id
		ORDER BY e.event_date DESC NULLS LAST, e.created_at DESC
		LIMIT ${limit}
	`;
}
