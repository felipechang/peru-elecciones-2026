import {getCandidate, getCandidateEvents} from '$lib/server/db';
import {error} from '@sveltejs/kit';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async ({params}) => {
    const id = Number(params.id);
    const [candidate, events] = await Promise.all([
        getCandidate(id),
        getCandidateEvents(id)
    ]);
    if (!candidate) error(404, 'Candidato no encontrado');
    return {candidate, events};
};
