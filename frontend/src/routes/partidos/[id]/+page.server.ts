import {getParty, getPartyCandidates, getPartySections} from '$lib/server/db';
import {error} from '@sveltejs/kit';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async ({params}) => {
    const id = Number(params.id);
    const [party, candidates, sections] = await Promise.all([
        getParty(id),
        getPartyCandidates(id),
        getPartySections(id)
    ]);
    if (!party) error(404, 'Partido no encontrado');
    return {party, candidates, sections};
};
