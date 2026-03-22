import {getLatestEvents} from '$lib/server/db';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async () => {
    const events = await getLatestEvents(10);
    return {events};
};
