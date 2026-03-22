<script lang="ts">
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();
	const candidate = $derived(data.candidate);
	const events = $derived(data.events);
</script>

<svelte:head><title>{candidate.name} — Peru Elecciones 2026</title></svelte:head>

<a href="/candidatos" class="text-sm text-red-700 hover:underline mb-4 inline-block">← Candidatos</a>

<div class="max-w-2xl">
	<!-- Candidate header -->
	<div class="bg-white border border-gray-200 rounded-xl p-6 mb-6">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-2xl font-black mb-1">{candidate.name}</h1>
				<div class="flex flex-wrap gap-2 text-sm">
					<span class="bg-red-100 text-red-800 px-2.5 py-0.5 rounded-full font-medium">{candidate.position}</span>
					{#if candidate.scope}
						<span class="bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full">{candidate.scope}</span>
					{/if}
					{#if candidate.list_order}
						<span class="bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded-full">Posición #{candidate.list_order}</span>
					{/if}
				</div>
			</div>
		</div>
		<div class="mt-4 pt-4 border-t border-gray-100">
			<p class="text-sm text-gray-500">Partido:</p>
			<a href="/partidos/{candidate.party_id}" class="font-semibold text-red-700 hover:underline">
				{candidate.party_name}
			</a>
		</div>
	</div>

	<!-- Events -->
	<h2 class="text-xl font-bold mb-4">Noticias recientes</h2>

	{#if events.length === 0}
		<p class="text-gray-500 italic">No hay noticias registradas para este candidato.</p>
	{:else}
		<div class="space-y-3">
			{#each events as ev}
				<div class="bg-white border border-gray-200 rounded-xl p-4">
					<div class="flex items-start justify-between gap-3">
						<h3 class="font-semibold text-sm leading-snug">{ev.title}</h3>
						{#if ev.event_date}
							<span class="text-xs text-gray-400 shrink-0">{ev.event_date}</span>
						{/if}
					</div>
					{#if ev.summary}
						<p class="text-sm text-gray-600 mt-2 leading-relaxed">{ev.summary}</p>
					{/if}
					{#if ev.source}
						<a
							href={ev.source}
							target="_blank"
							rel="noopener"
							class="text-xs text-red-700 hover:underline mt-2 inline-block"
						>Ver fuente →</a>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
