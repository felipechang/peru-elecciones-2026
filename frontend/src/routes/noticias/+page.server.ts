import {getLatestEvents} from '$lib/server/db';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async ({url}) => {
    const limit = Math.min(200, Math.max(20, Number(url.searchParams.get('limit') ?? 50)));
    const events = await getLatestEvents(limit);
    return {events, limit};
};
