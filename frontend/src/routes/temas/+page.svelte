<script lang="ts">
	import { renderMarkdown } from '$lib/markdown';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	let search = $state('');

	const filteredTopics = $derived(
		search.trim()
			? data.topics.filter((t) => t.name.toLowerCase().includes(search.toLowerCase()))
			: data.topics
	);
</script>

<svelte:head><title>Comparar Temas — Peru Elecciones 2026</title></svelte:head>

<h1 class="text-3xl font-black mb-2">Comparar Temas</h1>
<p class="text-gray-500 mb-6">Selecciona un tema para ver cómo cada partido lo aborda en su Plan de Gobierno.</p>

<div class="flex gap-6 flex-col lg:flex-row">
	<!-- Topic list -->
	<aside class="lg:w-72 shrink-0">
		<input
			type="search"
			bind:value={search}
			placeholder="Filtrar temas..."
			class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-red-400"
		/>

		{#if filteredTopics.length === 0}
			<p class="text-gray-500 text-sm italic">No hay temas.</p>
		{:else}
			<ul class="space-y-1">
				{#each filteredTopics as topic}
					<li>
						<a
							href="/temas?topic={topic.id}"
							class="flex w-full items-center justify-between gap-2 text-left px-3 py-2 rounded-lg text-sm transition-colors
								{data.topicId === topic.id
									? 'bg-red-700 text-white font-medium'
									: 'hover:bg-gray-100 text-gray-700'}"
						>
							<span class="min-w-0">{topic.name}</span>
							<span
								class="shrink-0 tabular-nums text-xs font-medium rounded-full px-2 py-0.5
									{data.topicId === topic.id
										? 'bg-white/20 text-white'
										: 'bg-gray-200 text-gray-600'}"
								title="{topic.party_count} partido{topic.party_count === 1 ? '' : 's'} con propuestas"
							>
								{topic.party_count}
							</span>
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</aside>

	<!-- Comparison panel -->
	<div class="flex-1 min-w-0">
		{#if !data.comparison}
			<div class="flex flex-col items-center justify-center h-64 text-gray-400 border-2 border-dashed border-gray-200 rounded-xl">
				<span class="text-4xl mb-3">📋</span>
				<p class="text-sm">Selecciona un tema de la lista</p>
			</div>
		{:else}
			<h2 class="text-xl font-bold mb-4">{data.comparison.topic.name}</h2>
			{#if data.comparison.sections.length === 0}
				<p class="text-gray-500 italic">Ningún partido tiene propuestas registradas para este tema.</p>
			{:else}
				<div class="space-y-4">
					{#each data.comparison.sections as s}
						<details class="bg-white border border-gray-200 rounded-xl group" open>
							<summary class="px-5 py-4 cursor-pointer font-semibold text-sm list-none flex justify-between items-center hover:text-red-700">
								<a href="/partidos/{s.party_id}" class="hover:underline" onclick={(e) => e.stopPropagation()}>
									{s.party_name}
								</a>
								<span class="text-gray-400 group-open:rotate-180 transition-transform text-xs ml-2 shrink-0">▼</span>
							</summary>
							<div
								class="px-5 pb-5 border-t border-gray-100 pt-3 prose prose-sm max-w-none text-gray-700 prose-headings:text-gray-900 prose-a:text-red-700 prose-strong:text-gray-900"
							>
								{@html renderMarkdown(s.content)}
							</div>
						</details>
					{/each}
				</div>
			{/if}
		{/if}
	</div>
</div>
