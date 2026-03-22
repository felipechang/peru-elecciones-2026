<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const party = $derived(data.party);
	const candidates = $derived(data.candidates);
	const sections = $derived(data.sections);

	const byPosition = $derived(
		candidates.reduce<Record<string, typeof candidates>>((acc, c) => {
			(acc[c.position] ??= []).push(c);
			return acc;
		}, {})
	);

	const positionOrder = ['Presidente', 'Vicepresidente', 'Senador', 'Congresista', 'Parlamento Andino'];
	const sortedPositions = $derived(
		Object.keys(byPosition).sort(
			(a, b) => (positionOrder.indexOf(a) + 1 || 99) - (positionOrder.indexOf(b) + 1 || 99)
		)
	);

	let activeTab = $state<'candidatos' | 'propuestas'>('candidatos');
</script>

<svelte:head><title>{party.name} — Peru Elecciones 2026</title></svelte:head>

<a href="/partidos" class="text-sm text-red-700 hover:underline mb-4 inline-block">← Todos los partidos</a>

<h1 class="text-3xl font-black mb-2">{party.name}</h1>

{#if party.summary}
	<div class="bg-white border border-gray-200 rounded-xl p-5 mb-6 text-gray-700 leading-relaxed max-w-3xl">
		{party.summary}
	</div>
{/if}

<!-- Tabs -->
<div class="flex gap-1 mb-6 border-b border-gray-200">
	<button
		onclick={() => (activeTab = 'candidatos')}
		class="px-4 py-2 text-sm font-medium border-b-2 transition-colors
			{activeTab === 'candidatos' ? 'border-red-600 text-red-700' : 'border-transparent text-gray-500 hover:text-gray-700'}"
	>
		Candidatos ({candidates.length})
	</button>
	<button
		onclick={() => (activeTab = 'propuestas')}
		class="px-4 py-2 text-sm font-medium border-b-2 transition-colors
			{activeTab === 'propuestas' ? 'border-red-600 text-red-700' : 'border-transparent text-gray-500 hover:text-gray-700'}"
	>
		Plan de Gobierno ({sections.length} temas)
	</button>
</div>

{#if activeTab === 'candidatos'}
	{#if candidates.length === 0}
		<p class="text-gray-500 italic">No hay candidatos registrados.</p>
	{:else}
		<div class="space-y-6">
			{#each sortedPositions as pos}
				<div>
					<h2 class="font-bold text-lg mb-3 text-gray-800">{pos}</h2>
					<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
						{#each byPosition[pos] as c}
							<a
								href="/candidatos/{c.id}"
								class="bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-red-400 hover:shadow-sm transition-all group"
							>
								<div class="flex items-center gap-3">
									{#if c.list_order}
										<span class="text-xs font-bold text-gray-400 w-5 text-right shrink-0">#{c.list_order}</span>
									{/if}
									<div>
										<p class="font-medium text-sm group-hover:text-red-700">{c.name}</p>
										{#if c.scope}
											<p class="text-xs text-gray-400">{c.scope}</p>
										{/if}
									</div>
								</div>
							</a>
						{/each}
					</div>
				</div>
			{/each}
		</div>
	{/if}
{:else}
	{#if sections.length === 0}
		<p class="text-gray-500 italic">No hay propuestas registradas.</p>
	{:else}
		<div class="space-y-4 max-w-3xl">
			{#each sections as s}
				<details class="bg-white border border-gray-200 rounded-xl group">
					<summary class="px-5 py-4 cursor-pointer font-semibold text-sm list-none flex justify-between items-center hover:text-red-700">
						{s.topic}
						<span class="text-gray-400 group-open:rotate-180 transition-transform text-xs">▼</span>
					</summary>
					<div class="px-5 pb-5 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap border-t border-gray-100 pt-3">
						{s.content}
					</div>
				</details>
			{/each}
		</div>
	{/if}
{/if}
