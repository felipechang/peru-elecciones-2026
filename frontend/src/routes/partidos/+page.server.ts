import {getParties} from '$lib/server/db';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async () => {
    const parties = await getParties();
    return {parties};
};
