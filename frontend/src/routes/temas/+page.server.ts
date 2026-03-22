import {getTopicComparison, getTopics} from '$lib/server/db';
import type {PageServerLoad} from './$types';

export const load: PageServerLoad = async ({url}) => {
    const topicId = Number(url.searchParams.get('topic') ?? 0);
    const [topics, comparison] = await Promise.all([
        getTopics(),
        topicId ? getTopicComparison(topicId) : Promise.resolve(null)
    ]);
    return {topics, comparison, topicId};
};
