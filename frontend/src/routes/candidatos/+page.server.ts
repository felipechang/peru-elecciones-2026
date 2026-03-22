import {getCandidates, getParties} from '$lib/server/db';
import type {PageServerLoad} from './$types';

const PAGE_SIZE = 50;

export const load: PageServerLoad = async ({url}) => {
    const q = url.searchParams.get('q') ?? '';
    const position = url.searchParams.get('position') ?? '';
    const partyId = Number(url.searchParams.get('party_id') ?? 0);
    const page = Math.max(1, Number(url.searchParams.get('page') ?? 1));

    const [{total, items}, parties] = await Promise.all([
        getCandidates({
            q: q || undefined,
            position: position || undefined,
            partyId: partyId || undefined,
            limit: PAGE_SIZE,
            offset: (page - 1) * PAGE_SIZE
        }),
        getParties()
    ]);

    return {candidates: items, total, parties, q, position, partyId, page, pageSize: PAGE_SIZE};
};
